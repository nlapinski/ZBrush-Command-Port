#!/usr/bin/python

import utils
import maya.cmds as cmds
class MayaServer(object):

    """
    
    Maya server using commandPort, gets meshes from zbrush
    
    attributes:
        self.status                    -- current server status (up/down)
        self.host                      -- current host for serving on from utils.getenvs
        self.port                      -- current port for serving on from utils.getenvs
        self.shared_dir                -- shared ZBrush/Maya directory from utils.getenvs
        self.cmdport_name              -- formated command port name
        self.file_path                 -- current file being loaded from ZBrush (full path)
        self.file_name                 -- current file being loaded from ZBrush (name only no ext)
        self.nodes                     -- a list of nodes to remove on ZBrush file import

    methods:
        start(ip,port)                 -- starts maya command port
        stop(ip,port)                  -- stops maya command port
        load(file)                     -- loads a mesh from zbrush
        cleanup()                      -- cleans up before file import

    """

    def __init__(self):
        self.host,self.port,self.shared_dir = utils.getenvs(maya=True,serv=True,shared_dir=True)

        self.cmdport_name = "%s:%s" % (self.host,self.port)
        self.status=utils.DOWN

        self.nodes = [  'blinn',
                        'blinnSG',
                        'materialInfo',
                        'ZBrushTexture',
                        'place2dTexture2'  ]

    def start(self):

        utils.writecfg(self.host,self.port,'MNET')

        self.status = cmds.commandPort(self.cmdport_name,query=True)

        if self.status is False:
            cmds.commandPort(name=self.cmdport_name ,sourceType='python')
            self.status = cmds.commandPort(self.cmdport_name,query=True)
            print 'listening %s' % self.cmdport_name

    def stop(self):
        cmds.commandPort(name=self.cmdport_name,
                sourceType='python',close=True)
        self.status = cmds.commandPort(self.cmdport_name,
                query=True)
        print 'closing %s' % self.cmdport_name

    def load(self,file_path):
        self.file_name = utils.split_file_name(file_path)
        self.file_path  = file_path
        self.cleanup()
        cmds.file(file_path,i=True,
                usingNamespaces=False,
                removeDuplicateNetworks=True)

    def cleanup(self):
        name = self.file_name

        if cmds.objExists(name):
            cmds.delete(name)

        for node in self.nodes:
            node = name+'_'+node
            if cmds.objExists(node):
                cmds.delete(node)

class ZBrushClient(object):
    """
    ZBrush client used for sending meshes to zbrush

    attributes:
        self.status      -- status of the connection to ZBrushServer
        self.ascii_path  -- current ascii file export path
        self.objs        -- list of objects to send to ZBrushServer
        self.host        -- current host obtained from utils.getenvs
        self.port        -- current port obtained from utils.getenvs
        self.sock        -- current open socket connection

    methods:
        connect()        -- connects to ZBrushServer
        hangup()         -- closes connection to ZBrushServer
        send()           -- send a file load command to ZBrush via ZBrushServer
        export()         -- exports selected meshes and checks for previous GoZBrushIDs
        relink()         -- relinks the current export mesh name to a prior GoZBrushID
        create()         -- exports a clean mesh with a new GoZBrushID
        parse_objs()     -- evalutes a list of objects for export, removes non-mesh dag types
        goz_check()      -- checks object history for instances of GoZBrushID
        load_confirm()   -- checks with ZBrushServer to make sure objects are loaded after a send

    """
    def __init__(self):
        self.host,self.port,self.shared_dir = utils.getenvs(zbrush=True,shared_dir=True)
        self.status=utils.DOWN
        self.sock = utils.socket.socket(utils.socket.AF_INET,utils.socket.SOCK_STREAM)

    def connect(self):
        if self.status is utils.DOWN:
            #self.sock.settimeout(2.8)
            self.sock.connect((self.host, int(self.port)))
            self.status = utils.UP
    
    def hangup(self):
        self.sock.close()
        pass
    
    def send(self):

        print self.host,self.port
        
        utils.writecfg(self.host,self.port,'ZNET')
        self.connect()
        self.export()
        self.sock.send('open|' + ':'.join(self.objs))
        self.load_confirm()
        pass

    def load_confirm(self):
        if self.sock.recv(1024)=='loaded':
            print 'zbrush loaded:'
            print ('\n'.join(self.objs))

    def export(self):
        
        self.objs = cmds.ls(selection=True,type='mesh',dag=True)

        if self.objs:
            self.parse_objs()

        
        for obj in self.objs:
            
            cmds.select(cl=True)
            cmds.select(obj)
            cmds.delete(ch=True)
            self.ascii_path = utils.make_file_name(obj)

            cmds.file(  self.ascii_path,
                        force=True,
                        options="v=0",
                        type="mayaAscii",
                        exportSelected=True)

    def parse_objs(self):

        cmds.select(cl=True)
        cmds.select(self.objs)
        cmds.pickWalk(direction='up')
        self.objs = cmds.ls(selection=True)
        cmds.select(self.objs)
        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)

        self.goz_check()

        pass

    def goz_check(self):


        for obj in self.objs:
            
            goz_check=cmds.attributeQuery('GoZBrushID',node=obj,exists=True)

            if goz_check:
                goz_id=cmds.getAttr(obj+'.GoZBrushID')
                if obj!=goz_id:
                    print obj, goz_id,'name mismatch'
            else:
                history=cmds.listHistory(obj)
                for old_obj in history:
                    goz_check=cmds.attributeQuery('GoZBrushID',
                                                    node=old_obj,
                                                    exists=True)
                    if goz_check:
                        goz_id=cmds.getAttr(old_obj+'.GoZBrushID')
                        if obj!=goz_id:
                            print 'rename'
        pass


    def relink(self):
        obj=self.obj
        goz_id=self.goz_id
        pre_sel=cmds.ls(sl=True)
        cmds.delete(obj,ch=True)
        cmds.rename(obj,goz_id)
        cmds.select(cl=True)
        cmds.select(goz_id)
        shape=cmds.pickWalk(direction='down')[0]
        goz_check=cmds.attributeQuery('GoZBrushID',node=shape,exists=True)
    
        if goz_check is False:
            cmds.addAttr(shape,longName='GoZBrushID',dataType='string')
        cmds.setAttr(shape+'.GoZBrushID',goz_id,type='string')
        cmds.select(cl=True)
        pre_sel.remove(obj)
        pre_sel.append(goz_id)
        cmds.select(pre_sel)

    def create(self):
        obj=self.obj
        
        pre_sel=cmds.ls(sl=True)
        cmds.delete(obj,ch=True)
        cmds.select(cl=True)
        cmds.select(obj)
        shape=cmds.pickWalk(direction='down')[0]
        goz_check=cmds.attributeQuery('GoZBrushID',node=shape,exists=True)
        if goz_check:
            cmds.setAttr(shape+'.GoZBrushID',obj,type='string')
        cmds.select(pre_sel)
