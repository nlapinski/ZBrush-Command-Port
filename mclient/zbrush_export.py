#!/usr/bin/python
from multiprocessing import Process
import sys
import socket
import os
from subprocess import *
from tempfile import *
import time


def send_osa(script_path):
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
    while os.path.isfile(lock_file) == False:
        print 'waiting'
    os.remove(lock_file)
    maya = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    maya.connect(("192.168.1.20", 6667))
    maya.send(mayaCMD)
    maya.close()

if __name__ == "__main__":

    file = (sys.argv)[1]
    tool = (sys.argv)[2]
    func = (sys.argv)[3]
    env = '$ZDOCS'

    if func == '0':
        zs_temp = zbrush_save(file, env,tool)
        send_osa(zs_temp)
    if func == '1':
        send_to_maya(file,env.replace('$',''))
