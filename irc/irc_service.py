import socket
import asyncio
from log import logger
from tools import event

class IRCConnection:
    onConnected = event.Event()
    onBroadcastRequested = event.Event()
    onSpreadDetected = event.Event()

    def __init__(self, server, domain, port, nickname, channel):
        self.server = server
        self.domain = domain
        self.port = port
        self.nickname = nickname
        self.channel = channel
        self.IRC = None
        self.logger = logger.Logger()
        self.MSG_LEN = 2048
        self.isConnected = False

    async def connect(self):
        self.IRC = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.IRC.connect((self.server, self.port))

    def is_connected(self):
        if self.IRC is None:
            return False
        
        return self.isConnected
            
    async def register_user(self):        
        await self.send_data(f'USER {self.nickname} {self.domain} {self.domain} :{self.nickname}')
        await self.send_data(f'NICK {self.nickname}')

    async def join_channel(self):        
        await self.send_data(f'JOIN {self.channel}')

    async def send_data(self, command):
        self.IRC.send(bytes(command + "\n", "UTF-8"))

    async def send_message(self, message):
        if self.is_connected() == False:
            return
        
        await self.send_data(f'PRIVMSG {self.channel} :{message}')

    async def listen(self):
        while True:
            await asyncio.sleep(0.1)
            
            self.IRC.settimeout(0.1)
            try:
                ircmsg = self.IRC.recv(self.MSG_LEN).decode("UTF-8")
            except socket.timeout:
                continue

            if len(ircmsg) == 0:
                continue

            ircmsg = ircmsg.strip('\r\n')
            
            if ircmsg.startswith("PING :"):
                await self.handle_ping()
                continue
            
            if self.isConnected == False and ("End of /MOTD command" in ircmsg or "376" in ircmsg):
                self.isConnected = True
                await self.onConnected.notify(self)
                self.logger.log(ircmsg)
                continue

            # if "PRIVMSG" in ircmsg:
            #     await self.handle_priv_message(ircmsg)
            #     continue

            if "BROADCAST" in ircmsg:
                await self.handle_broadcast_request()
                continue

            if "SPREAD" in ircmsg:
                await self.handle_spread_detected(ircmsg)
                continue

            self.logger.log(ircmsg)

    async def handle_ping(self):
        await self.send_data("PONG :pingisn")
        self.logger.log("PONG :pingisn")

    async def handle_broadcast_request(self):
        await self.onBroadcastRequested.notify(self)
                      
    async def handle_spread_detected(self, ircmsg):
        try:
            id = ircmsg.split("id:")[1].split(" ")[0]
            ip = ircmsg.split("ip:")[1].split(" ")[0]
            port = ircmsg.split("port:")[1]
            ircNick = ircmsg.split('!', 1)[0][1:]
        except:
            self.logger.log("Error parsing SPREAD message", level=logger.LogLevel.ERROR)
            return

        await self.onSpreadDetected.notify(self, id = id, ip = ip, port = port, ircNick = ircNick)


    async def handle_priv_message(self, ircmsg):
        name = ircmsg.split('!', 1)[0][1:]
        message = ircmsg.split('PRIVMSG', 1)[1].split(':', 1)[1]
        self.logger.log(f"Name: {name}, Message: {message}")





