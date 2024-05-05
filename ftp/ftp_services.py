import threading
from pyftpdlib import servers
from pyftpdlib.handlers import FTPHandler
import os
import asyncio
import logging

class FTPServer(threading.Thread):
    def __init__(self, host='', port=21, username='', password='', passivePorts=range(60000, 65535), filesPath='.'):
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.passiveRange = passivePorts
        self.filesPath = filesPath

    def run(self):
        handler = FTPHandler
        handler.passive_ports = self.passiveRange
        handler.authorizer.add_user(self.username, self.password, self.filesPath, perm='elradfmwMT')
        # server = servers.FTPServer((self.host, self.port), handler)
        server = servers.ThreadedFTPServer((self.host, self.port), handler)
        server.serve_forever()


