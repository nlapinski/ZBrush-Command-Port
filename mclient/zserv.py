#!/usr/bin/python

import SocketServer
import socket
import subprocess
import time
import os
import sys

"""
Starts a server which listens for commands sent from Maya.
When it receives an 'open|path1:path2' command,
triggers the opening of the zbrush files via appleScript

On load if ZBrush is not open it will try to open it 
and install 2 GUI buttons for sending single or all meshes to maya

ZBrush server extends the socket server request handler

"""

SHARED_DIR_ENV='$ZDOCS'

class ZBrushServer(SocketServer.ThreadingMixIn,SocketServer.TCPServer):
    """
    ZBrush server, allows quick rebind
    """
    
    daemon_threads=True
    allow_reuse_address=True

    def __init__(self,server_address,RequestHandlerClass):
        SocketServer.TCPServer.__init__(
                    self,
                    server_address,
                    RequestHandlerClass)


class ZBrushHandler(SocketServer.BaseRequestHandler):
    """
    The base RequestHandler for accepting commands from maya

    It is instantiated once per connection to the server (1)

    """

    def handle(self):
        while 1:
            try:

                self.data = self.request.recv(1024).strip()
                if not self.data:
                    break
                    self.request.close()
                print '\n\n'
                print '{} sent:'.format(self.client_address[0])
                print self.data

                if self.data.split('|')[0] == 'open':
                    objs = self.data.split('|')[1].split(':')
                    for obj in objs:
                        print 'got: '+obj
                        zs_temp = zbrush_open(obj+'.ma')
                        send_osa(zs_temp)
                    print 'loaded all objs!'
                    self.request.send('loaded')
            except KeyboardInterrupt:
                self.request.close()
                break



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
    -buttons call python to send files to maya via mclient.zbrush_export
    
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
        [VarSet, lock_name,[FileNameExtract, [GetActiveToolPath], 2]]
        [FileNameSetNext, #export_path,"ZSTARTUP_ExportTamplates\Maya.ma"]
        [IPress,Tool:Export]
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
            [VarSet, lock_name,[FileNameExtract, [GetActiveToolPath], 2]]
            [FileNameSetNext, #export_path,"ZSTARTUP_ExportTamplates\Maya.ma"]
            [IPress,Tool:Export]
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

    #zbrush script to iterate through sub tools,
    #and open matches, appends new tools

    zscript = """
            [RoutineDef, open_file,
            [FileNameSetNext,"!:#FILENAME"]
            [VarSet,in_tool,#TOOLNAME]
            [VarSet,imp,0]
            [Loop, [SubToolGetCount],
            [FileNameSetNext,"!:#FILENAME"]
            [VarSet, a, a+1]
            [SubToolSelect,a-1]
            //[VarSet, sub, [FileNameExtract,[GetActiveToolPath],2]]

            [VarSet,SubToolTitle,[IgetTitle, Tool:Current Tool]]
            [VarSet,sub, [FileNameExtract, SubToolTitle, 2]]


            [If,([StrLength,in_tool]==[StrLength,sub])&&([StrFind,sub,in_tool]>-1),
                [IPress,Tool:Import]
                [VarSet,imp,1],]
                //[LoopExit]
            ]
            [If, imp<1,
                    [If, a==[SubToolGetCount],
                        [IPress,Tool:SubTool:Duplicate]
                        [IPress,Tool:SubTool:MoveDown]
                        [IPress,Tool:Geometry:Del Higher]
                        [FileNameSetNext,"!:#FILENAME"]
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

if __name__ == "__main__":
    zbrush_ui_script = zbrush_gui()
    err_code = send_osa(zbrush_ui_script)

    while err_code != 0:
        err_code = send_osa(zbrush_ui_script)
    print "GUI Installed" if not err_code else 0


    host = socket.gethostbyname(socket.getfqdn())
    port = 6668

    try:
        server = ZBrushServer((host,port),ZBrushHandler)
        server.allow_reuse_address=True
    except socket.error, e:
        import errno
        print e
        if '[Errno 48]' in str(e):
            print 'please wait a few seconds before relaunching'
        else:
            print 'unhandled exception!'
    else:
        try:
            print 'Sever started!'
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
            print "Server shutting down!"
