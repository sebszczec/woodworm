from botnet.tcp import tcp_services
import logging

class Context:
    def __init__(self, ircNick, ip, port, pathToFiles = None):
        self.ircNick = ircNick
        self.ip = ip
        self.port = port
        self.connected = False
        self.tcpSession = tcp_services.TCPSession()
        self.tcpReversedSession = tcp_services.TCPSession()
        self.fileList = list()
        self.fileListRefreshTime = "Never"
        self.pathToFiles = pathToFiles

    def get_ircNick(self):
        return self.ircNick
    
    def get_ip(self):
        return self.ip
    
    def get_port(self):
        return self.port
    
    def set_tcp_session(self, tcp_session):
        self.tcpSession = tcp_session

    def get_tcp_session(self):
        return self.tcpSession
    
    def set_reversed_session(self, tcp_session):
        self.tcpReversedSession = tcp_session

    def get_reversed_tcp_session(self):
        return self.tcpReversedSession
    
    def get_active_tcp_session(self):
        result = self.tcpSession
        if not result.isActive:
            logging.warning(f"Bot {self.ircNick} has no connection, trying to use reversed connection")
            result = self.tcpReversedConnection
        
        if not result.isActive:
            logging.warning(f"Bot {self.ircNick} has no active connections")
            result = None
        
        return result

    def onConnectionClosed(self, *args, **kwargs):
        self.tcpSession = None

    def onReversedConnectionClosed(self, *args, **kwargs):
        self.tcpReversedConnection = None

    def getFileList(self):
        return self.fileList
    
    def getFileListRefreshTime(self):
        return self.fileListRefreshTime

