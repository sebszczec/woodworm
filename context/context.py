class Context:
    def __init__(self, ircNick, ip, port):
        self.ircNick = ircNick
        self.ip = ip
        self.port = port
        self.connected = False

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
    

