import sys
import os
scripts = os.path.expandvars('$ZDOCS/maya_scripts')
sys.path.append(scripts)
import zclient
zclient.send_to_zbrush('144.118.154.204', 6668)
