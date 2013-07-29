from pymel.core import window
from pymel.core import button
from pymel.core import rowColumnLayout
from pymel.core import text
from pymel.core import textField
from pymel.core import separator
from pymel.core import deleteUI
#from pymel.core import confirmDialog
import maya_tools

class Win(object):

    """
    
    GUI for maya_tools
    
    attributes:
        self.serv            -- MayaServer instance
        self.client          -- ZBrushClient instance
        
    methods:
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
    """

    def __init__(self):

        self.serv=maya_tools.MayaServer()
        self.client=maya_tools.ZBrushClient()

        self.build()
        self.buttons()

        self.listen()

    def send(self,*args):
        self.client.host = self.user_zbrush_ip.getText()
        self.client.port = self.user_zbrush_port.getText()
        self.client.send()
        print 'send'

    def listen(self,*args):

        self.serv.host = self.user_maya_ip.getText()
        self.serv.port = self.user_maya_port.getText()
        self.serv.start()

        if self.serv.status:
            self.status_ui.setBackgroundColor((0.0,1.0,0.5))
            self.status_ui.setLabel(
                    'Status: listening ('+self.serv.host+':'+str(self.serv.port)+')')
        else:
            self.status_ui.setBackgroundColor((1,0,0))
            self.status_ui.setLabel(
                    'Status: not listening')


    def build(self):
        if window('goz', exists=True):
            deleteUI('goz',window=True)

        self.gui_window = window('goz',title="send to zbrush")
        layout = rowColumnLayout(
            numberOfColumns=3,
            columnAttach=(1,'right',0),
            columnWidth=[(1,100),(2,240),(3,60)])
        text(label='ZBrush IP')
        self.user_zbrush_ip = textField(text=self.client.host)
        self.spacer(1)
        text(label='ZBrush PORT')
        self.user_zbrush_port=textField(text=self.client.port)
        self.spacer(2)
        self.send_btn = button(label="Send Meshes to ZBrush", parent=layout)
        self.spacer(2)
        separator(style='double',height=30)
        self.spacer(1)
        text(label='Maya IP')
        self.user_maya_ip = textField(text=self.serv.host)
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
