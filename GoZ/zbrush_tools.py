""" starts ZBrushSever, manages MayaClient"""
#!/usr/bin/python
import os
import socket
import SocketServer
from threading import Thread
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

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self.status = False

    def start(self):
        """ looks for previous server, trys to start a new one"""

        self.status = False
        
        utils.validate_host(self.host)
        utils.validate_port(self.port)

        if self.server is not None:
            print 'killing previous server...'
            self.server.shutdown()
            self.server.server_close()

        print 'starting a new server!'

        self.server = ZBrushSocketServ((self.host, int(self.port)), ZBrushHandler)
        self.server.allow_reuse_address = True
        self.server_thread = Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        print 'Serving on %s:%s' % (self.host, self.port)
        self.status = True

    def stop(self):
        """ shuts down ZBrushSever"""
        self.server.shutdown()
        self.server.server_close()
        print 'stoping...'
        self.status = False

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
            print data
            # check for conn-reset/disconnect by peer (on client)
            if data == 'check':
                self.request.send('ok')

            # parse object list from maya
            if data.split('|')[0] == 'open':
                print data
                objs = data.split('|')[1].split(':')
                for obj in objs:
                    print 'got: ' + obj
                    parent = obj.split('#')[1]
                    obj = obj.split('#')[0]
                    zs_temp = self.zbrush_open(obj + '.ma',parent)
                    utils.send_osa(zs_temp)
                print 'loaded all objs!'
                self.request.send('loaded')


    @staticmethod
    def zbrush_open(name,parent):
        """open a file with zbrush
        -create temp zscript file
        -load with file open commands
        -replace #TOOLNAME/#FILENAME with maya path/filename
        -iterate through current subtools to check for 'matches'
        -import if match, append new cloned tool for unique tools

        """
        script_path = os.path.dirname(
            os.path.abspath(__file__))
        script_path = os.path.join(script_path, 'zbrush_load.txt')
        zs_temp = open(script_path, 'w+')

        env = os.getenv(utils.SHARED_DIR_ENV)
        print env

        # zbrush script to iterate through sub tools,
        # and open matches, appends new tools


        zscript = """

                //this is a new set of import functions
                //it allows the loop up of top level tools
                //routine to locate a tool by name
                //ZBrush uses ToolID, SubToolID, and UniqueID's 
                //All of these are realative per project/session
                [RoutineDef, findTool,
                    
                    //ToolIDs befor 47 are 'default' tools
                    //48+ are user loaded tools
                    //this starts the counter at 48
                    //also gets the last 'tool'
                    [VarSet,count,[ToolGetCount]-47]
                    [VarSet,a, 47]
                    
                    //flag for if a object was imported
                    //or a new blank object needs to be made 
                    [VarSet, import,0]
                    
                    //shuts off interface update
                    [IFreeze,
                    
                    [Loop, #count,
                        //increment current tool
                        [VarSet, a, a+1]
                        
                        //select tool to look for matches
                        [ToolSelect, #a]
                        
                        //check for matching tool
                        //looks in the interface/UI
                        [VarSet, uiResult, [IExists,Tool:SubTool:#TOOLNAME]]
                       
                        [If, #uiResult == 1,

                            //iterate through sub tools
                            //even though the ui element exists
                            //it may not be visable 
                            [Loop,[SubToolGetCount],

                                //get currently selected tool name to compare
                                [VarSet,currentTool,[IgetTitle, Tool:Current Tool]]
                                [VarSet,subTool, [FileNameExtract, #currentTool, 2]]
                                [If,([StrLength,"#TOOLNAME"]==[StrLength,#subTool])&&([StrFind,#subTool,"#TOOLNAME"]>-1),
                                    //there was a match, import
                                    [VarSet,import,1]
                                    //stop looking
                                    [LoopExit]
                                ,]
                                //move through each sub tool to make it visable
                                [If,[IsEnabled,Tool:SubTool:SelectDown],
                                    [IPress, Tool:SubTool:SelectDown]
                                    ,[LoopExit]
                                ]
                            ]
                            //break out of parent loop if a tool is found
                            [If,#import==1,
                                [LoopExit]
                            ,
                            ]
                        ]
                    ]
                    ]
                    //check to see if imported or needs a new blank mesh

                    //might be redundant-check
                    [If, #import==0,
                    //make a blank PolyMesh3D
                    [ToolSelect, 41]
                    [IPress,Tool:Make PolyMesh3D]

                    ,]
                ]
                
                
                [RoutineDef, open_file,
                    //check if in edit mode
                    [VarSet, ui,[IExists,Tool:SubTool:All Low]]

                    //if no open tool make a new tool
                    // this could happen if there is no active mesh
                    [If, ui == 0,
                    [ToolSelect, 41]
                    [IPress,Tool:Make PolyMesh3D]
                    , 
                    ]

                    //find tool
                    [RoutineCall, findTool]
                    //lowest sub-d
                    [IPress, Tool:SubTool:All Low]
                    [FileNameSetNext,"!:#FILENAME"]
                    //finally import the tool
                    [IPress,Tool:Import]
                ]

                [RoutineCall,open_file]

                """


        # swap above zscript #'s with info from maya
        # then write to temp file
        zscript = zscript.replace(
            '#FILENAME', os.path.join(env, name))
        zscript = zscript.replace('#TOOLNAME', name.replace('.ma', ''))
        zscript = zscript.replace('#PARENT',parent)
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

    def __init__(self, host, port):
        self.host = host
        self.port = port

    @staticmethod
    def activate_zbrush():
        """ osascript -e 'tell app "ZBrush" to activate' """
        utils.open_osa()

    @staticmethod
    def zscript_ui():
        """ assembles a zscript to be loaded by ZBrush to create GUI buttons """

        # grab the current path of this file, make a temp file in the same
        # location
        script_path = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_path, 'zbrush_gui.txt')
        zs_temp = open(script_path, 'w+')

        # zscript to create the 'send' button
        zscript = """
        [RoutineDef, send_file,
            
            //check if in edit mode
            [VarSet, ui,[IExists,Tool:SubTool:All Low]]

            //if no open tool make a new tool
            [If, ui == 0,
            [ToolSelect, 41]
            [IPress,Tool:Make PolyMesh3D]
            ,]
            
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

            [VarSet, validpath,[FileExists, "!:/Volumes/public/goz_default/"]]

            [If, validpath != 1,


                //prevents zbrush crash from exporting to a invalid path
                //if zbrush exports to a bad path it will lock up
                [MessageOK, "Invalid ZDOCS file path for export"]
                [MessageOK, #export_path]
                [Exit]
                ,


            ]


            //finally export the tool
            [IPress,Tool:Export]

            //get base tool
            [SubToolSelect,0]
            [VarSet, base_tool, [SubToolGetID]]



            //trigger the python module to send maya the load commands
            [ShellExecute,
                //merge the python command with the tool name
                [StrMerge, #module_path,
                        #tool_name, " ",#base_tool
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

            //check if in edit mode
            [VarSet, ui,[IExists,Tool:SubTool:All Low]]

            //if no open tool make a new tool
            [If, ui == 0,
            [ToolSelect, 41]
            [IPress,Tool:Make PolyMesh3D]
            ,]

            //set all tools to lowest sub-d
            [IPress, Tool:SubTool:All Low]

            //iterator variable
            [VarSet,t,0]

            //start at the first subtool
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



                [VarSet, validpath,[FileExists, "!:/Volumes/public/goz_default/"]]

                [If, validpath != 1,


                    //prevents zbrush crash from exporting to a invalid path
                    //if zbrush exports to a bad path it will lock up
                    [MessageOK, "Invalid ZDOCS file path for export"]
                    [MessageOK, #export_path]
                    [Exit]
                    ,


                ]


                //finally export
                [IPress,Tool:Export]


                //get base tool
                [SubToolSelect,0]
                [VarSet, base_tool, [SubToolGetID]]

                [ShellExecute,
                    //join module_path tool_name for maya to load
                    [StrMerge, #module_path, #tool_name, " ",#base_tool]
                ]
            ]
        ]
        [IButton, "TOOL:Send to Maya -all", "Export model as a *.ma to maya",
            [RoutineCall, send_all]
        ]
        """
        env = os.getenv(utils.SHARED_DIR_ENV)
        print env

        zscript = zscript.replace('#ENVPATH', env)
        zs_temp.write(zscript)
        zs_temp.flush()
        zs_temp.close()

        utils.send_osa(script_path)

    def test_client(self):
        """ tests connection with maya, creates a sphere and deletes it """

        utils.validate_host(self.host)
        utils.validate_port(self.port)

        maya_cmd = 'import maya.cmds as cmds;'
        maya_cmd += 'cmds.sphere(name="goz_server_test;")'
        maya_cmd += 'cmds.delete("goz_server_test")'
        maya = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        maya.settimeout(5)
        try:
            maya.connect((self.host, int(self.port)))
        except socket.error as err:
            print err
            print 'connection refused'
            return False
        except ValueError:
            print 'specify a valid port'
            return False
        else:
            maya.send(maya_cmd)
            maya.close()
            return True

    @staticmethod
    def send(obj_name,parent_name):
        """ sends a file to maya"""
        print 'Parent tool: '+parent_name

        # construct file read path for maya, uses SHARED_DIR_ENV
        # make realative path
        file_path = utils.make_fp_rel(obj_name)

        print file_path


        # previous import was not looking inside of GoZ package
        maya_cmd = 'from GoZ import maya_tools;maya_tools.load("' + file_path+'","'+obj_name+'","'+parent_name +'")'

        print maya_cmd

        maya = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host, port = utils.get_net_info('MNET')

        print host, port

        maya.connect((host, int(port)))
        maya.send(maya_cmd)
        maya.close()


if __name__ == "__main__":
    import sys
    # send to maya/save from zbrush
    # arg 1: object name ie: pSphere1
    MayaClient.send(sys.argv[1],sys.argv[2])
