#!/usr/bin/python
import sys
import socket
import os
from subprocess import *
from tempfile import *
import time

SHARED_DIR_ENV='$ZDOCS'


def send_osa(script_path):
    """send osa/apple script from zbrush via the shell"""
    
    cmd = ['osascript -e',
           '\'tell app "ZBrush"',
           'to open',
           '"' + script_path + '"\'']

    cmd = ' '.join(cmd)
    print cmd
    script = Popen(cmd, shell=True)


def zbrush_save(file, tool):
    """save a file from zbrush

    -creates a tmp file to load with zscript
    -zscript is sent to zbrush with save commands
    -after save writes a temp lock file 
    -starts a new python script that waits for the temp file
    -after temp file is created send file paths to maya

    """

    zs_temp = NamedTemporaryFile(delete=False, suffix='.txt')
    env_expand = os.path.expandvars(SHARED_DIR_ENV)

    zscript = '[RoutineDef, save_f,'
    zscript += '[SubToolSelect,'+tool+']'
    zscript += '[FileNameSetNext,"!:'
    zscript += os.path.join(env_expand, file + '.ma')
    zscript += '","ZSTARTUP_ExportTamplates\Maya.ma"]'
    zscript += '[IPress,Tool:Export]'
    zscript += '[MemCreate, zzz, 1, 0]'
    zscript += '[MemSaveToFile, zzz,"!:' + \
                os.path.join(env_expand, file + '.zzz') + '"]'

    script_name = '/usr/bin/python -m mclient.zbrush_export'
    zscript += '[ShellExecute,"' + script_name + ' ' +file+ ' '+tool+' '+'1'+ '"]'
    zscript += '[Exit]'
    zscript += ']'
    zscript += '[RoutineCall,save_f]'
    zs_temp.write(zscript)
    return zs_temp.name


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
    time_out = time.time()
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

    mnet = os.getenv('MNET', "192.168.1.20:6667")
    host = mnet.split(':')[0]
    port = mnet.split(':')[1]

    maya.connect((host, int(port)))
    maya.send(mayaCMD)
    maya.close()

if __name__ == "__main__":

    """send to maya/save from zbrush

    -arg 1: object name ie: pSphere1
    -arg 2: zbrush object index (base 0)
    -arg 3: save/send (0/1)

    """

    file = (sys.argv)[1]
    tool = (sys.argv)[2]
    func = (sys.argv)[3]

    if func == '0':
        zs_temp = zbrush_save(file,tool)
        send_osa(zs_temp)
    if func == '1':
        send_to_maya(file)
