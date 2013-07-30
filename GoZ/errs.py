class GoZError(Exception):

    """
    Exception base

    Attributes
        msg -- gui message

    """


    def __init__(self,msg):
        self.msg=msg


class ZDOCSError(Exception):
    """
    Exception raised for missing ZDOCS env

    Attributes
        msg -- gui message
    """
    def __init__(self,msg):
        self.msg=msg


class IpError(Exception):
    """
    Exception raised for invalid IP addresses

    Attribitues
        ip -- input ip address
        msg -- gui message

    """

    def __init__(self,ip,msg):
        self.ip=ip
        self.msg=msg

class ZBrushServerError(Exception):
    """
    Exception raised for connection failure

    Attribitues
        msg -- gui message

    """

    def __init__(self,msg):
        self.msg=msg

class PortError(Exception):

    """
    Exception raised for invalid socket ports

    Attributes
        port -- input port
        msg  -- gui msg
    """
    def __init__(self,port,msg):
        self.port=port
        self.msg=msg
        self.message=msg

class ZBrushServError(Exception):
    """
    Exception raised for connection refuse from zserv

    Attributes
        msg -- gui msg
    """
    def __init__(self,msg):
        self.msg=msg

class ZBrushNameError(Exception):

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

class SelectionError(Exception):

    """
    Exception raise for no file mesh selected

    Attributes
        msg -- gui msg

    """

    def __init__(self,msg):
        self.msg=msg

class InUseError(Exception):

    """
    Exception raise for commandPort in use (socket in use)

    Attributes
        msg -- gui msg

    """

    def __init__(self,msg):
        self.msg=msg
