from pymel.core import window
from pymel.core import button
from pymel.core import rowColumnLayout
from pymel.core import text
from pymel.core import textField
from pymel.core import separator
from pymel.core import deleteUI
from pymel.core import confirmDialog
import maya_tools

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
        #new server/client, make gui, start server
        self.serv=maya_tools.MayaServer()
        self.client=maya_tools.ZBrushClient()

        self.build()
        self.buttons()
        #start MayaServer 
        self.listen()
        #check ZBrushClient connection to ZBrushServer
        with maya_tools.utils.err_handler(self.error_gui): 
            self.client.connect()

    def update_network(self):
        #sends host/port back to client/server
        
        self.client.host = self.user_zbrush_host.getText()
        self.client.port = self.user_zbrush_port.getText()

        self.serv.host = self.user_maya_host.getText()
        self.serv.port = self.user_maya_port.getText()
    
    def new_client_socket(self):

        #checks client host/port for new values
        #either creates or uses existing socket
        #note try to shorten this
        if (self.client.host == self.user_zbrush_host.getText() and
                self.client.port == self.user_zbrush_port.getText()):
            self.client.check_socket()
            return

        self.update_network()
        self.client.status = False
        self.client.sock = None
        with maya_tools.utils.err_handler(self.error_gui): 
            self.client.connect()

    def send(self,*args):

        self.new_client_socket()

        #construct list of selection, filter meshes
        #move functionality to maya_tools
        if self.client.parse_objs():
                #check for any GoZBrushIDs, and relink/create
                goz_result = self.client.goz_check()
                for obj in goz_result:
                        #clean this up
                        self.client.goz_id = obj[1]
                        self.client.goz_obj = obj[0]
                        self.rename_gui()
                with maya_tools.utils.err_handler(self.error_gui): 
                        self.client.send()
        else:
                self.error_gui('Please select a mesh to send')

    def listen(self,*args):
        #writes back host/port, starts listening
        self.update_network()
        self.serv.status=False

        with maya_tools.utils.err_handler(self.error_gui): 
            self.serv.start()

        #check if server is up, set gui accordingly
        if self.serv.status:
            self.status_ui.setBackgroundColor((0.0,1.0,0.5))
            self.status_ui.setLabel(
                    'Status: listening ('+self.serv.host+':'+str(self.serv.port)+')')
        else:
            self.status_ui.setBackgroundColor((1,0,0))
            self.status_ui.setLabel('Status: not listening')

    def rename_gui(self):
        #confirms object rename, triggers create or relink then revises obj list
        c = confirmDialog(title="ZBrush Name Conflict",
                message="%s has a old ZBrush ID, of %s, try to relink?" 
                % (self.client.goz_obj,self.client.goz_id),
                button=['Relink','Create'])
        if 'Relink' in c:
            #relink to past GoZBrushID
            self.client.relink()
            self.client.parse_objs()
        if 'Create' in c:
            #new object for zbrush
            self.client.create()
            self.client.parse_objs()
            print 'time make a new one'

    def error_gui(self,message):
        """ simple gui for displaying errors """
        confirmDialog(title=str('GoZ Error:'),message= '\n'+str(message),button=['Ok'])

    def build(self):
        if window('goz', exists=True):
            deleteUI('goz',window=True)

        self.gui_window = window('goz',title="send to zbrush")
        layout = rowColumnLayout(
            numberOfColumns=3,
            columnAttach=(1,'right',0),
            columnWidth=[(1,100),(2,240),(3,60)])
        text(label='ZBrush IP')
        self.user_zbrush_host = textField(text=self.client.host)
        self.spacer(1)
        text(label='ZBrush PORT')
        self.user_zbrush_port=textField(text=self.client.port)
        self.spacer(2)
        self.send_btn = button(label="Send Meshes to ZBrush", parent=layout)
        self.spacer(2)
        separator(style='double',height=30)
        self.spacer(1)
        text(label='Maya IP')
        self.user_maya_host = textField(text=self.serv.host)
        self.spacer(1)
        text(label='Maya PORT')
        self.user_maya_port=textField(text=self.serv.port)
        self.spacer(2)
        self.listen_btn = button(label="Listen for Meshes from ZBrush", parent=layout)
        self.spacer(2)
        self.status_ui=text(label='Status: not listening',
            height=30,
            enableBackground=True,
            backgroundColor=(1.0,0.0,0.0))
        self.spacer(1) 
        self.gui_window.show()

    def buttons(self):
        self.send_btn.setCommand(self.send)
        self.listen_btn.setCommand(self.listen)

    def spacer(self,num):
        for i in range(0,num):
            separator(style='none')
