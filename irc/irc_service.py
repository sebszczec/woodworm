import socket
import asyncio
from log import logger
from tools import event

class IRCConnection:
    onConnected = event.Event()

    def __init__(self, server, port, nickname, channel):
        self.server = server
        self.port = port
        self.nickname = nickname
        self.channel = channel
        self.IRC = None
        self.logger = logger.Logger()
        self.MSG_LEN = 2048

    def connect(self):
        self.IRC = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.IRC.connect((self.server, self.port))

    def register_user(self):
        self.send_data(f'USER {self.nickname} slaugh.pl slaugh.pl :{self.nickname}')
        self.send_data(f'NICK {self.nickname}')

    def join_channel(self):
        self.send_data(f'JOIN {self.channel}')

    def send_data(self, command):
        self.IRC.send(bytes(command + "\n", "UTF-8"))

    async def listener(self):
        self.IRC.settimeout(0.1)
        try:
            ircmsg = self.IRC.recv(self.MSG_LEN).decode("UTF-8")
        except socket.timeout:
            return

        if len(ircmsg) == 0:
            return

        ircmsg = ircmsg.strip('\r\n')
        
        if "PRIVMSG" in ircmsg:
            self.handle_priv_message(ircmsg)
            return
        
        if ircmsg.startswith("PING :"):
            self.handle_ping()
            return
        
        if "End of /MOTD command" in ircmsg or "376" in ircmsg:
            await self.onConnected.notify(self)
            self.logger.log(ircmsg)
            return

        self.logger.log(ircmsg)

    def handle_ping(self):
        self.IRC.send(bytes("PONG :pingisn", "UTF-8"))
                      
    def handle_priv_message(self, ircmsg):
        name = ircmsg.split('!', 1)[0][1:]
        message = ircmsg.split('PRIVMSG', 1)[1].split(':', 1)[1]
        self.logger.log(f"Name: {name}, Message: {message}")





