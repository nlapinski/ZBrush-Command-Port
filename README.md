===================
ZBrush-Command-Port
===================

Connect Maya with ZBrush via Python


Install
=======

zclient
-------

client for sending files to zbrush from maya, includes a gui for setup.
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


zserv
-----

python module to receive files from maya and load in zbrush.

copy mclient to `/your/python/install/site-packages/`
zserv will launch zbrush when loaded, probably better to start ZBrush first.
zserv also places a GUI in zbrush for sending to maya.

host:port can be passed as commandline arguments:
```bash
python -m mclient.zserv 10.10.0.10:6668
```

mclient
-------

client for sending files to maya from zbrush,
this is triggered by 2 ui buttons in ZBrush

```bash
python -m mclient.zbrush_export file_name tool# save/send(0 or 1)
```

General Setup
=============

- Create a folder ZBrush and Maya have acess to (network drive)
- set up some enviromental variables on each machine:

	```bash
	export ZDOCS = /path/to/goz_default
	export MNET your.maya.ip:port
	export ZNET your.zbrush.up:port
	```
