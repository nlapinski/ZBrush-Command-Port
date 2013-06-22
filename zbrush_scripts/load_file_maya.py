#!/usr/bin/python

import sys
import socket
import os
import time
from subprocess import *
from tempfile import *


file = (sys.argv)[1]
env = (sys.argv)[2]

print file, env


def send_to_maya(file, env):

    if(os.environ.get('ZDOCS') == None):
        # this might need to differ from the path for zbrush to save if it is
        # being sent to linux
        env = '/your/path/for/maya/to/load/files'
    env = '$' + env

    file_path = os.path.join(env, file + '.ma')
    mayaCMD = 'import maya.cmds as cmds'
    mayaCMD += '\n'
    mayaCMD += 'import maya.mel as mel'
    mayaCMD += '\n'
    mayaCMD += 'try:'
    mayaCMD += '\n'
    mayaCMD += '    cmds.delete("' + file + '")'
    mayaCMD += '\n'
    mayaCMD += 'except:'
    mayaCMD += '\n'
    mayaCMD += '    print "error"'
    mayaCMD += '\n'
    mayaCMD += 'print "' + file_path + '"'
    mayaCMD += '\n'
    mayaCMD += 'cmds.file("' + file_path + '",i=True,uns=False,rdn=True)'
    mayaCMD += '\n'
    mayaCMD += 'print "SENT"'
    mayaCMD += '\n'
    lock_file = os.path.expandvars(file_path).replace('.ma', '.zzz')
    while os.path.exists(lock_file) == False:
        print 'waiting'
    os.remove(lock_file)
    maya = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    maya.connect(("129.25.142.85", 6667))
    maya.send(mayaCMD)
    maya.close()

send_to_maya(file, env)
