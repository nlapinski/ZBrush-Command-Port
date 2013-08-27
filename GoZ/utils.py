"""
Utilities for managing validation and enviromental variables

CONSTANTS:
    
    MAYA_ENV        -- default maya network info env var
    ZBRUSH_ENV      -- default zbrush network info env var

    SHARED_DIR_ENV  -- ZDOCS default file path, /some/path/goz_default
    DEFAULT_NET     -- Contains fallbacks for host/port (local)
    OS              -- platform check
                       currently only osx is supported

    SHARED_DIR_*    -- default OSX file plath for 'localmode'
    SHARED_DIR_*    -- default WIN file path for 'localmode'

"""

import os
import socket
from GoZ import errs
from contextlib import contextmanager
import sys

SHARED_DIR_ENV = 'ZDOCS'

#currently only OSX is supported due to apple script usage
SHARED_DIR_DEFAULT_OSX = '/Users/Shared/Pixologic/GoZProjects'
#win32 api could be used on windows
SHARED_DIR_DEFAULT_WIN = 'C:\\Users\\Public\\Pixologic\\GoZProjects'

OS = sys.platform

# maya network info env
MAYA_ENV = 'MNET'
# zbrush network info env
ZBRUSH_ENV = 'ZNET'

# default network info
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
    """ validates IP/host, or raises and error """

    try:
        host = socket.gethostbyname(host)
    except socket.error:
        raise errs.IpError(host, 'Please specify a valid host: %s' % (host))


def validate(net_string):
    """runs host/port validation on a string"""

    print net_string

    host, port = net_string.split(':')
    validate_host(host)
    validate_port(port)
    return (host, port)


def get_net_info(net_env):
    """
    check for enviromental variabels,
    or defaults network info (local)
    net_env is MNET or ZNET

    missing SHARED_DIR_ENV forces local mode
    """

    # check the shared dir first. it could force us into local mode
    shared_dir = os.getenv(SHARED_DIR_ENV)

    # check for empty but existing env var
    if shared_dir is '':
        shared_dir = None

    if shared_dir is None:
        # if no shared directory is set, start in local modee
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
    """ makes a relative file path to use in maya"""
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
    """ 
    opens zbrush

    blocks untill ZBrush is ready for addional commands
    makes sure ZBrush is ready to install the GUI

    launches ZBrush
    loop to check if ZBrush is 'ready'
    brings ZBrush to front/focus
    clears any crash messages 

    """

    osa = "osascript "\
    +"-e 'tell application \"ZBrush\" to launch' "\
    +"-e 'tell application \"System Events\"' "\
    +"-e 'repeat until visible of process \"ZBrushOSX\" is false' "\
    +"-e 'set visible of process \"ZBrushOSX\" to false' "\
    +"-e 'end repeat' "\
    +"-e 'end tell' "\
    +"-e 'tell application \"System Events\"' "\
    +"-e 'tell application process \"ZBrushOSX\"' "\
    +"-e 'set frontmost to true' "\
    +"-e 'keystroke return' "\
    +"-e 'end tell' "\
    +"-e 'end tell'"
    
    print osa
    os.system(osa)
