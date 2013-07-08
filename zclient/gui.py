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

class win(): 

    def build(self):
        
        print "window init"

        znet = os.environ.get('ZNET')
        mnet = os.environ.get('MNET')
  

        try:
            #try to use env vars
            self.z_port = znet.split(':')[1]
            self.z_ip = znet.split(':')[0]

            self.m_port = mnet.split(':')[1]
            self.m_ip = mnet.split(':')[0]

        except:
            #fall back to defaults
            self.z_port = 6668
            self.z_ip = '192.168.1.17'
            self.m_port = 6667
            self.m_ip = '192.168.1.20'

        self.m_port_new=self.m_port
        self.m_ip_new=self.m_ip

        self.z_port_new=self.z_port
        self.z_ip_new=self.z_ip

        if window('goz', exists=True):
            deleteUI('goz',window=True)
        
        self.gui_window = window('goz',title="send to zbrush")
        layout = rowColumnLayout(
            numberOfColumns=3,
            columnAttach=(1,'right',0),
            columnWidth=[(1,100),(2,240),(3,60)])
        label_z_ip=text(label='ZBrush IP')
        self.user_z_ip = textField(text=self.z_ip)
        self.spacer(1)
        label_z_port=text(label='ZBrush PORT')
        self.user_z_port=textField(text=self.z_port)
        self.spacer(2)
        self.send = button(label="Send", parent=layout)
        self.spacer(2)
        space = separator(style='double',height=30)
        self.spacer(1)
        label_m_ip=text(label='Maya IP')
        self.user_m_ip = textField(text=self.m_ip)
        self.spacer(1)
        label_m_port=text(label='Maya PORT')
        self.user_m_port=textField(text=self.m_port)
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
        self.m_ip_new=self.user_m_ip.getText()
        self.m_port_new=self.user_m_port.getText()
        #store user defined IP/Port incase window is closed
        os.environ['MNET']= self.m_ip_new+':'+self.m_port_new

    def get_ui_z(self, *args):
        self.z_ip_new=self.user_z_ip.getText()
        self.z_port_new=self.user_z_port.getText()
        #store user defined IP/Port incase window is closed
        os.environ['ZNET']=self.z_ip_new+':'+self.z_port_new


    def __init__(self):
        self.build()
        self.start_listening()
        self.send.setCommand(self.execute)
        self.listen.setCommand(self.start_listening)
        
        self.gui_window.show()

    def show(self):
        self.gui_window.show()

    def start_listening(self, *args):

        self.get_ui_m()

        main.stop(self.m_ip,self.m_port)
        self.m_ip=self.m_ip_new
        self.m_port=self.m_port_new

        status = main.start(self.m_ip,self.m_port)
        
        self.status.setBackgroundColor((1,0,.5))
        self.status.setLabel(
                'Status: not listening')

        if status:
            self.status.setBackgroundColor((0.0,1.0,0.5))
            self.status.setLabel(
                    'Status: listening ('+self.m_ip+':'+str(self.m_port)+')')

    def execute(self, *args):
        self.get_ui_z()
        self.z_ip=self.z_ip_new
        self.z_port=self.z_port_new
        main.send_to_zbrush(self.z_ip,self.z_port)
        self.gui_window.setVisible(False)

    def execute_shelf(self, *args):
        main.send_to_zbrush(self.z_ip,self.z_port)

