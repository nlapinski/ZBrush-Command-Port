from pymel.core import window
from pymel.core import button
from pymel.core import rowColumnLayout
from pymel.core import text
from pymel.core import textField
from pymel.core import separator
from pymel.core import loadPlugin
from pymel.core import selected
from pymel.core import deleteUI
import os

from zclient import main

"""a simple ui for executing commands in zclient.main
also handles reading enviromental variables for network config
"""


class Win(): 

    def build(self):
        
        print "window init"

        znet = os.environ.get('ZNET')
        mnet = os.environ.get('MNET')
  

        try:
            #try to use env vars
            self.zbrush_port = znet.split(':')[1]
            self.zbrush_ip = znet.split(':')[0]

            self.maya_port = mnet.split(':')[1]
            self.maya_ip = mnet.split(':')[0]
            print 'using env vars'

        except:
            #fall back to defaults
            self.zbrush_port = 6668
            self.zbrush_ip = '192.168.1.17'
            #maya defaults
            self.maya_port = 6667
            self.maya_ip = 'localhost'
            print 'using defaults'

        self.maya_port_new=self.maya_port
        self.maya_ip_new=self.maya_ip

        self.zbrush_port_new=self.zbrush_port
        self.zbrush_ip_new=self.zbrush_ip

        if window('goz', exists=True):
            deleteUI('goz',window=True)
        
        self.gui_window = window('goz',title="send to zbrush")
        layout = rowColumnLayout(
            numberOfColumns=3,
            columnAttach=(1,'right',0),
            columnWidth=[(1,100),(2,240),(3,60)])
        label_zbrush_ip=text(label='ZBrush IP')
        self.user_zbrush_ip = textField(text=self.zbrush_ip)
        self.spacer(1)
        label_zbrush_port=text(label='ZBrush PORT')
        self.user_zbrush_port=textField(text=self.zbrush_port)
        self.spacer(2)
        self.send = button(label="Send", parent=layout)
        self.spacer(2)
        space = separator(style='double',height=30)
        self.spacer(1)
        label_maya_ip=text(label='Maya IP')
        self.user_maya_ip = textField(text=self.maya_ip)
        self.spacer(1)
        label_maya_port=text(label='Maya PORT')
        self.user_maya_port=textField(text=self.maya_port)
        self.spacer(2)
        self.listen = button(label="Listen (cmd port)", parent=layout)
        self.spacer(2)
        self.status=text(label='Status: not listening',
            height=30,
            enableBackground=True,
            backgroundColor=(1.0,0.0,0.0))
        self.spacer(1)

    def spacer(self,num):
        for i in range(0,num):
            space=separator(style='none')

    def get_ui_m(self, *args):
        self.maya_ip_new=self.user_maya_ip.getText()
        self.maya_port_new=self.user_maya_port.getText()
        #store user defined IP/Port incase window is closed
        os.environ['MNET']= self.maya_ip_new+':'+self.maya_port_new

    def get_ui_z(self, *args):
        self.zbrush_ip_new=self.user_zbrush_ip.getText()
        self.zbrush_port_new=self.user_zbrush_port.getText()
        #store user defined IP/Port incase window is closed
        os.environ['ZNET']=self.zbrush_ip_new+':'+self.zbrush_port_new


    def __init__(self):
        self.build()
        self.start_listening()
        self.send.setCommand(self.execute)
        self.listen.setCommand(self.start_listening)
        
        self.gui_window.show()

    def show(self):
        self.gui_window.show()

    def start_listening(self, *args):
        """open maya command port using .main.start()"""
        self.get_ui_m()

        main.stop(self.maya_ip,self.maya_port)
        self.maya_ip=self.maya_ip_new
        self.maya_port=self.maya_port_new

        status = main.start(self.maya_ip,self.maya_port)
        
        self.status.setBackgroundColor((1,0,.5))
        self.status.setLabel(
                'Status: not listening')

        if status:
            self.status.setBackgroundColor((0.0,1.0,0.5))
            self.status.setLabel(
                    'Status: listening ('+self.maya_ip+':'+str(self.maya_port)+')')

    def execute(self, *args):
        self.get_ui_z()
        self.zbrush_ip=self.zbrush_ip_new
        self.zbrush_port=self.zbrush_port_new
        main.send_to_zbrush(self.zbrush_ip,self.zbrush_port)
        self.gui_window.setVisible(False)

    def execute_shelf(self, *args):
        """used for shelf send (so you dont need the gui all the time): """
        main.send_to_zbrush(self.zbrush_ip,self.zbrush_port)

