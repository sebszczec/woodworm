import threading
from pyftpdlib import servers
from pyftpdlib.handlers import FTPHandler
import os
import asyncio
import logging

class FTPServer(threading.Thread):
    def __init__(self, host='', port=3021, username='anonymous', password=''):
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def run(self):
        handler = FTPHandler
        handler.passive_ports = range(60000, 65535)
        handler.authorizer.add_anonymous(os.getcwd())
        handler.authorizer.add_user('slaugh', 'seb666', '.', perm='elradfmwMT')
        server = servers.FTPServer((self.host, self.port), handler)
        server.serve_forever()

    async def start(self):        
        service = asyncio.to_thread(self.run)
        task = asyncio.create_task(service)

