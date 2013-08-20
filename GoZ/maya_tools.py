"""Maya Server and ZBrush client classes """

import socket
import errno
import GoZ.errs as errs
import GoZ.utils as utils
import maya.cmds as cmds
import os.chmod
import stat

# nodes marked for removal from maya on import from ZBrush
GARBAGE_NODES = ['blinn',
                 'blinnSG',
                 'materialInfo',
                 'ZBrushTexture',
                 'place2dTexture2']
                      
class MayaServer(object):

    """

    Maya server using commandPort, gets meshes from zbrush

    attributes:
        self.status                    -- current server status (up/down)
        self.host                      -- current host for serving on from utils.get_net_info
        self.port                      -- current port for serving on from utils.get_net_info
        self.cmdport_name              -- formated command port name
        self.file_path                 -- current file being loaded from ZBrush (full path)
        self.file_name                 -- current file being loaded from ZBrush (name only no ext)
        self.nodes                     -- a list of nodes to remove on ZBrush file import

    methods:
        start(ip,port)                 -- starts maya command port
        stop(ip,port)                  -- stops maya command port
    """

    def __init__(self):
        self.host, self.port = utils.get_net_info('MNET')

        self.cmdport_name = "%s:%s" % (self.host, self.port)
        self.status = False


    def start(self):
        """ starts a command port"""

        # check network info
        utils.validate_host(self.host)
        utils.validate_port(self.port)

        self.cmdport_name = "%s:%s" % (self.host, self.port)
        self.status = cmds.commandPort(self.cmdport_name, query=True)

        # if down, start a new command port
        if self.status is False:
            cmds.commandPort(name=self.cmdport_name, sourceType='python')
            self.status = cmds.commandPort(self.cmdport_name, query=True)
        print 'listening %s' % self.cmdport_name

    def stop(self):
        """ stop command port """
        cmds.commandPort(name=self.cmdport_name,
                         sourceType='python', close=True)
        self.status = cmds.commandPort(self.cmdport_name,
                                       query=True)
        print 'closing %s' % self.cmdport_name

# Maya-side callbacks

def load(file_path):
    """
    get file name from file path
    remove matching nodes
    import file
    """
    file_name = utils.split_file_name(file_path)
    cleanup(file_name)
    cmds.file(file_path, i=True,
              usingNamespaces=False,
              removeDuplicateNetworks=True)

def cleanup(name):
    """ removes un-used nodes on import of obj"""

    if cmds.objExists(name):
        cmds.delete(name)

    for node in GARBAGE_NODES:
        node = name + '_' + node
        if cmds.objExists(node):
            cmds.delete(node)


