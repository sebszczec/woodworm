import time

class Context:
    def __init__(self, ip, port, ircNick):
        self.id = self.generate_id()
        self.ip = ip
        self.port = port
        self.ircNick = ircNick
        self.connected = False

    def generate_id(self):
        utc_time = int(time.time())
        return str(utc_time)
    
    def get_id(self):
        return self.id
    
    def get_ip(self):
        return self.ip
    
    def get_port(self):
        return self.port
    
    def get_irc_nick(self):
        return self.ircNick
    
    def is_connected(self):
        return self.connected
    
    def set_connected(self, connected):
        self.connected = connected
    

