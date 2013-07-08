#!/usr/bin/python

import sys
import socket
import os
from subprocess import *
from tempfile import *
import time
file = (sys.argv)[1]
tool = (sys.argv)[2]

check_env = os.environ.get('ZDOCS')
env = '$ZDOCS'

if(check_env == None):
    print 'no env'
    env = "/your/file/path/for/zbrush/to/save/files"


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

    zscript = '[RoutineDef, save_file,'
    zscript += '[SubToolSelect,'+tool+']'
    zscript += '[FileNameSetNext,"!:'
    zscript += os.path.join(env_expand, file + '.ma')
    print file
    zscript += '","ZSTARTUP_ExportTamplates\Maya.ma"]'
    zscript += '[IPress,Tool:Export]'
    zscript += '[MemCreate, zzz, 1, 0]'
    zscript += '[MemSaveToFile, zzz,"!:' + \
        os.path.join(env_expand, file + '.zzz') + '"]'
    script_name = 'zbrush_scripts/load_file_maya.py'
    script_path = os.path.join(env_expand, script_name)
    print env
    zscript += '[ShellExecute,"' + script_path + ' ' + \
        file + ' ' + str(env).replace('$', '') + '"]'
    zscript += '[Exit]'
    zscript += ']'
    zscript += '[RoutineCall,save_file]'
    print zscript
    zs_temp.write(zscript)
    return zs_temp.name

zs_temp = zbrush_save(file, env,tool)
send_osa(zs_temp)
