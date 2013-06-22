ZBrush-Command-Port
===================

Connect with ZBrush via Python


Install
-------------------

Create a folder ZBrush and Maya have acess to (network drive)
set env var $ZDOCS = /path/to/goz_default

-place zbrush_scripts, and maya_scripts in that folder   
-open send_to_maya.txt with ZBrush    
-copy shelf_script_maya.py to a shelf button and add ZBrush IP address    
-modify load_file_maya.py to include Maya's IP and command port #    
 
-After files are in place lauch Maya+ZBrush    
- ./zserv.py to start listening for commands to send to zbrush    
-start a command port in maya with the maya shelf script    
