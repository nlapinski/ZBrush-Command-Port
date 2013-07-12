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
    mayaCMD = 'import zclient'
    mayaCMD += '\n'
    mayaCMD += 'zclient.main.get_from_zbrush("'+file_path+'")'
    
    maya = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # FIXME: get rid of this default value. error if MNET is not set
    mnet = os.getenv('MNET', "192.168.1.20:6667")
    host, port = mnet.split(':')

    maya.connect((host, int(port)))
    maya.send(mayaCMD)
    maya.close()

if __name__ == "__main__":

    """send to maya/save from zbrush

    -arg 1: object name ie: pSphere1
    -arg 2: zbrush object index (base 0)

    """

    file = (sys.argv)[1]
    tool = (sys.argv)[2]
    
    send_to_maya(file)
