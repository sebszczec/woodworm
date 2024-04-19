from botnet.tcp import tcp_services

class Context:
    def __init__(self, ircNick, ip, port):
        self.ircNick = ircNick
        self.ip = ip
        self.port = port
        self.connected = False
        self.TcpConnection = tcp_services.TCPClient(ip, port)
        self.TcpReversedConnection = None

    def get_ircNick(self):
        return self.ircNick
    
    def get_ip(self):
        return self.ip
    
    def get_port(self):
        return self.port
    
    def is_connected(self):
        return self.connected
    
    def set_connected(self, connected):
        self.connected = connected
    
    def get_tcp_connection(self):
        return self.TcpConnection
    
    def set_tcp_reversed_connection(self, tcp_connection):
        self.TcpReversedConnection = tcp_connection

    def get_tcp_reverse_connection(self):
        return self.TcpReversedConnection


