#!/usr/bin/python

import socket
import maya.cmds as cmds
import os
import time
import sys

def start(ip,port):
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
    addr= ip+':'+str(port)
    try:
        cmds.commandPort(n=addr,close=True)
        print 'closing... '+addr
    except:
        print 'no open sockets'


def send_to_zbrush(host, port):

    env = '$ZDOCS'

    cmds.delete(ch=True)
    objs = cmds.ls(selection=True)

    if objs:

        for obj in objs:
            print obj

        print 'Maya >> ZBrush'
        print host+':'+port

        name = os.path.relpath(objs[0] + '.ma')

        ascii_file = os.path.join(env, name)
        print ascii_file
        try:
            os.remove(os.path.expandvars(ascii_file))
        except:
            pass

        cmds.file(ascii_file, type="mayaAscii", es=True)

        time.sleep(8)
  
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, int(port)))
        s.send('open|' + name)
        s.close()

    else: 
        print 'Select an object'
