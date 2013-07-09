#!/usr/bin/python
from multiprocessing import Process
import sys
import socket
import os
from subprocess import *
from tempfile import *
import time


def send_osa(script_path):
    """send osa/apple script from zbrush via the shell"""
    
    cmd = ['osascript -e',
           '\'tell app "ZBrush"',
           'to open',
           '"' + script_path + '"\'']

    cmd = ' '.join(cmd)
    print cmd
    script = Popen(cmd, shell=True)
    # script.communicate()
    # Popen(cmd.replace('.txt','.zsc'))


def zbrush_save(file, env, tool):
    """save a file from zbrush

    -creates a tmp file to load with zscript
    -zscript is sent to zbrush with save commands
    -after save writes a temp lock file 
    -starts a new python script that waits for the temp file
    -after temp file is created send file paths to maya

    """

    # FIXME: don't pass the environment variable name, define it in a constant
    zs_temp = NamedTemporaryFile(delete=False, suffix='.txt')
    env_expand = os.path.expandvars(env)
    print env

    zscript = '[RoutineDef, save_f,'
    zscript += '[SubToolSelect,'+tool+']'
    zscript += '[FileNameSetNext,"!:'
    zscript += os.path.join(env_expand, file + '.ma')
    print file
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
    print zscript
    zs_temp.write(zscript)
    return zs_temp.name


def send_to_maya(file, env):
    """send a file to maya

    -cleans up past objects/shaders/textures
    -removes object from maya if it exists
    -loads object saved from zbrush
    -removes zbrush temp lock file

    """
    # FIXME: don't pass the environment variable name, define it in a constant
    env = '$' + env

    file_path = os.path.join(env, file + '.ma')

    # FIXME: put all this code in a function that maya can import and execute on the other side
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
    mayaCMD += 'try:'
    mayaCMD += '\n'
    mayaCMD += '    cmds.delete("'+file+'_blinn")'
    mayaCMD += '\n'
    mayaCMD += '    cmds.delete("'+file+'_blinnSG")'
    mayaCMD += '\n'
    mayaCMD += '    cmds.delete("'+file+'_materialInfo")'
    mayaCMD += '\n'
    mayaCMD += '    cmds.delete("'+file+'_ZBrushTexture")'
    mayaCMD += '\n'
    mayaCMD += '    cmds.delete("'+file+'_place2dTexture2")'
    mayaCMD += '\n'
    mayaCMD += 'except:'
    mayaCMD += '\n'
    mayaCMD += '    print "'+file+'_blinn'+ ' does not exist"'
    mayaCMD += '\n'
    mayaCMD += 'print "' + file_path + '"'
    mayaCMD += '\n'
    mayaCMD += 'cmds.file("' + file_path + '",i=True,uns=False,rdn=True)'
    mayaCMD += '\n'
    mayaCMD += 'print "SENT"'
    mayaCMD += '\n'

    # wait until the zbrush file has finished saving before sending
    # the import command to maya
    lock_file = os.path.expandvars(file_path).replace('.ma', '.zzz')
    # FIXME: add a timeout here to avoid infinite loop
    while os.path.isfile(lock_file) == False:
        print 'waiting'
    os.remove(lock_file)
    maya = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   
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
    env = '$ZDOCS'

    if func == '0':
        zs_temp = zbrush_save(file, env,tool)
        send_osa(zs_temp)
    if func == '1':
        send_to_maya(file,env.replace('$',''))
