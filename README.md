===================
ZBrush-Command-Port
===================

Connect Maya with ZBrush via Python


Install
=======

- Download a copy of the repo, place in your site packages  
- Alternativly sym link it to your site-packages folders   
- Currently this only is tested on OSX/Linux   

	```bash
	ln -s /Users/name/GoZ/ /your/python/site-packages/GoZ
        ln -s /USers/name/GoZ/ /maya/default/site-packages/GoZ
	```
- Create a shelf button in Maya simmilar to:  

	```python
	import GoZ.mayagui    
        mayagui=GoZ.mayagui.Win()
	```

- Start ZBrushServer config with: 

	```python
	/usr/bin/python -m GoZ.go
	```

General Setup
=============

- Create a folder ZBrush and Maya have acess to (network drive)
- set up the shared  enviromental variable on each machine:

	```bash
	export ZDOCS = /path/to/goz_default
	```
