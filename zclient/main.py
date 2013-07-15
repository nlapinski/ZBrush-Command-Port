#!/usr/bin/python

import socket
import maya.cmds as cmds
import maya.mel as mel
import os
import time
import sys
import stat

from zclient import err

SHARED_DIR_ENV = '$ZDOCS'

"""a collection of helper functions to manage command port creation 

-manages sending and reciving meshes from zbrush
-constructs lists of file names to send to mclient.zserv

"""

# FIXME: make a MayaServer class ----------
def start(ip,port):
    """opens a maya command port, checks for open ports and closes them

        maya commandport does not resolve localhost to the machines external IP
        this can depend on your /etc/hosts file 
        maya resolves localhost to localhost.localdomain or 127.0.0.1

        This type of binding is only usable by the local interface

        opening a port on 'localhost:port' should not conflict with 'host:port'
        however 'host:port' is externally accessible where host is the domain/device name

        this can be checked with  lsof -i | grep maya.bin

        This case can differ slightly  on OSX or Windows

        To be on the safe side a manual IP/host specification is allowed but socket.gfqdn
        should work most of the time, however it can return 'localhost' if no 
        fully qualified domain name is resolved
    
    """

    try:
        cmds.commandPort(name="%s:%s" % (ip,port),
                        echoOutput=False,
                        sourceType='python')

        print 'opening... %s:%s' % (ip,port)
    
    except RuntimeError, err:
        import errno
        if ('(%s)' % errno.EADDRINUSE) in str(err):
            print 'socket in use'
        else:
            print 'failed to open commandport'
            raise err
    else:
        print 'cmd port open... %s:%s'%(ip,port)

    status = cmds.commandPort("%s:%s"%(ip,port),q=True)


    return status

def stop(ip,port):
    """close a maya command port """
    try:
        cmds.commandPort(name="%s:%s"%(ip,port),close=True)
        print 'closing... '
    except RuntimeError:
        print 'no open sockets'

def get_from_zbrush(file_path):
    """
    loads *.ma from zbrush, called via command port in mclient.zbrush_export
        
        -cleanup
        -load file

    """
    #shape name is the same as the filename
    #split file/ext for shape name, used to remove conflicting nodes
    ascii_file=os.path.splitext(file_path)[0]
    ascii_file=os.path.split(ascii_file)[1]
    
    #clean up nodes, based on shape name/file name
    nodes=[ 'blinn',
            'blinnSG',
            'materialInfo',
            'ZBrushTexture',
            'place2dTexture2']

    try:
        cmds.delete(ascii_file)
    except Exception as e:
        if 'No object' in str(e):
            print str(e).replace('No object matches name:','Skipping:')
            pass
        else:
            raise e
    else:
        print 'Removed: ' + ascii_file

    for cleanup in nodes:
        try:
            cmds.delete(ascii_file+'_'+cleanup)
        except Exception as e:
            if 'No object' in str(e):
                print str(e).replace('No object matches name:','Skipping:')
                pass
            else:
                raise e
        else:
            print 'Removed: '+ascii_file+'_'+cleanup

    #note there is no longflag for import,-i or i=True
    cmds.file(file_path,i=True,usingNamespaces=False,removeDuplicateNetworks=True)
    print 'Imported: '+ascii_file

# FIXME: ------ end MayaServer class ----------


# FIXME: make a ZBrushClient class ----------
def open_zbrush_client(host,port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, int(port)))
    except socket.error, e:
        raise e
    return s

def close_zbrush_client(sock):
    sock.close()

# FIXME: not in ZBrushClient 
def relink(obj,goz_id):
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
    print 'relink'

# FIXME: not in ZBrushClient 
def create(obj,goz_id):
    pre_sel=cmds.ls(sl=True)
    cmds.delete(obj,ch=True)

    cmds.select(cl=True)
    cmds.select(obj)
    shape=cmds.pickWalk(direction='down')[0]

    goz_check=cmds.attributeQuery('GoZBrushID',node=shape,exists=True)
    if goz_check:
        cmds.setAttr(shape+'.GoZBrushID',obj,type='string')
    cmds.select(pre_sel)

def send_to_zbrush(sock):
    """send some objects to zbrush

    -cleans history, freeze xforms
    -grabs UI host/port
    -save asciifiles
    -contructs a command list parsed by mclient.zserv
    -sets permissions on saved files (so zbrush can overwrite)
    -open|obj1:obj2:obj:3 is the listformat
    | denotes end of open commands
    : seperates objects/files
    """

    #check SHARED_DIR_ENV
    try:
        os.environ[SHARED_DIR_ENV.replace('$','')]
    except KeyError:
        print 'ZDOCS not set'
        raise
    else:
        print 'found ZDOCS'

    # FIXME: extract a new function for doing the object exporting work. keep export separate from the socket work
    # ---- start separate function here -------------
    #send only mesh types!
    objs = cmds.ls(selection=True,type='mesh',dag=True)
    cmds.select(cl=True)
    cmds.select(objs)
    cmds.pickWalk(direction='up')
    objs = cmds.ls(selection=True)
    cmds.select(objs)
    
    if objs:

        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
        #cmds.delete(ch=True)

        for obj in objs:
            
            goz_check=cmds.attributeQuery('GoZBrushID',node=obj,exists=True)

            if goz_check:
                goz_id=cmds.getAttr(obj+'.GoZBrushID')
                if obj!=goz_id:
                    print obj, goz_id,'name mismatch'
                    print 'rename'
                    raise err.ZBrushNameError(obj,goz_id,'rename')
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
                            raise err.ZBrushNameError(obj,goz_id,'History: rename')
            

            cmds.select(cl=True)
            cmds.select(obj)
            cmds.delete(ch=True)

            print obj
            print 'Maya >> ZBrush'
            name = os.path.relpath(obj + '.ma')
            ascii_file = os.path.join(SHARED_DIR_ENV, name)
            expanded_path = os.path.expandvars(ascii_file)
            #except if non-existant, new file
            try:
                os.remove(expanded_path)
            except OSError:
                print 'file may not exist, passing'
                pass

            cmds.file(  ascii_file,
                        force=True,
                        options="v=0",
                        type="mayaAscii",
                        exportSelected=True)
            #make sure zbrush can acess this file
            os.chmod(expanded_path,stat.S_IRWXO | stat.S_IRWXU | stat.S_IRWXG)
    # ---- end separate function here, returng list of objects -------------

        #network code only connects once, and sends
        #checks for zbrush response, or mitigates connection errors
        try:
            sock.send('open|' + ':'.join(objs))
            if sock.recv(1024):
                print 'zbrush loaded:'
                print ('\n'.join(objs))
            else:
                raise IOError
        except Exception,e:
            raise e

    else:
        # FIXME: don't just use an index error. use a GoZError, or create a ZBrushClientError (see FIXME in zclient.err)
        #raises a error for gui to display
        raise IndexError


