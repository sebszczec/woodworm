import time

class Context:
    def __init__(self, ip, port):
        self.id = self.generate_id()
        self.ip = ip
        self.port = port
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
    
    def is_connected(self):
        return self.connected
    
    def set_connected(self, connected):
        self.connected = connected
    

