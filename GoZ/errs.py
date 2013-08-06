""" custom exceptions for GoZ """


class IpError(Exception):

    """
    Exception raised for invalid IP addresses

    Attribitues
        host -- input host address
        msg -- gui message

    """

    def __init__(self, host, msg):
        Exception.__init__(self, msg)
        self.host = host
        self.msg = msg


class ZBrushServerError(Exception):

    """
    Exception raised for connection failure

    Attribitues
        msg -- gui message

    """

    def __init__(self, msg):
        Exception.__init__(self, msg)
        self.msg = msg


class PortError(Exception):

    """
    Exception raised for invalid socket ports

    Attributes
        port -- input port
        msg  -- gui msg
    """

    def __init__(self, port, msg):
        Exception.__init__(self, msg)
        self.port = port
        self.msg = msg
        self.message = msg


class SelectionError(Exception):

    """
    Exception raise for no file mesh selected

    Attributes
        msg -- gui msg

    """

    def __init__(self, msg):
        Exception.__init__(self, msg)
        self.msg = msg
