#!/usr/bin/python

import socket
import subprocess
import time
import os
import sys

"""Starts a server which listens for commands sent from Maya.
When it receives an 'open|path1:path2' command,
triggers the opening of the zbrush files via appleScript

On load if ZBrush is not open it will try to open it 
and install 2 GUI buttons for sending single or all meshes to maya


"""

SHARED_DIR_ENV='$ZDOCS'

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
    script_path=os.path.dirname(os.path.abspath(__file__))
    script_path=os.path.join(script_path,'zbrush_gui.txt')
    zs_temp = open(script_path,'w+')


    #zscript for sending a sigle file to maya

    zscript="""


[RoutineDef, send_file,

    [VarSet, env_path, "!:#ENVPATH/"]


    [VarSet, name, [FileNameExtract, [GetActiveToolPath], 2]]
    [VarSet, name, [StrMerge,name,".ma"]]

    [IPress, Tool:SubTool:All Low]
    [VarSet, path, "/usr/bin/python -m mclient.zbrush_export "]
    [VarSet, q, [SubToolGetActiveIndex]]
   
    [VarSet, export_path, [StrMerge,env_path,name_ma] ]


    [MemCreate, zzz, 1, 0]

    [VarSet, lock_name,[FileNameExtract, [GetActiveToolPath], 2]]

    [VarSet, lock_file,[StrMerge,env_path,#lock_name,".zzz"]]

    [FileNameSetNext, #export_path,"ZSTARTUP_ExportTamplates\Maya.ma"]

    [IPress,Tool:Export]

    [MemSaveToFile, zzz,lock_file]


    [ShellExecute,
        [StrMerge, #path, 
            [StrMerge,
                [StrMerge, #lock_name, " "],#q
            ]
        ]
    ]



            
]

[IButton, "TOOL:Send to Maya", "Export model as a *.ma to maya",
    [RoutineCall, send_file]
]

    """

    #zscript for sending all files to maya

    zscript+="""


[RoutineDef, send_all,

    [VarSet,t,0]
    [SubToolSelect,0]

    [Loop,[SubToolGetCount],
        [VarSet,t,t+1]
        [SubToolSelect,t-1]

        [VarSet, env_path, "!:#ENVPATH/"]
        [VarSet, name, [FileNameExtract, [GetActiveToolPath], 2]]
        [VarSet, name, [StrMerge,name,".ma"]]
        [IPress, Tool:SubTool:All Low]
        [VarSet, path, "/usr/bin/python -m mclient.zbrush_export "]
        [VarSet, q, [SubToolGetActiveIndex]]
        [VarSet, export_path, [StrMerge,env_path,name_ma] ]
        [MemCreate, zzz, 1, 0]
        [VarSet, lock_name,[FileNameExtract, [GetActiveToolPath], 2]]
        [VarSet, lock_file,[StrMerge,env_path,#lock_name,".zzz"]]
        [FileNameSetNext, #export_path,"ZSTARTUP_ExportTamplates\Maya.ma"]
        [IPress,Tool:Export]
        [MemSaveToFile, zzz,lock_file]
        [ShellExecute,
            [StrMerge, #path, 
                [StrMerge,
                    [StrMerge, #lock_name, " "],#t
                ]
            ]
        ]
    ]       
]

[IButton, "TOOL:Send to Maya -all", "Export model as a *.ma to maya",
    [RoutineCall, send_all]
]

    """


    expanded_env=os.getenv(SHARED_DIR_ENV.replace('$',''))
    zscript=zscript.replace('#ENVPATH',expanded_env)

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

    script_path=os.path.dirname(os.path.abspath(__file__))
    script_path=os.path.join(script_path,'zbrush_load.txt')
    zs_temp = open(script_path,'w+')
    
    env = os.getenv(SHARED_DIR_ENV.replace('$',''))

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
    host = socket.gethostbyname(socket.getfqdn())
    port = 6668

    print 'listening on: '+str(host)+':'+str(port)

    znet = os.getenv('ZNET')

    if znet is not None:
        print 'listening on: '+str(znet)
        host = znet.split(':')[0]
        port = znet.split(':')[1]

    if len(sys.argv)==2:
        args = (sys.argv)[1]
        print 'listening on: '+str(args)
        host = args.split(':')[0]
        port = int(args.split(':')[1])


    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    time.sleep(2)
    soc.bind((host, port))
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
        if data.split('|')[0] == 'open':
            objs = data.split('|')[1].split(':')
            for obj in objs:
                print 'got: '+obj
                zs_temp = zbrush_open(obj+'.ma')
                send_osa(zs_temp)

    conn.close()
    print "loaded all objs"

if __name__ == "__main__":
    zbrush_ui_script = zbrush_gui()
    err_code = send_osa(zbrush_ui_script)
    while err_code != 0:
        err_code = send_osa(zbrush_ui_script)
    print "GUI Installed" if not err_code else 0
    print 'Sever Started!'
    while 1:
        listen()
