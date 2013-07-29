#!/usr/bin/python
import sys
import socket
import os
from subprocess import *
import time

SHARED_DIR_ENV='$ZDOCS'


"""

This module is execute as a script from within zbrush
It takes a name from zbrush sends a load command to maya

"""

def send_to_maya(file):
    """send a file to maya

    -calls get_from_zbrush() in zclient.main in maya
    -grabs the mnet env for IP/PORT or defaults 
    """

    file_path = os.path.join(SHARED_DIR_ENV, file + '.ma')

    print file_path
    mayaCMD = 'import __main__'
    mayaCMD += '\n'
    #mayaCMD += 'zclient.main.get_from_zbrush("'+file_path+'")'
    mayaCMD += '__main__.mayagui.serv.load("'+file_path+'")'
    #mayaCMD += 'mayagui.serv.load("'+file_path+'")'

    print mayaCMD
    maya = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # defaults to local if not set


    mnet = os.environ.get('MNETa')
    
    if mnet:
        host, port = mnet.split(':')
    else:
        port = 6667
        host = socket.gethostbyname(socket.getfqdn())


    maya.connect((host, int(port)))
    maya.send(mayaCMD)
    maya.close()

    return 'DONE'

if __name__ == "__main__":

    """send to maya/save from zbrush

    -arg 1: object name ie: pSphere1
    -arg 2: zbrush object index (base 0)

    """

    file = (sys.argv)[1]
    
    ret = send_to_maya(file)
    print ret
