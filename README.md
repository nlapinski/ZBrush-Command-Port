===================
ZBrush-Command-Port
===================

Connect Maya with ZBrush via Python


Install
=======

- Download a copy of the repo, place in your site packages  
- Alternativly sym link it to your site-packages folders   
- Currently this only is tested on OSX/Linux, (FC 18, OSX 10.8.2), (Maya2013,ZBrush 4R4P2)
- For the stand alone ZBrushServer TkInter might be needed, should work on python 2.7+ 

```bash
ln -s /Users/name/GoZ/ /your/python/site-packages/GoZ
ln -s /USers/name/GoZ/ /maya/default/site-packages/GoZ
```
- Create a shelf button in Maya simmilar to:  

```python
import GoZ.mayagui    
mayagui=GoZ.mayagui.Win()
```

- Create a 'send' shelf button in Maya:

```python
mayagui.send()
```        

- Start ZBrushServer config with: 

```python
./start_zbrush.py
```

- Create a folder ZBrush and Maya have acess to (network drive)
- set up the shared  enviromental variable on each machine:
- set up the desired server/client host/ports in a env var

```bash
export ZDOCS = /path/to/goz_default
export MNET = 127.0.0.1:6667
export ZNET = 127.0.0.1:6668
```
