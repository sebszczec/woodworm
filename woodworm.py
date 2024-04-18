import asyncio
from time import sleep
from irc import irc_service
from log import logger
from context import context
from botnet import botnet_database
import socket
import os

class Woodworm:
    def __init__(self, pathToFiles, ircNick, channel, domain, ircServerPort):
        self.syslog = logger.Logger()
        self.botnetDB = botnet_database.BotnetDatabase()
        self.storageDirectory = pathToFiles
        self.ircNick = ircNick
        self.channel = channel 
        self.domain = domain
        self.ircServerPort = ircServerPort
        self.my_ip = socket.gethostbyname(socket.gethostname())
        
        self.myContext = context.Context(self.ircNick, self.my_ip, 3000)
        self.myContext.set_connected(True)
        
        self.irc_connection = irc_service.IRCConnection(self.domain, self.domain, self.ircServerPort, self.ircNick, self.channel)
        
        self.irc_connection.onConnected.subscribe(self.irc_onConnected)
        self.irc_connection.onBroadcastRequested.subscribe(self.irc_onBroadcastRequested)
        self.irc_connection.onSpreadDetected.subscribe(self.irc_onSpreadDetected)
        self.irc_connection.onSomeoneLeftChannel.subscribe(self.irc_onSomeoneLeftChannel)
        self.irc_connection.onCommandLS.subscribe(self.irc_onCommandLS)

        print("Woodworm initialized")


    async def start(self):
        await self.irc_connection.connect()
        await self.irc_connection.register_user()
    
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.irc_connection.listen())
            tg.create_task(self.another_loop())

        # await irc_connection.listen()


    async def irc_onConnected(self, *args, **kwargs):
        irc_connection = args[0]
        await irc_connection.join_channel()


    async def irc_onBroadcastRequested(self, *args, **kwargs):
        irc_connection = args[0]
        self.syslog.log("Broadcast requested", level=logger.LogLevel.DEBUG)
        self.syslog.log("SPREADING...", level=logger.LogLevel.DEBUG)
        await irc_connection.send_message(f"SPREAD ip:{self.myContext.get_ip()} port:{self.myContext.get_port()}")


    async def irc_onSpreadDetected(self, *args, **kwargs):
        irc_connection = args[0]
        ip = kwargs.get('ip')
        port = kwargs.get('port')
        nick = kwargs.get('ircNick')
        self.syslog.log(f"SPREAD DETECTED: nick:{nick}, ip:{ip} port:{port}", level=logger.LogLevel.DEBUG)

        if self.botnetDB.get_bot(nick) is None:
            self.botnetDB.add_bot(context.Context(nick, ip, port))
            self.syslog.log(f"Bot added to DB: nick: {nick}, ip: {ip} port: {port}", level=logger.LogLevel.INFO)
            self.syslog.log(f"Number of bots: {len(self.botnetDB.get_bots())}", level=logger.LogLevel.INFO)


    async def irc_onSomeoneLeftChannel(self, *args, **kwargs):
        nick = kwargs.get('ircNick')
        if self.botnetDB.get_bot(nick) is not None:
            self.botnetDB.remove_bot(self.botnetDB.get_bot(nick))
            self.syslog.log(f"Bot removed from DB: nick: {nick}", level=logger.LogLevel.INFO)
            self.syslog.log(f"Number of bots: {len(self.botnetDB.get_bots())}", level=logger.LogLevel.INFO)


    async def irc_onCommandLS(self, *args, **kwargs):
        irc_connection = args[0]
        nickname = kwargs.get('nickname')
        files = await self.list_files()
        await irc_connection.send_query(nickname, f"FILES {files}")


    async def list_files(self):
        files = []
        try:
            files = await asyncio.to_thread(os.listdir, self.storageDirectory)
        except Exception as e:
            self.syslog.log(f"Error listing files: {str(e)}", level=logger.LogLevel.ERROR)
        return files


    async def another_loop(self):
        while True:
            await asyncio.sleep(1)
            self.syslog.log("I'm still alive!", level=logger.LogLevel.DEBUG) 

