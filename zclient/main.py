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

    """opens a maya command port, checks for open ports and closes them """
    
    addr= ip+':'+str(port)

    
    try:
        cmds.commandPort(n=addr,sourceType='python')
        print 'opening... '+addr
    except:
        print 'error creating socket on:'
        print addr

    status = cmds.commandPort(addr,q=True)


    return status

def stop(ip,port):

    """close a maya command port """
    
    addr= ip+':'+str(port)
    try:
        cmds.commandPort(n=addr,close=True)
        print 'closing... '+addr
    except:
        print 'no open sockets'

def get_from_zbrush(file_path):


    """loads *.ma from zbrush, called via command port in mclient.zbrush_export
        
        -cleanup
        -load file

    """

    ascii_file=os.path.splitext(file_path)[0]
    ascii_file=os.path.split(ascii_file)[1]
    print ascii_file

    try:
        cmds.delete(ascii_file)
    except:
        print 'object does not exist'
    try:
        cmds.delete(ascii_file+'_blinn')
        cmds.delete(ascii_file+'_blinnSG')
        cmds.delete(ascii_file+'_materialInfo')
        cmds.delete(ascii_file+'_ZBrushTexture')
        cmds.delete(ascii_file+'_place2dTexture2')
    except:
        print ascii_file+' does not need cleanup'
    print file_path
    cmds.file(file_path,i=True,uns=False,rdn=True)
    print 'got: '+ascii_file

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
            try:
                os.remove(expanded_path)
            except:
                pass

            cmds.file(  ascii_file,
                        force=True,
                        options="v=0",
                        type="mayaAscii",
                        exportSelected=True)
            #make sure zbrush can acess this file
            os.chmod(expanded_path,stat.S_IRWXO | stat.S_IRWXU | stat.S_IRWXG)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, int(port)))
        s.send('open|' + ':'.join(objs))
        print ('open|' + ':'.join(objs))
        s.close()

    else: 
        print 'Select an object'
