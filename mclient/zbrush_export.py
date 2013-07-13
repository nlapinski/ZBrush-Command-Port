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
    -removes zbrush temp lock file
    -grabs the mnet env for IP/PORT or defaults 
    """

    file_path = os.path.join(SHARED_DIR_ENV, file + '.ma')

    print file_path
    mayaCMD = 'import zclient'
    mayaCMD += '\n'
    mayaCMD += 'zclient.main.get_from_zbrush("'+file_path+'")'

    # wait until the zbrush file has finished saving before sending
    # the import command to maya
    
    lock_file = os.path.expandvars(file_path).replace('.ma', '.zzz')
    #added timeout check to prevent loop from breaking
    time_out = time.time()+5
    
    while os.path.isfile(lock_file) == False:
        print 'waiting'
        time.sleep(1)
        if time.time()>time_out:
            print 'timeout'
            break
    try:
        os.remove(lock_file)
    except:
        print 'no lock file, sending anyway'

    maya = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print mayaCMD

    # FIXME: get rid of this default value. error if MNET is not set
    mnet = os.getenv('MNET', "localhost:6667")
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
    send_to_maya(file)
