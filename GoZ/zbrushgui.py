"""ZBrushGUI uses zbrushtools, starts ZBrushServer and MayaClient """

from GoZ import zbrush_tools as zbrush_tools
import Tkinter
import tkMessageBox
import GoZ.utils as utils

class ZBrushGUI(object):

    """

    GUI for zbrush_tools

    build a UI using Tkinter, gets network info from utils.get_net_info
    starts ZBrushServer and MayaClient from zbrush_tools

    Also installs a zscript GUI in ZBrush using zbrush_tools.zscript_ui

    attributes:
        self.serv             -- ZBrushServer instance
        self.client           -- MayaClient instance

        self.maya_status_ui   -- status lines
        self.zbrush_status_ui --
      
        self.maya_host_ui     -- maya host
        self.maya_port_ui     -- maya port

        self.zbrush_port_ui   -- zbrush port

    """

    def __init__(self):
        zhost, zport = utils.get_net_info('ZNET')
        mhost, mport = utils.get_net_info('MNET')
        
        self.serv = zbrush_tools.ZBrushServer(zhost, zport)
        self.client = zbrush_tools.MayaClient(mhost, mport)
        
        self.maya_status_ui = None
        self.maya_host_ui = None
        self.maya_port_ui = None

        self.zbrush_port_ui = None 
        self.zbrush_status_ui = None
        self.win = None

        self.build()
        self.serv_start()
        self.test_client()
        self.zscript_ui()
        self.win.mainloop()

    def serv_start(self):
        """
        starts sever

        gets network info from UI (port)

        sets status line
        """ 
        self.serv.port = self.zbrush_port_ui.get()

        with zbrush_tools.utils.err_handler(self.error_gui):
            self.serv.start()

        if self.serv.status:
            status_line = 'ZBrush Server Status: %s:%s' % (
                self.serv.host, self.serv.port)

            self.zbrush_status_ui.config(text=status_line, background='green')
        else:
            self.zbrush_status_ui.config(
                text='ZBrush Server Status: down',
                background='red')

    def serv_stop(self):
        """
        stops server

        sets status line 
        
        """

        self.serv.stop()
        self.zbrush_status_ui.config(
            text='ZBrush Server Status: down',
            background='red')

    def zscript_ui(self):
        """install UI in ZBrush """

        self.client.activate_zbrush()
        self.client.zscript_ui()

    def test_client(self):
        """tests conn to MayaSever """

        self.client.host = self.maya_host_ui.get()
        self.client.port = self.maya_port_ui.get()

        self.maya_status_ui.config(
            text='MayaClient Status: conn refused',
            background='red')

        with zbrush_tools.utils.err_handler(self.error_gui):
            ret = self.client.test_client()

        if ret:
            print 'connected to maya'
            self.maya_status_ui.config(
                text='MayaClient Status: connected',
                background='green')

    def build(self):
        """Creates tkinter UI """
        self.win = Tkinter.Tk()
        self.win.title('GoZ GUI')
        Tkinter.Label(
            self.win,
            text='GoZ - Basic Setup:').pack(
                pady=5,
                padx=25)

        Tkinter.Label(
            self.win,
            text='Set MNET/ZNET/ZDOCS envs').pack(
                pady=0,
                padx=25)
        Tkinter.Label(
            self.win,
            text='like: ZNET=127.0.0.1:6668').pack(
                pady=0,
                padx=25)
        Tkinter.Label(
            self.win,
            text='set ZDOCS to your network path').pack(
                pady=0,
                padx=25)

        zb_cfg = Tkinter.LabelFrame(self.win, text="ZBrush Server")
        zb_cfg.pack(pady=15, fill="both", expand="yes")

        Tkinter.Label(zb_cfg, text='ZBrush Port:').pack(pady=5, padx=5)
        self.zbrush_port_ui = Tkinter.Entry(zb_cfg, width=15)
        self.zbrush_port_ui.pack()
        self.zbrush_port_ui.insert(0, self.serv.port)

        Tkinter.Button(
            zb_cfg,
            text='Start',
            command=self.serv_start).pack()
        Tkinter.Button(
            zb_cfg,
            text='Stop',
            command=self.serv_stop).pack()

        self.zbrush_status_ui = Tkinter.Label(
            zb_cfg,
            text='ZBrush Server Status: down',
            background='red')
        self.zbrush_status_ui.pack(pady=5, padx=5)

        maya_cfg = Tkinter.LabelFrame(self.win, text="Maya Client")
        maya_cfg.pack(pady=15, fill="both", expand="yes")

        Tkinter.Label(maya_cfg, text='Maya Host:').pack(pady=5, padx=5)
        self.maya_host_ui = Tkinter.Entry(maya_cfg, width=15)
        self.maya_host_ui.insert(0, self.client.host)
        self.maya_host_ui.pack()

        Tkinter.Label(maya_cfg, text='Maya Port:').pack(pady=5, padx=5)
        self.maya_port_ui = Tkinter.Entry(maya_cfg, width=15)
        self.maya_port_ui.insert(0, self.client.port)
        self.maya_port_ui.pack()

        Tkinter.Button(
            maya_cfg,
            text='Make ZBrush UI',
            command=self.zscript_ui).pack()
        Tkinter.Button(
            maya_cfg,
            text='Test Connection',
            command=self.test_client).pack()
        self.maya_status_ui = Tkinter.Label(
            maya_cfg,
            text='Maya Client Status: conn refused',
            background='red')
        self.maya_status_ui.pack(pady=5, padx=5)

    @staticmethod
    def error_gui(message):
        """simple tkinter gui for displaying errors"""
        tkMessageBox.showwarning('GoZ Error:', message)
