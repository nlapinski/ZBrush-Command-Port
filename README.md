ZBrush-Command-Port
===================

Connect Maya with ZBrush via Python


Install
-------------------

**zclient**
client for sending files to zbrush from maya, includes a gui for setup
place in your/maya/install/site-packages/zclient

create a shelf button in maya with:
```python
import zclient
mainwindow=zclient.gui.win()
```
this is for the setup GUI

create another shelf button with:
```python
mainwindow.execute_shelf()
```
this button is for sending to zbrush, after the GUI is setup with IP info


**zserv** 
python module to recive files from maya and load in zbrush
copy mclient to /your/python/install/site-packages/
zserv will launch zbrush when loaded
host:port can be passed as commandline arguments
```bash
python -m zserv 10.10.0.10:6668
```

**mclient**
client for sending files to maya from zbrush

**General setup**
Create a folder ZBrush and Maya have acess to (network drive)

set up some enviromental variables on each machine

```bash
export ZDOCS = /path/to/goz_default
export MNET your.maya.ip:port
export ZNET your.zbrush.up:port
```


OLD INFO:

-place zbrush_scripts, and maya_scripts in that folder   
-open send_to_maya.txt with ZBrush    
-copy shelf_script_maya.py to a shelf button and add ZBrush IP address    
-modify load_file_maya.py to include Maya's IP and command port #    
 
-after files are in place lauch Maya+ZBrush    
-run zserv.py to start listening for commands to send to zbrush    
-start a command port in maya with the maya shelf script    
