"""
a simple ui for executing commands in zclient.main
also handles reading enviromental variables for network config
"""

from pymel.core import window
from pymel.core import button
from pymel.core import rowColumnLayout
from pymel.core import text
from pymel.core import textField
from pymel.core import separator
from pymel.core import loadPlugin
from pymel.core import selected
from pymel.core import deleteUI
from pymel.core import confirmDialog
import socket
import os

from zclient import main

#does this return the current host name?
EMTPY_VALUE = '<type workstation name>'

class Win(object): 

    def __init__(self):
        self.build()
        self.start_listening()
        self.send.setCommand(self.execute)
        self.listen.setCommand(self.start_listening)
        
        self.gui_window.show()

    def build(self):
        """
        constructs a gui using pymel

        also attemps to resolve ZNET (host:port) of zbrush

        also attemps to to resolve MNET (host:port) this is the 
        host and port for maya to listen on

        if MNET is not defined defaults back to using python socket methods to find 
        external IP, if no host can be resolved returns error

        socket.getfqdn should work most of the time, however if /etc/hosts 
        redirects to local host a error is raised

        parsing of ifconfig output could prevent this
        """
        
        print "window init"

        znet = os.environ.get('ZNET')
        if znet:
            self.zbrush_ip, self.zbrush_port = znet.split(':')
        else:
            self.zbrush_port = 6668
            self.zbrush_ip = EMTPY_VALUE

        mnet = os.environ.get('MNET')
        if mnet:
            self.maya_ip, self.maya_port = mnet.split(':')
        else:
            self.maya_port = 6667
            #may resolve to localhost, or 127.0.0.1, this will raise an error
            external_ip = socket.gethostbyname(socket.getfqdn())
            if external_ip == '127.0.0.1':
                print 'ip err'
                print 'could not resolve external IP'
                print 'defaulting to IP/HOST from  MNET or gui'
                error_gui('Could no resolve external IP')
            else:
                self.maya_ip = external_ip
                print 'resolved local ip'

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
        self.send = button(label="Send Meshes to ZBrush", parent=layout)
        self.spacer(2)
        space = separator(style='double',height=30)
        self.spacer(1)
        label_maya_ip=text(label='Maya IP')
        self.user_maya_ip = textField(text=self.maya_ip)
        self.spacer(1)
        label_maya_port=text(label='Maya PORT')
        self.user_maya_port=textField(text=self.maya_port)
        self.spacer(2)
        self.listen = button(label="Listen for Meshes from ZBrush", parent=layout)
        self.spacer(2)
        self.status=text(label='Status: not listening',
            height=30,
            enableBackground=True,
            backgroundColor=(1.0,0.0,0.0))
        self.spacer(1)

    def spacer(self,num):
        for i in range(0,num):
            space=separator(style='none')

    def validate_ip(self,ip_addr):
        return socket.inet_aton(ip_addr)

    def get_maya_settings(self, *args):
        maya_ip = self.user_maya_ip.getText()
        maya_ip = socket.gethostbyname(maya_ip)
        try:
            self.validate_ip(maya_ip)
        except socket.error:
            return socket.error
        else:
            maya_port = self.user_maya_port.getText()
            #store user defined IP/Port incase window is closed
            os.environ['MNET'] = maya_ip+':'+maya_port
            return maya_ip, maya_port

    def get_zbrush_settings(self, *args):
        zbrush_ip = self.user_zbrush_ip.getText()
        try:
            self.validate_ip(zbrush_ip)
        except socket.error:
            #bring up an error gui
            return socket.error
        else:
            zbrush_port = self.user_zbrush_port.getText()
            #store user defined IP/Port incase window is closed
            os.environ['ZNET'] = zbrush_ip+':'+zbrush_port
            return zbrush_ip, zbrush_port

    def show(self):
        self.gui_window.show()

    def start_listening(self, *args):
        """open maya command port using .main.start()"""
        try:
            maya_ip, maya_port = self.get_maya_settings()
        except socket.error:
            error_gui('Plese specifiy a valid Maya Host or IP')
        else:
            main.stop(self.maya_ip,self.maya_port)
            self.maya_ip = maya_ip
            self.maya_port = maya_port

            status = main.start(self.maya_ip,self.maya_port)
        
            self.status.setBackgroundColor((1,0,.5))
            self.status.setLabel(
                    'Status: not listening')

            if status:
                self.status.setBackgroundColor((0.0,1.0,0.5))
                self.status.setLabel(
                        'Status: listening ('+self.maya_ip+':'+str(self.maya_port)+')')
            else:
                error_gui('Please specify a valid Maya Host or IP')

    def execute(self, *args):
        try:
            self.zbrush_ip, self.zbrush_port = self.get_zbrush_settings()
            main.send_to_zbrush(self.zbrush_ip, self.zbrush_port)
        except TypeError:
            error_gui('Plese specifiy a valid ZBrush IP')
        except IndexError:
            error_gui('Please select a polygon object')
        else:
            self.gui_window.setVisible(False)


def error_gui(message):
    """ simple gui for displaying errors """
    
    confirmDialog(title='Error',
                message= str(message),
                button=['Ok'])

def execute_shelf():
    """
    used for shelf send (so you dont need the gui all the time)
    
    checks ZNET is valid, checks for an object in current seleciton
    """
    try:
        zbrush_ip, zbrush_port = os.environ['ZNET'].split(':')
        main.send_to_zbrush(zbrush_ip, zbrush_port)
    except KeyError:
        error_gui('ZNET is undefined')
    except IndexError:
        error_gui('Please select a polygon object')
        

