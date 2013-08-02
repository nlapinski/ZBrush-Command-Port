"""
Utilities for managing validation and enviromental variables

constants:
    SHARED_DIR_ENV  -- ZDOCS default file path, /some/path/goz_default
    DEFAULT_NET     -- Contains fallbacks for host/port (local)
    CFG             -- python config file with host/port info

methods:
    validate        -- validates host and port
    validate_host   -- validates a host
    validate_port   -- validates a port
    getenvs         -- returns enviromenal variables
    split_file_name -- returns a object name from full file path
    make_file_name  -- constructs a file path, with ENVs
    err_handler     -- general error handler
                       takes a gui/logger function
    get_net_info    -- takes a eniromental varaible to look for
                       returns host/port
    read_cfg        -- looks in defaults.cfg for host/port info

"""

import os
import socket
from . import errs
from contextlib import contextmanager
import sys
from threading import Thread
import ConfigParser
import errno

SHARED_DIR_ENV = 'ZDOCS'
DEFAULT_NET = {'MNET': '127.0.0.1:6667', 'ZNET': '127.0.0.1:6668'}
CFG = 'defaults.cfg'


@contextmanager
def err_handler(gui):
    """handles general GoZ errors, raises a gui/logger on err """

    try:
        yield
    except (errs.PortError,
            errs.IpError,
            errs.SelectionError,
            errs.InUseError,
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
    route = os.system("ping -t 2 -c 1 " + host)

    if route != 0:
        raise errs.IpError(host, 'Please specify a valid host: %s' % (host))

    try:
        host = socket.gethostbyname(host)
        socket.inet_aton(host)
    except socket.error:
        raise errs.IpError(host, 'Please specify a valid host: %s' % (host))


def validate(net_string):
    """
    runs host/port validation on a string
    in xx.xx.xx.xx:xxxx format (host:port)
    """

    host, port = net_string.split(':')
    validate_host(host)
    validate_port(port)
    return (host, port)


def read_cfg(net_env):
    """ read defaults.cfg and try to return the host/port """

    cfg_path = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.join(cfg_path, CFG)
    config = ConfigParser.ConfigParser()
    config.read(cfg_path)
    try:
        return config.get('GoZ', net_env)
    except ConfigParser.NoSectionError:
        return


def writecfg(host, port, key):
    """
    stores any changes in the GUI to defaults.cfg
    also stores cahnges in env vars (current process)
    """

    os.environ[key] = '%s:%s' % (host, port)

    cfg_path = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.join(cfg_path, 'defaults.cfg')

    config = ConfigParser.ConfigParser()
    config.read(cfg_path)
    host, port = str(host), str(port)
    config.set('GoZ', str(key), '%s:%s' % (host, port))

    with open(cfg_path, 'wb') as configfile:
        config.write(configfile)


def get_net_info(net_env):
    """
    check for enviromental variabels, places them in defaults.cfg
    default back to config file
    finally default network info (local)
    net_env is MNET or ZNET

    check should be added to verify if a host/port can be served on

    check env vars (MNET/ZNET), write to cfg
    cfg might be removed, it is useful if env vars are not set globally
    """

    net_string = os.environ.get(net_env)

    if net_string:
        host, port = validate(net_string)
        writecfg(host, port, net_env)

    # env vars failed defaults to defaults.cfg
    net_string = read_cfg(net_env)

    if net_string:
        print net_string
        return validate(net_string)

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
    name = os.path.relpath(name + '.ma')
    env_path = os.path.join('$' + SHARED_DIR_ENV, name)
    expanded_path = os.path.expandvars(env_path)
    return expanded_path


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
