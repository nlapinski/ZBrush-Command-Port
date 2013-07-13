#!/usr/bin/python

import socket
import maya.cmds as cmds
import maya.mel as mel
import os
import time
import sys
import stat

SHARED_DIR_ENV = '$ZDOCS'

"""a collection of helper functions to manage command port creation 

-manages sending and reciving meshes from zbrush
-constructs lists of file names to send to mclient.zserv

"""

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
    else:
        print 'cmd port open... %s:%s'%(ip,port)

    status = cmds.commandPort("%s:%s"%(ip,port),q=True)


    return status

def stop(ip,port):
    """close a maya command port """
    try:
        cmds.commandPort(name="%s:%s"%(ip,port),close=True)
        print 'closing... '+addr
    except:
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

def send_to_zbrush(host, port):
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
    else:
        print 'found ZDOCS'


    #send only mesh types!
    objs = cmds.ls(selection=True,type='mesh',dag=True)
    cmds.select(cl=True)
    cmds.select(objs)
    cmds.pickWalk(direction='up')
    objs = cmds.ls(selection=True)
    
    if objs:

        cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
        cmds.delete(ch=True)

        for obj in objs:
            cmds.select(cl=True)
            cmds.select(obj)
            print obj
            print 'Maya >> ZBrush'
            print host+':'+port
            name = os.path.relpath(obj + '.ma')
            ascii_file = os.path.join(SHARED_DIR_ENV, name)
            expanded_path = os.path.expandvars(ascii_file)
            print ascii_file
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

        # FIXME: deal with connection errors
        # FIXME: shouldn't we connect once and send many times, instead of connect for each object?
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, int(port)))
            s.send('open|' + ':'.join(objs))
            print ('open|' + ':'.join(objs))
            s.close()
        except:
            print 'Too many send commands'

    else:
        #raises a error for gui to display
        raise IndexError
