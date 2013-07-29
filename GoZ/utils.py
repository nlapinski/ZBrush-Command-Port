#!/usr/bin/python
import os
import socket
import errs
from contextlib import contextmanager
import sys
from threading import Thread
import ConfigParser

SHARED_DIR_ENV = 'ZDOCS'
UP = True
DOWN = False


"""
Utility class for managing validation and enviromental variables

constants:
    SHARED_DIR_ENV  --
    MNET            --
    ZNET            --
    UP              --
    DOWN            --

methods:
    validate        --
    getenvs         --
    split_file_name --
    make_file_name  --
    err_handler     --

"""

@contextmanager
def err_handler():
    
    try:
        yield
    except errs.GoZError, e:
        print e.msg
    except Exception,e:
        print e
        raise e
    finally:
        pass

def validate_port(port):

    try:
        port = int(port)
    except ValueError:
        raise errs.PortError(port,'Please specify a valid port')

def validate_host(host):

    route = os.system("ping -t 2 -c 1 "+host)

    if route != 0:
        raise errs.IpError(host,'Please specify a valid host')

    try:
        host = socket.gethostbyname(host)
        socket.inet_aton(host)
    except socket.error:
        raise errs.IpError(host,'Please specify a valid host')

def writecfg(host,port,key):

    cfg_path = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.join(cfg_path,'defaults.cfg')

    config = ConfigParser.ConfigParser()
    config.read(cfg_path)
    host,port = str(host),str(port)
    config.set('GoZ', str(key), '%s:%s'%(host,port))

    with open(cfg_path, 'wb') as configfile:
        config.write(configfile)

    pass

def getenvs(**kwargs):


    cfg_path = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.join(cfg_path,'defaults.cfg')
    
    config = ConfigParser.ConfigParser()
    config.read(cfg_path)

    mnet = config.get('GoZ','MNET')
    znet = config.get('GoZ','ZNET')

    env_list = []

    if 'maya' in kwargs:
        mhost,mport = mnet.split(':')
        try:
                validate_host(mhost)
        except errs.IpError:
                mhost = socket.gethostbyname(socket.getfqdn())
        try:
                validate_port(mport)
        except errs.PortError:
                mport = 6667

        if 'serv' in kwargs:
            sock = socket.socket()
            try:
                   sock.bind((mhost,int(mport)))
                   sock.close()
            except socket.error,e:

                   print e
                   mhost = socket.gethostbyname(socket.getfqdn())

        env_list.append(mhost)
        env_list.append(mport)

    if 'zbrush' in kwargs:
        zhost,zport = znet.split(':')
        
        try:
            validate_host(zhost)
        except errs.IpError:
            zhost = socket.gethostbyname(socket.getfqdn())
        try:
            validate_port(zport)
        except errs.PortError:
            zport = 6668
        if 'serv' in kwargs:
               sock = socket.socket()
               try:
                   sock.bind((zhost,int(zport)))
                   sock.close()
               except socket.error,e:
                   print e
                   zhost = socket.gethostbyname(socket.getfqdn())

        env_list.append(zhost)
        env_list.append(zport)

    if 'shared_dir' in kwargs:
        env_list.append(SHARED_DIR_ENV)

    return env_list

def split_file_name(file_path):

    file_name=os.path.splitext(file_path)[0]
    file_name=os.path.split(file_name)[1]

    return file_name

def make_file_name(name):
    name = os.path.relpath(name + '.ma')
    env_path = os.path.join('$'+SHARED_DIR_ENV, name)
    expanded_path = os.path.expandvars(env_path)
    return expanded_path


def send_osa(script_path):
    cmd = ['osascript -e',
            '\'tell app "ZBrush"',
             'to open',
            '"' + script_path + '"\'']

    cmd = ' '.join(cmd)
    print cmd 
    os.system(cmd)
    #return ret
