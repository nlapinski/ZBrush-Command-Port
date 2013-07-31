"""ZBrushGUI uses zbrushtools, starts ZBrushServer and MayaClient """

from . import zbrush_tools
import Tkinter


class ZBrushGUI(object):

    """

    GUI for zbrush_tools

    attributes:
        self.serv            -- ZBrushServer instance
        self.client          -- MayaClient instance
                             -- both inherit host/port attr
    methods:
        build                -- construct gui for zbrush_tools
        serv_start           -- start a ZBrush command port with ZBrushServer.start()
        test_client          -- create a connection to maya with MayaClient.connect()
        zscript_ui           -- attaches two zbrush gui elements (makes a zscript from env vars)

    """

    def __init__(self):

        self.serv = zbrush_tools.ZBrushServer()
        self.client = zbrush_tools.MayaClient()
        self.maya_status_ui = None
        self.maya_host_ui = None
        self.zbrush_port_ui = None
        self.maya_port_ui = None
        self.zbrush_status_ui = None
        self.win = None
        self.zbrush_host_ui = None

        self.build()
        self.serv_start()
        self.test_client()
        self.zscript_ui()
        self.win.mainloop()

    def serv_start(self):
        """start sever command """

        self.serv.host = self.zbrush_host_ui.get()
        self.serv.port = self.zbrush_port_ui.get()

        self.serv.start()

        status_line = 'ZBrushServer Status: %s:%s' % (
            self.serv.host, self.serv.port)

        self.zbrush_status_ui.config(text=status_line, background='green')

    def serv_stop(self):
        """stop server command """

        self.serv.stop()
        self.zbrush_status_ui.config(
            text='ZBrushServer Status: down',
            background='red')

    def zscript_ui(self):
        """install UI in ZBrush """

        print 'make zbrush ui'
        self.client.zscript_ui()

    def test_client(self):
        """tests conn to MayaSever """

        self.client.host = self.maya_host_ui.get()
        self.client.port = self.maya_port_ui.get()

        if self.client.test_client():
            print 'connected to maya'
            self.maya_status_ui.config(
                text='MayaClient Status: connected',
                background='green')
        else:
            self.maya_status_ui.config(
                text='MayaClient Status: conn refused',
                background='red')

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
            text='Set hosts/ports in default.cfg').pack(
                pady=0,
                padx=25)
        Tkinter.Label(
            self.win,
            text='If not set starts in local mode').pack(
                pady=0,
                padx=25)
        Tkinter.Label(
            self.win,
            text='ZBrush should be launched first').pack(
                pady=0,
                padx=25)
        Tkinter.Label(
            self.win,
            text='Everything should be automatic').pack(
                pady=0,
                padx=25)
        Tkinter.Label(
            self.win,
            text='Changes are added to default.cfg').pack(
                pady=0,
                padx=25)

        zb_cfg = Tkinter.LabelFrame(self.win, text="ZBrush Server")
        zb_cfg.pack(pady=15, fill="both", expand="yes")

        Tkinter.Label(zb_cfg, text='ZBrush Host:').pack(pady=5, padx=5)
        self.zbrush_host_ui = Tkinter.Entry(zb_cfg, width=15)
        self.zbrush_host_ui.pack()
        self.zbrush_host_ui.insert(0, self.serv.host)
        Tkinter.Label(zb_cfg, text='ZBrush Port:').pack(pady=5, padx=5)
        self.zbrush_port_ui = Tkinter.Entry(zb_cfg, width=15)
        self.zbrush_port_ui.pack()
        self.zbrush_port_ui.insert(0, self.serv.port)

        Tkinter.Button(
            zb_cfg,
            text='Start ZBrushServer',
            command=self.serv_start).pack(
            )
        Tkinter.Button(
            zb_cfg,
            text='Stop ZBrushServer',
            command=self.serv_stop).pack(
            )

        self.zbrush_status_ui = Tkinter.Label(
            zb_cfg,
            text='ZBrushServer Status: down',
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
            command=self.test_client).pack(
            )
        self.maya_status_ui = Tkinter.Label(
            maya_cfg,
            text='MayaClient Status: conn refused',
            background='red')
        self.maya_status_ui.pack(pady=5, padx=5)
