#!/usr/bin/python

from contextlib import contextmanager

@contextmanager
def handler():
    try:
        yield
    except IpError, e:
        print e
    except PortError,e:
        print e
    except Error,e:
        print e
    finally:
        pass

class Error(Exception):
    """
    Base exception class
    """
    pass

class IpError(Error):
    """
    Exception raised for invalid IP addresses

    Attribitues
        ipo -- input ip address
        msg -- gui message

    """

    def __init__(self,ip,msg):
        self.ip=ip
        self.msg=msg
        error_gui(msg)

class PortError(Error):

    """
    Exception raised for invalid socket ports

    Attributes
        port -- input port
        msg  -- gui msg
    """

    def __init__(self,port,msg):
        self.port=port
        self.msg=msg
        error_gui(msg)

class ZBrushNameError(Error):

    """
    Exception raised for Zbrush naming conflict

    Attributes
        name -- maya name
        goz  -- goz name
        msg  -- gui msg

    """

    def __init__(self,obj,goz_id,msg):
        self.obj=obj
        self.goz_id=goz_id
        self.msg=msg
