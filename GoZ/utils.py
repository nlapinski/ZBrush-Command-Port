"""
Utilities for managing validation and enviromental variables

constants:
    SHARED_DIR_ENV  -- ZDOCS default file path, /some/path/goz_default
    DEFAULT_NET     -- Contains fallbacks for host/port (local)

methods:
    validate        -- validates host and port
    validate_host   -- validates a host
    validate_port   -- validates a port
    getenvs         -- returns enviromenal variables
    split_file_name -- returns a object name from full file path
    make_file_name  -- constructs a file path, with ENVs
    err_handler     -- general error handler
                       takes a gui/logger function
    get_net_info    -- takes a env varaible to look for
                       returns host/port
"""

import os
import socket
from . import errs
from contextlib import contextmanager
import sys
import ConfigParser
import errno

SHARED_DIR_ENV = 'ZDOCS'


SHARED_DIR_DEFAULT_OSX = '/Users/Shared/Pixologic/GoZProjects'
SHARED_DIR_DEFAULT_WIN = 'C:\\Users\\Public\\Pixologic\\GoZProjects'

OS = sys.platform

MAYA_ENV = 'MNET'
ZBRUSH_ENV = 'ZNET'

DEFAULT_NET = {MAYA_ENV: 'localhost:6667', ZBRUSH_ENV: 'localhost:6668'}


@contextmanager
def err_handler(gui):
    """handles general GoZ errors, raises a gui/logger on err """

    try:
        yield
    except (errs.PortError,
            errs.IpError,
            errs.SelectionError,
            errs.ZBrushServerError) as err:
        print err.msg
        gui(err.msg)
    except Exception as err:
        print err
        gui(err)
    finally:
        pass


def validate_port(port):
    """ checks port is valid,or raises an error """

    try:
        port = int(port)
    except ValueError:
        raise errs.PortError(port, 'Please specify a valid port: %s' % (port))


def validate_host(host):
    """ pings host, also trys to resolve hostname if a computer name is used """

    try:
        host = socket.gethostbyname(host)
    except socket.error:
        raise errs.IpError(host, 'Please specify a valid host: %s' % (host))


def validate(net_string):
    """
    runs host/port validation on a string
    """

    print net_string

    host, port = net_string.split(':')

    if host == 'localhost':
        return ('',port)

    validate_host(host)
    validate_port(port)
    return (host, port)


def get_net_info(net_env):
    """
    check for enviromental variabels, places them in defaults.cfg
    default back to config file
    finally default network info (local)
    net_env is MNET or ZNET

    check should be added to verify if a host/port can be served on

    """

    # check the shared dir first. it could force us into local mode
    shared_dir = os.getenv(SHARED_DIR_ENV)
    if shared_dir is None:
        # if no shared directory is set, we MUST operate in local mode
        print "No shared directory set. Defaulting to local mode"
        if OS == 'darwin':
            print "working on OSX"
            os.environ[SHARED_DIR_ENV] = SHARED_DIR_DEFAULT_OSX
        elif OS == 'win32' or OS == 'win64':
            print "working on Windows"
            os.environ[SHARED_DIR_ENV] = SHARED_DIR_DEFAULT_WIN
    else:
        net_string = os.environ.get(net_env)

        if net_string:
            host, port = validate(net_string)
            return host, port

    # finally default to local mode
    net_string = DEFAULT_NET[net_env]

    if net_string:
        return validate(net_string)


def split_file_name(file_path):
    """ recovers 'name' from file, strips ext and dir """
    file_name = os.path.splitext(file_path)[0]
    file_name = os.path.split(file_name)[1]

    return file_name

def make_file_name(name):
    """ makes a full resolved file path for zbrush """
    expanded_path = os.path.expandvars(make_fp_rel(name))
    return expanded_path

def make_fp_rel(name):
    name = os.path.relpath(name + '.ma')
    return os.path.join('$' + SHARED_DIR_ENV, name)

def send_osa(script_path):
    """ sends a zscript file for zbrush to open """
    cmd = ['osascript -e',
           '\'tell app "ZBrush"',
           'to open',
           '"' + script_path + '"\'']

    cmd = ' '.join(cmd)
    print cmd
    os.system(cmd)

def open_osa():
    """ opens zbrush """

    cmd = "osascript -e 'tell app \"ZBrush\" to launch'"
    print cmd
    os.system(cmd)

    cmd = "osascript -e 'tell app \"ZBrush\" to activate'"
    print cmd
    os.system(cmd)
