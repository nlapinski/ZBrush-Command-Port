#!/usr/bin/python

import socket
import subprocess
import time
import os
from tempfile import *
import sys



def send_osa(script_path):
    cmd = ['osascript -e',
           '\'tell app "ZBrush"',
           'to open',
           '"' + script_path + '"\'']

    cmd = ' '.join(cmd)
    ret = os.system(cmd)
    return ret

def zbrush_gui():

    """Creates a gui when zserv starts in zbrush for send all/single obj

    -make zscript
    -send osa/apple tell
    -'save_file' zscript sends one
    -'save_all' iterates subtools and saves each
    -buttons call python, python calls zscript, then more python
    ^this is where it gets really convoluded,
    however its to prevent locking ZBrush execution
    
    zbrush_export(save) is called, and creates a save funciton then send to maya
    
    """


    print 'init gui'
    zs_temp = NamedTemporaryFile(delete=False,suffix='.txt')

    zscript = """
                
            [RoutineDef, save_file,

            [VarSet, name, [FileNameExtract, [GetActiveToolPath], 2]]
            [IPress, Tool:SubTool:All Low]
            [VarSet, path, "/usr/bin/python -m mclient.zbrush_export "]
            [VarSet, q, [SubToolGetActiveIndex]]
            [ShellExecute,
            [StrMerge,[StrMerge, #path, [StrMerge,[StrMerge, name, " "],#q]]," 0"]]
             ]

            [IButton, "TOOL:Send to Maya", "Export model as a *.ma to maya",
            [RoutineCall, save_file]
            ]

            [RoutineDef, save_all,
            [VarSet,t,0]
            [IPress, Tool:SubTool:All Low]
            [SubToolSelect,0]
            [Loop, [SubToolGetCount], 

            [VarSet, t, t+1]
            [SubToolSelect,t-1]
            [VarSet, name, [FileNameExtract,[GetActiveToolPath],2]]
            [VarSet, path, "/usr/bin/python -m mclient.zbrush_export "]
            [VarSet, q, [Val, #t-1]]
            [ShellExecute,
            [StrMerge,[StrMerge, #path, [StrMerge,[StrMerge, name, " "],#q]]," 0"]]

            ]
            ]


            [IButton, "TOOL:Send all", "Export model as a *.ma to maya",

            [RoutineCall, save_all]

            ]

            """

    zs_temp.write(zscript)
    return zs_temp.name

def zbrush_open(name):

    """open a file with zbrush
    
    -create temp zscript file
    -load with file open commands
    -replace #TOOLNAME/#FILENAME with maya path/filename
    -iterate through current subtools to check for 'matches'
    -import if match, append new cloned tool for unique tools

    """

    zs_temp = NamedTemporaryFile(delete=False, suffix='.txt')
    env = os.getenv('ZDOCS')
    print env

    #zbrush script to iterate through sub tools and open matches, appends new tools
    zscript = """
            [RoutineDef, open_file,
            [FileNameSetNext,"!:#FILENAME"]
            [VarSet,in_tool,#TOOLNAME]
            [VarSet,imp,0]
            [Loop, [SubToolGetCount],
            [VarSet, a, a+1]
            [SubToolSelect,a-1]
            [VarSet, sub, [FileNameExtract,[GetActiveToolPath],2]]
            [If, [StrFind, in_tool, sub]>-1,
                [IPress,Tool:Import]
                [VarSet,imp,1],]
            ]
            [If, imp<1,
                    [If, a==[SubToolGetCount],


                        [IPress,Tool:SubTool:Duplicate]
                        [IPress,Tool:SubTool:MoveDown]
                        [IPress,Tool:Geometry:Del Higher]
                        [IPress,Tool:Import]
                        [ToolSetPath,[SubToolGetCount],"!:#FILENAME"]
                        , [MessageOk, False]
                    ]
            ]
            ]
            [RoutineCall,open_file]
                """

    zscript = zscript.replace('#FILENAME',os.path.join(env, name))
    zscript = zscript.replace('#TOOLNAME',name.replace('.ma',''))
    zs_temp.write(zscript)
    return zs_temp.name

def listen():

    """waits for file open commands from maya, iterates obj list """

    HOST = socket.gethostbyname(socket.getfqdn())
    PORT = 6668

    print 'Default IP: '+str(HOST)+':'+str(PORT)

    znet = os.getenv('ZNET')

    if znet is not None:
        print 'Env IP: '+str(znet)
        HOST=znet.split(':')[0]
        PORT=znet.split(':')[1]

    if len(sys.argv)==2:
        args = (sys.argv)[1]
        print 'User IP: '+str(args)
        HOST=args.split(':')[0]
        PORT=int(args.split(':')[1])


    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    time.sleep(2)
    soc.bind((HOST, PORT))
    soc.listen(1)
    conn, addr = soc.accept()

    while 1:
        try:
            data = conn.recv(1024)
        except:
            print "err"
            break
        if not data:
            break
        if(data.split('|')[0] == 'open'):
            objs = data.split('|')[1].split(':')
            for obj in objs:
                print obj
                zs_temp = zbrush_open(obj+'.ma')
                send_osa(zs_temp)

    conn.close()
    print "end"

if __name__ == "__main__":
    zbrush_ui_script = zbrush_gui()
    err_code = send_osa(zbrush_ui_script)
    while err_code != 0:
        err_code = send_osa(zbrush_ui_script)
    print 'status: '+str(err_code)
    print 'listen'
    while 1:
        listen()
