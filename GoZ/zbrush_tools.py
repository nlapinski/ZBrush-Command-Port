""" starts ZBrushSever, manages MayaClient"""

import SocketServer
from GoZ import utils as utils

class ZBrushServer(object):

    """

    ZBrush server extending SocketServer module, gets meshes from maya

    attributes:
        self.status                    -- current server status (up/down)
        self.host                      -- current host for serving on from utils.get_net_info
        self.port                      -- current port for serving on from utils.get_net_info
        self.cmdport_name              -- formated command port name

    methods:
        start()              -- start the server
        stop()               -- stop the server

    class:
        ZBrushSocketServ     -- configures daemon mode for socketserv module
        ZBrushHandler        -- handles loading objects from maya

    """

    def __init__(self):

        self.host, self.port = utils.get_net_info('ZNET')
        self.server = None
        self.server_thread = None

    def start(self):
        """ looks for previous server, trys to start a new one"""

        utils.writecfg(self.host, self.port, 'ZNET')

        try:
            self.server.shutdown()
            self.server.server_close()
            print 'killing previous server...'
        except AttributeError:
            print 'starting a new server!'

        self.server = self.ZBrushSocketServ(
            (self.host, int(self.port)), self.ZBrushHandler)
        self.server.allow_reuse_address = True
        self.server_thread = utils.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        print 'Serving on %s:%s' % (self.host, self.port)

    def stop(self):
        """ shuts down ZBrushSever"""
        self.server.shutdown()
        self.server.server_close()
        print 'stoping...'

    class ZBrushSocketServ(SocketServer.ThreadingMixIn, SocketServer.TCPServer):

        """ extends socket server with custom settings"""
        timeout = 5
        daemon_threads = True
        allow_reuse_address = True

        # handler is the RequestHandlerClass
        def __init__(self, server_address, handler):
            SocketServer.TCPServer.__init__(
                self,
                server_address,
                handler)

        def handle_timeout(self):
            print 'TIMEOUT'

    class ZBrushHandler(SocketServer.BaseRequestHandler):

        """ custom handler for ZBrushSever"""

        def handle(self):
            # keep handle open until client/server close
            while True:
                data = self.request.recv(1024).strip()
                if not data:
                    self.request.close()
                    break
                print '\n\n'
                print '{} sent:'.format(self.client_address[0])
                print data
                # check for conn-reset/disconnect by peer (on client)
                if data == 'check':
                    self.request.send('ok')

                # parse object list from maya
                if data.split('|')[0] == 'open':
                    objs = data.split('|')[1].split(':')
                    for obj in objs:
                        print 'got: ' + obj
                        zs_temp = self.zbrush_open(obj + '.ma')
                        utils.send_osa(zs_temp)
                    print 'loaded all objs!'
                    self.request.send('loaded')

        # posibly revert to non static
        @staticmethod
        def zbrush_open(name):
            """open a file with zbrush
            -create temp zscript file
            -load with file open commands
            -replace #TOOLNAME/#FILENAME with maya path/filename
            -iterate through current subtools to check for 'matches'
            -import if match, append new cloned tool for unique tools

            """
            script_path = utils.os.path.dirname(
                utils.os.path.abspath(__file__))
            script_path = utils.os.path.join(script_path, 'zbrush_load.txt')
            zs_temp = open(script_path, 'w+')

            env = utils.os.getenv(utils.SHARED_DIR_ENV)
            print env

            # zbrush script to iterate through sub tools,
            # and open matches, appends new tools

            zscript = """
                    [RoutineDef, open_file,
                    [IPress, Tool:SubTool:All Low]
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

            zscript = zscript.replace(
                '#FILENAME', utils.os.path.join(env, name))
            zscript = zscript.replace('#TOOLNAME', name.replace('.ma', ''))
            zs_temp.write(zscript)
            return zs_temp.name


class MayaClient(object):

    """
    Maya client used for sending meshes to maya

    attributes:
        self.host        -- current host obtained from utils.get_net_info
        self.port        -- current port obtained from utils.get_net_info

    methods:
        zscript_ui       -- creates UI for ZBrush (appears in ZBrush)
        test_client      -- tests connection to maya
        send             -- sends meshes to maya
    """

    def __init__(self):
        self.host, self.port = utils.get_net_info('MNET')

    @staticmethod
    def zscript_ui():
        """ assembles a zscript to be loaded by ZBrush to create GUI buttons """

        #grab the current path of this file, make a temp file in the same location
        script_path = utils.os.path.dirname(utils.os.path.abspath(__file__))
        script_path = utils.os.path.join(script_path, 'zbrush_gui.txt')
        zs_temp = open(script_path, 'w+')

        #zscript to create the 'send' button
        zscript = """
        [RoutineDef, send_file,
            //set lowest subtool resolution
            [IPress, Tool:SubTool:All Low]
            
            //base path for saving files
            //'!:' is required to prefix paths in ZBrush
            //   #ENVPATH is replaced with the expanded SHARED_DIR_ENV
            [VarSet, env_path, "!:#ENVPATH/"]
            
            //extracts the current active tool name
            [VarSet, tool_name,[FileNameExtract, [GetActiveToolPath], 2]]
            
            //appends .ma to the path for export, construct filename
            [VarSet, file_name, [StrMerge,tool_name,".ma"]]
            
            //python module execution command
            [VarSet, module_path, "/usr/bin/python -m GoZ.zbrush_tools "]
            
            //append env to file path
            [VarSet, export_path, [StrMerge,env_path,file_name] ]
            
            //set the maya 'tamplate?' I think ofer spelled something wrong
            //this sets the file name for the next export \w correct 'tamplate'
            [FileNameSetNext, #export_path,"ZSTARTUP_ExportTamplates\Maya.ma"]
            
            //finally export the tool
            [IPress,Tool:Export]

            //trigger the python module to send maya the load commands
            [ShellExecute,
                //merge the python command with the tool name
                [StrMerge, #module_path,
                        #tool_name
                ]
            ]
        ]
        
        //gui button for triggering this script
        [IButton, "TOOL:Send to Maya", "Export model as a *.ma to maya",
            [RoutineCall, send_file]
        ]

        """
        # zscript to create the 'send -all' button
        zscript += """
        [RoutineDef, send_all,

            //set all tools to lowest sub-d 
            [IPress, Tool:SubTool:All Low]

            //iterator variable
            [VarSet,t,0]

            //start at the first subtoo
            [SubToolSelect,0]

            //iterate through all subtools
            [Loop,[SubToolGetCount],
                
                //increment iterator
                [VarSet,t,t+1]

                //select current subtool index in loop
                [SubToolSelect,t-1]

                //set base export path #ENVPATH is replace with SHARED_DIR_ENV (expanded)
                [VarSet, env_path, "!:#ENVPATH/"]

                //current tool name
                [VarSet, tool_name, [FileNameExtract, [GetActiveToolPath], 2]]

                //start constructing export file path /some/dir/tool.ma
                [VarSet, file_name, [StrMerge,tool_name,".ma"]]

                //base python module shell command
                [VarSet, module_path, "/usr/bin/python -m GoZ.zbrush_tools "]

                
                //full export path
                [VarSet, export_path, [StrMerge,env_path,file_name] ]
                
                //set export path to be used by next command
                [FileNameSetNext, #export_path,"ZSTARTUP_ExportTamplates\Maya.ma"]
                
                //finally export
                [IPress,Tool:Export]
                [ShellExecute,
                    //join module_path tool_name for maya to load
                    [StrMerge, #module_path, #tool_name]
                ]
            ]
        ]
        [IButton, "TOOL:Send to Maya -all", "Export model as a *.ma to maya",
            [RoutineCall, send_all]
        ]
        """

        env = utils.os.getenv(utils.SHARED_DIR_ENV)
        print env

        zscript = zscript.replace('#ENVPATH', env)
        zs_temp.write(zscript)
        zs_temp.flush()
        zs_temp.close()

        utils.send_osa(script_path)

    def test_client(self):
        """ tests connection with maya, creates a sphere and deletes it """

        utils.writecfg(self.host, self.port, 'MNET')

        maya_cmd = 'import maya.cmds as cmds'
        maya_cmd += '\n'
        maya_cmd += 'cmds.sphere(name="test")'
        maya_cmd += '\n'
        maya_cmd += 'cmds.delete("test")'
        maya = utils.socket.socket(
            utils.socket.AF_INET, utils.socket.SOCK_STREAM)

        try:
            maya.connect((self.host, int(self.port)))
        except utils.socket.error as err:
            print err
            print 'connection refused'
            return False
        else:
            maya.send(maya_cmd)
            maya.close()
            return True

    @staticmethod
    def send():
        """ sends a file to maya"""

        # construct file read path for maya, uses SHARED_DIR_ENV
        name = (utils.sys.argv)[1]
        file_path = utils.make_file_name(name)

        maya_cmd = 'import __main__'
        maya_cmd += '\n'
        maya_cmd += '__main__.mayagui.serv.load("' + file_path + '")'

        maya = utils.socket.socket(
            utils.socket.AF_INET, utils.socket.SOCK_STREAM)
        host, port = utils.get_net_info('MNET')

        maya.connect((host, int(port)))
        maya.send(maya_cmd)
        maya.close()


if __name__ == "__main__":

    # send to maya/save from zbrush
    #-arg 1: object name ie: pSphere
    MayaClient.send()
