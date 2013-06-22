import sys
import maya.cmds as cmds
import os
import socket
scripts = os.path.expandvars('$ZDOCS/maya_scripts')
sys.path.append(scripts)
import zclient
zclient.send_to_zbrush('144.118.154.204', 6668)

localIP = socket.gethostbyname(socket.gethostname())

cmds.commandPort(n=localIP+':6667',stp='python)
