"""Classes to creat a gui within maya uses maya_tools """

from pymel.core import window
from pymel.core import button
from pymel.core import rowColumnLayout
from pymel.core import text
from pymel.core import textField
from pymel.core import separator
from pymel.core import deleteUI
from pymel.core import confirmDialog
from GoZ import maya_tools as maya_tools


class Win(object):

    """

    GUI for maya_tools

    attributes:
        self.serv            -- MayaServer instance
        self.client          -- ZBrushClient instance

    methods:

        __init__             -- start Server/Client, make UI
        build                -- construct gui for maya_tools
        spacer               -- add some pymel spacers
        get_maya_settings    -- get settings from gui
        get_zbrush_settings  -- ''                         ''
        show                 -- bring gui to front

        listen               -- start a maya command port with MayaServer.start()
        connect              -- create a connection to zbrush with ZBrushClient.connect()
        send                 -- sends to zbrush with ZBrushClient.send()
        zbrush_gozid         -- present dialog box for ZBrushClient.relink()/create()
        shelf_send           -- send to zbrush with ZBrushClient.send()
        rename_gui           -- dialouge for rename/relink goz_id
        update_network          -- set host/port in client/server
    """

    def __init__(self):
        """ new server/client, make gui, start server """

        self.serv = maya_tools.MayaServer()
        self.client = maya_tools.ZBrushClient()
        self.gui_window = None
        self.send_btn = None
        self.user_zbrush_host = None
        self.user_zbrush_port = None
        self.listen_btn = None
        self.user_maya_port = None
        self.maya_status_ui = None
        self.conn_btn = None
        self.zbrush_status_gui = None

        # make the gui
        self.build()
        self.buttons()
        # start MayaServer
        self.listen()
        # check ZBrushClient connection to ZBrushServer
        self.connect()

        self.client.check_socket()
        self.check_status_ui()

    def update_network(self):
        """ sends host/port back to client/server """

        self.client.host = self.user_zbrush_host.getText()
        self.client.port = self.user_zbrush_port.getText()

        self.serv.port = self.user_maya_port.getText()

    def connect(self, *args):
        """ connects to ZBrushServer using maya_tools"""
        print args

        self.update_network()
        with maya_tools.utils.err_handler(self.error_gui):
            self.client.connect()
        self.check_status_ui()

    def check_status_ui(self):
        """ updates statuslines, connected/disconnected for zbrush """
        # check if client is connected, set gui accordingly
        if self.client.status:
            self.zbrush_status_ui.setBackgroundColor((0.0, 1.0, 0.5))
            self.zbrush_status_ui.setLabel(
                'Status: connected (' +
                self.client.host + ':' +
                str(self.client.port) + ')')
        else:
            self.zbrush_status_ui.setBackgroundColor((1, 0, 0))
            self.zbrush_status_ui.setLabel('Status: not connected')

    def send(self, *args):
        """ send to zbrush """

        self.client.check_socket()
        try:
            self.check_status_ui()
        except:
            pass

        if self.client.status is False:
            # try last socket, or fail
            with maya_tools.utils.err_handler(self.error_gui):
                self.client.connect()
            self.check_status_ui()

        # construct list of selection, filter meshes
        if self.client.parse_objs():
            # check for any GoZBrushIDs, and relink/create
            for obj, goz_id in self.client.get_gozid_mismatches():
                # relinked objs are removed from self.client.objs
                # this prevents relinking 2 previous tool histories
                # it stops relinking after the 1st match/relink
                # so pSphere1 contains both meshes, but pSphere2 still exists
                # this prevents overwriting 2 zbrush tools with the same obj

                # the 'skip' option during in the relink gui keeps the obj to look
                # for an alternative history, for example relink the 2nd obj history
                # if skip fails to relink, it will default to 'create'

                if obj in self.client.objs:
                    self.client.goz_id = goz_id
                    self.client.goz_obj = obj
                    self.rename_gui()
            with maya_tools.utils.err_handler(self.error_gui):
                self.client.send()
        else:
            self.error_gui('Please select a mesh to send')

    def listen(self, *args):
        """  writes back host/port, starts listening """

        print args

        self.update_network()
        self.serv.status = False

        with maya_tools.utils.err_handler(self.error_gui):
            self.serv.start()

        # check if server is up, set gui accordingly
        if self.serv.status:
            self.maya_status_ui.setBackgroundColor((0.0, 1.0, 0.5))
            self.maya_status_ui.setLabel(
                'Status: listening (' +
                self.serv.host + ':' +
                str(self.serv.port) + ')')
        else:
            self.maya_status_ui.setBackgroundColor((1, 0, 0))
            self.maya_status_ui.setLabel('Status: not listening')

    def rename_gui(self):
        """
        confirms object rename,
        triggers create or relink
        then revises objlist
        """
        gui_message = """%s has a old ZBrush ID, of %s, try to relink?

                        NOTE! relinking will 
                        remove objects named "%s"
                        selected mesh as the new one!!
                        """ % (self.client.goz_obj, self.client.goz_id,self.client.goz_id)

        choice = confirmDialog(title="ZBrush Name Conflict",
                               message=gui_message,
                               button=['Relink', 'Create', 'Skip'])
        if 'Relink' in choice:
            # relink to past GoZBrushID
            self.client.relink()
            #remove any corrected IDs from list
            self.client.parse_objs()
        if 'Create' in choice:
            # new object for zbrush
            self.client.create()
            #remove any corrected IDs from list
            self.client.parse_objs()
            print 'time make a new one'

    def build(self):
        """ constructs gui """
        if window('goz', exists=True):
            deleteUI('goz', window=True)

        self.gui_window = window('goz', title="send to zbrush")
        layout = rowColumnLayout(
            numberOfColumns=3,
            columnAttach=(1, 'right', 0),
            columnWidth=[(1, 100), (2, 240), (3, 60)])
        text(label='ZBrush IP')
        self.user_zbrush_host = textField(text=self.client.host)
        self.spacer(1)
        text(label='ZBrush PORT')
        self.user_zbrush_port = textField(text=self.client.port)
        self.spacer(2)
        self.send_btn = button(label="Send Meshes to ZBrush", parent=layout)
        self.spacer(2)
        self.conn_btn = button(label="Connect to ZBrush", parent=layout)
        self.spacer(2)
        self.zbrush_status_ui = text(label='Status: not connected',
                                     height=30,
                                     enableBackground=True,
                                     backgroundColor=(1.0, 0.0, 0.0))
        self.spacer(2)
        separator(style='double', height=30)
        self.spacer(1)
        text(label='Maya PORT')
        self.user_maya_port = textField(text=self.serv.port)
        self.spacer(2)
        self.listen_btn = button(
            label="Listen for Meshes from ZBrush",
            parent=layout)
        self.spacer(2)
        self.maya_status_ui = text(label='Status: not listening',
                                   height=30,
                                   enableBackground=True,
                                   backgroundColor=(1.0, 0.0, 0.0))
        self.spacer(1)
        self.gui_window.show()

    def buttons(self):
        """ attaches methods to callbacks """
        self.send_btn.setCommand(self.send)
        self.conn_btn.setCommand(self.connect)
        self.listen_btn.setCommand(self.listen)

    @staticmethod
    def error_gui(message):
        """ simple gui for displaying errors """
        confirmDialog(
            title=str('GoZ Error:'),
            message='\n' + str(message),
            button=['Ok'])

    @staticmethod
    def spacer(num):
        """ creates a spacer """
        for _ in range(0, num):
            separator(style='none')