class ZBrushClient(object):

    """
    ZBrush client used for sending meshes to zbrush

    attributes:
        self.status      -- status of the connection to ZBrushServer
        self.ascii_path  -- current ascii file export path
        self.objs        -- list of objects to send to ZBrushServer
        self.host        -- current host obtained from utils.get_net_info
        self.port        -- current port obtained from utils.get_net_info
        self.sock        -- current open socket connection

    methods:
        connect()        -- connects to ZBrushServer
        send()           -- send a file load command to ZBrush via ZBrushServer
        export()         -- exports selected meshes and checks for previous GoZBrushIDs
        relink()         -- relinks the current export mesh name to a prior GoZBrushID
        create()         -- exports a clean mesh with a new GoZBrushID
        parse_objs()     -- evalutes a list of objects for export, removes non-mesh dag types
        goz_check()      -- checks object history for instances of GoZBrushID
        load_confirm()   -- checks with ZBrushServer to make sure objects are loaded after a send
        check_socket     -- poll ZBrushServer, execute before sending to look for issues

    """

    def __init__(self):

        # setup host/port, set server to 'down', create a port and try to
        # connect
        self.host, self.port = utils.get_net_info('ZNET')
        self.status = False
        self.sock = None
        self.objs = None
        self.goz_id = None
        self.goz_obj = None
        self.ascii_path = None

    def connect(self):
        """connects to ZBrushServer """

        try:
            # close old socket, might not exist so skip
            self.sock.close()
        except AttributeError:
            print 'no socket to close...'

        self.status = False

        utils.validate_host(self.host)
        utils.validate_port(self.port)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # time out incase of a bad host/port that actually exists
        self.sock.settimeout(45)

        try:
            self.sock.connect((self.host, int(self.port)))
        except socket.error as err:
            self.status = False
            if errno.ECONNREFUSED in err:
                raise errs.ZBrushServerError(
                    'Connection Refused: %s:%s' % (self.host, self.port))

        self.status = True

    def check_socket(self):
        """ verify connection to zbrush """

        if self.sock is None:
            return

        try:
            self.sock.send('check')
            if self.sock.recv(1024) == 'ok':
                # connected
                print 'connected!'
            else:
                # bad connection, clear socket
                self.status = False
                self.sock.close()
                self.sock = None
                print 'conn reset!'

        except socket.error as err:
            # catches server down errors, resets socket
            self.status = False
            self.sock.close()
            self.sock = None
            if errno.ECONNREFUSED in err:
                print 'conn ref'
                # server probbly down
            if errno.EADDRINUSE in err:
                # this is fine
                print 'already connected...'
            if errno.EPIPE in err:
                # server down, or unexpected connection interuption
                print 'broken pipe, trying to reconnect'
        except AttributeError:
            print 'need new sock'

    def send(self):
        """ send to ZBrush """

        # export, send
        if self.status:
            self.export()
            self.sock.send('open|' + ':'.join(self.objs))
            # check receipt of objs
            self.load_confirm()
        else:
            raise errs.ZBrushServerError(
                'Please connect to ZBrushServer first')

    def load_confirm(self):
        """ make sure files loaded correctly """
        if self.sock.recv(1024) == 'loaded':
            print 'ZBrush Loaded:'
            print ('\n'.join(self.objs))
        else:
            self.status = False
            self.sock = None
            print 'ZBrushServer is down!'
            raise errs.ZBrushServerError('ZBrushServer is down!')

    def export(self):
        """ save some files """

        print self.objs

        for obj in self.objs:

            cmds.select(cl=True)
            cmds.select(obj)
            cmds.delete(ch=True)
            self.ascii_path = utils.make_file_name(obj)

            cmds.file(self.ascii_path,
                      force=True,
                      options="v=0",
                      type="mayaAscii",
                      exportSelected=True)
            os.chmod(self.ascii_path, stat.S_IXOTH | stat.S_IWOTH | stat.S_IROTH)

    def parse_objs(self):
        """ grab meshes from selection, needs some revision """
        self.objs = cmds.ls(selection=True, type='mesh', dag=True)
        if self.objs:
            xforms = cmds.listRelatives(
                self.objs, parent=True, fullPath=True)
            #freeze transform
            cmds.makeIdentity(xforms,apply=True, t=1, r=1, s=1, n=0)
            cmds.select(xforms)
            self.objs = cmds.ls(selection=True)
            return True
        else:
            return False

    def goz_check(self):
        """ 
        creates a list of objects with GoZBrushID in history
        
        GoZBrushID is created by ZBrush on export and is used to track
        name changes that can occur in maya

        this function compares object current name against the ID

        this list is handled by the gui to allow for dialog boxes
        
        """

        goz_list = []

        for obj in self.objs:

            goz_check = cmds.attributeQuery(
                'GoZBrushID', node=obj, exists=True)

            if goz_check:
                # check for 'rename'
                goz_id = cmds.getAttr(obj + '.GoZBrushID')
                if obj != goz_id:
                    goz_list.append((obj, goz_id))
            else:
                # check for old ID in history
                history = cmds.listHistory(obj)
                for old_obj in history:
                    goz_check = cmds.attributeQuery('GoZBrushID',
                                                    node=old_obj,
                                                    exists=True)
                    if goz_check:
                        goz_id = cmds.getAttr(old_obj + '.GoZBrushID')
                        if obj != goz_id:
                            goz_list.append((obj, goz_id))

        #resulting mismatches to be handled
        return goz_list

    def relink(self):
        """ relink object name with existing GoZBrushID"""
        if self.goz_obj not in self.objs:
            return

        # manages re linking GoZBrush IDs, checks for attribute on shape/xform
        obj = self.goz_obj
        goz_id = self.goz_id

        pre_sel = cmds.ls(sl=True)
        cmds.delete(obj, ch=True)

        # in the case of a object being duplicated this removes the duplicate
        # to prevent deletion, the 'create' option is prefered
        # is only happens when an object was duplicated and merged (original still exists)
        if cmds.objExists(goz_id):
            cmds.delete(goz_id)

        cmds.rename(obj, goz_id)
        cmds.select(cl=True)
        cmds.select(goz_id)
        shape = cmds.ls(selection=True, type='mesh', dag=True)[0]
        xform = cmds.listRelatives(shape, parent=True, fullPath=True)[0]
        goz_check_xform = cmds.attributeQuery(
            'GoZBrushID', node=xform, exists=True)
        goz_check_shape = cmds.attributeQuery(
            'GoZBrushID', node=shape, exists=True)

        if goz_check_shape is False:
            cmds.addAttr(shape, longName='GoZBrushID', dataType='string')
        if goz_check_xform is False:
            cmds.addAttr(xform, longName='GoZBrushID', dataType='string')

        cmds.setAttr(shape + '.GoZBrushID', goz_id, type='string')
        cmds.setAttr(xform + '.GoZBrushID', goz_id, type='string')
        cmds.select(cl=True)
        pre_sel.remove(obj)
        pre_sel.append(xform)
        print pre_sel
        cmds.select(pre_sel)

    def create(self):
        """ changes a GoZBrush ID to match object name """
        obj = self.goz_obj
        pre_sel = cmds.ls(sl=True)
        cmds.delete(obj, ch=True)
        cmds.select(cl=True)
        cmds.select(obj)
        shape = cmds.ls(selection=True, type='mesh', dag=True)[0]
        xform = cmds.listRelatives(shape, parent=True, fullPath=True)[0]
        goz_check_xform = cmds.attributeQuery(
            'GoZBrushID', node=xform, exists=True)
        goz_check_shape = cmds.attributeQuery(
            'GoZBrushID', node=shape, exists=True)

        if goz_check_shape:
            cmds.setAttr(shape + '.GoZBrushID', obj, type='string')
        if goz_check_xform:
            cmds.setAttr(xform + '.GoZBrushID', obj, type='string')
        cmds.select(pre_sel)
