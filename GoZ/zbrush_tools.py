#!/usr/bin/python

import SocketServer
import utils

class ZBrushServer(object):

    """
    
    ZBrush server extending SocketServer module, gets meshes from maya
    
    attributes:
        self.status                    -- current server status (up/down)
        self.host                      -- current host for serving on from utils.getenvs
        self.port                      -- current port for serving on from utils.getenvs
        self.shared_dir                -- shared ZBrush/Maya directory from utils.getenvs
        self.cmdport_name              -- formated command port name

    methods:
        start()              -- start the server 
        stop()               -- stop the server

    class:
        ZBrushSocketServ     -- configures daemon mode for socketserv module
        ZBrushHandler        -- handles loading objects from maya

    """

    def __init__(self):

        self.host,self.port,self.shared_dir = utils.getenvs(zbrush=True,serv=True,shared_dir=True)
   
    def start(self):

        utils.writecfg(self.host,self.port,'ZNET')

        try:
                self.server.shutdown()
                self.server.server_close()
                print 'killing previous server...'
        except AttributeError:
                print 'starting a new server!'

        self.server = self.ZBrushSocketServ((self.host,int(self.port)),self.ZBrushHandler)
        self.server.allow_reuse_address=True
        self.server_thread = utils.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        print 'Serving on %s:%s'% (self.host,self.port)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        print 'stoping...'

    class ZBrushSocketServ(SocketServer.ThreadingMixIn,SocketServer.TCPServer):

        timeout = 5
        daemon_threads=True
        allow_reuse_address=True

        def __init__(self,server_address,RequestHandlerClass):
            SocketServer.TCPServer.__init__(
                        self,
                        server_address,
                        RequestHandlerClass)

        def handle_timeout(self):
            print 'TIMEOUT'


    class ZBrushHandler(SocketServer.BaseRequestHandler):


        timeout = 5


        def handle(self):
            while 1:
                try:

                    self.data = self.request.recv(1024).strip()
                    if not self.data:
                        self.request.close()
                        break
                    print '\n\n'
                    print '{} sent:'.format(self.client_address[0])
                    print self.data

                    if self.data.split('|')[0] == 'open':
                        objs = self.data.split('|')[1].split(':')
                        for obj in objs:
                            print 'got: '+obj
                            zs_temp = self.zbrush_open(obj+'.ma')
                            utils.send_osa(zs_temp)
                        print 'loaded all objs!'
                        self.request.send('loaded')
                except KeyboardInterrupt:
                    self.request.close()
                    break

        def zbrush_open(self,name):

            """open a file with zbrush
            -create temp zscript file
            -load with file open commands
            -replace #TOOLNAME/#FILENAME with maya path/filename
            -iterate through current subtools to check for 'matches'
            -import if match, append new cloned tool for unique tools

            """
            script_path=utils.os.path.dirname(utils.os.path.abspath(__file__))
            script_path=utils.os.path.join(script_path,'zbrush_load.txt')
            zs_temp = open(script_path,'w+')


            # this should be inherited - didnt see a straight forward way to do it
            self.shared_dir = utils.getenvs(shared_dir=True)[0]
            env = utils.os.getenv(self.shared_dir.replace('$',''))
            print env

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

            zscript = zscript.replace('#FILENAME',utils.os.path.join(env, name))
            zscript = zscript.replace('#TOOLNAME',name.replace('.ma',''))
            zs_temp.write(zscript)
            return zs_temp.name 


class MayaClient(object):

    def __init__(self):
        self.host,self.port,self.shared_dir = utils.getenvs(maya=True,shared_dir=True) 

    def zscript_ui(self):

        script_path=utils.os.path.dirname(utils.os.path.abspath(__file__))
        script_path=utils.os.path.join(script_path,'zbrush_gui.txt')
        zs_temp = open(script_path,'w+')
        
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

        env = utils.os.getenv(self.shared_dir.replace('$',''))
        print env

        zscript=zscript.replace('#ENVPATH',env)
        zs_temp.write(zscript)
        zs_temp.flush()
        zs_temp.close()
        
        utils.send_osa(script_path)

    def test_client(self):
        
        utils.writecfg(self.host,self.port,'MNET')

        mayaCMD = 'import maya.cmds as cmds'
        mayaCMD += '\n'
        mayaCMD += 'cmds.sphere(name="test")'
        mayaCMD += '\n'
        mayaCMD += 'cmds.delete("test")'
        maya = utils.socket.socket(utils.socket.AF_INET, utils.socket.SOCK_STREAM)
        try:
            maya.connect((self.host, int(self.port)))
        except utils.socket.error,e:
            print e
            print 'connection refused'
            return False
        else:
            maya.send(mayaCMD)
            maya.close()
            return True

    @staticmethod
    def send():

        shared_dir = '$'+utils.getenvs(shared_dir=True)

        file = (utils.sys.argv)[1]
        file_path = utils.os.path.join(shared_dir, file + '.ma')

        mayaCMD = 'import __main__'
        mayaCMD += '\n'
        mayaCMD += '__main__.mayagui.serv.load("'+file_path+'")'

        maya = utils.socket.socket(utils.socket.AF_INET, utils.socket.SOCK_STREAM)
 
        host,port = utils.getenvs(maya=True) 

        maya.connect((host, int(port)))
        maya.send(mayaCMD)
        maya.close()


if __name__ == "__main__":

    """send to maya/save from zbrush
    -arg 1: object name ie: pSphere1
    """
    MayaClient.send()
