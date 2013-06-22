#!/usr/bin/python

import socket
import maya.cmds as cmds
import os
import time


def send_to_zbrush(h, p):

    check_env = os.environ.get('ZDOCS')
    env = '$ZDOCS'

    if(check_env == None):
        print 'no env'
        env = "/your/file/path/for/maya/to/save/files"

    cmds.delete(ch=True)
    objs = cmds.ls(selection=True)

    name = os.path.relpath(objs[0] + '.ma')

    ascii_file = os.path.join(env, name)
    print ascii_file

    cmds.file(ascii_file, type="mayaAscii", es=True)

    time.sleep(8)

    HOST = h
    PORT = p
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.send('open|' + name)
    s.close()
