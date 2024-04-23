import asyncio
from time import sleep
from irc import irc_service
from log import logger
from context import context
from botnet import botnet_database
from botnet.tcp import tcp_services
import socket
import os
import datetime


class Woodworm:
    def __init__(self, pathToFiles, ircNick, channel, domain, ircServer, ircServerPort, tcpPort):
        self.syslog = logger.Logger()
        self.botnetDB = botnet_database.BotnetDatabase()
        self.storageDirectory = pathToFiles
        self.ircNick = ircNick
        self.channel = channel 
        self.domain = domain
        self.ircServer = ircServer
        self.ircServerPort = ircServerPort
        self.my_ip = socket.gethostbyname(socket.gethostname())
        self.tcpPort = tcpPort

        self.myContext = context.Context(self.ircNick, self.my_ip, self.tcpPort)

        self.tcp_server = tcp_services.TCPServer(self.my_ip, self.tcpPort)        
        self.tcp_server.onConnectionRegistered.subscribe(self.tcpServer_onConnectionReceived)

        self.irc_connection = irc_service.IRCConnection(self.ircServer, self.domain, self.ircServerPort, self.ircNick, self.channel)
        self.irc_connection.onConnected.subscribe(self.irc_onConnected)
        self.irc_connection.onBroadcastRequested.subscribe(self.irc_onBroadcastRequested)
        self.irc_connection.onSpreadDetected.subscribe(self.irc_onSpreadDetected)
        self.irc_connection.onSomeoneLeftChannel.subscribe(self.irc_onSomeoneLeftChannel)
        self.irc_connection.onCommandLS.subscribe(self.irc_onCommandLS)
        self.irc_connection.onCommandSTAT.subscribe(self.irc_onCommandSTAT)
        self.irc_connection.onCommandSEND.subscribe(self.irc_onCommandSEND)


    async def start(self, debug):
        await self.irc_connection.connect()
        await self.irc_connection.register_user()
        await self.tcp_server.start()
    
        if not debug:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.irc_connection.listen(0.0))
                tg.create_task(self.tcp_server.listen(0.0))
        else:
            while True:
                await self.irc_connection.listen_step(0.0)
                await self.tcp_server.listen_step(0.0)


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
            bot = context.Context(nick, ip, port)
            tcpClient = tcp_services.TCPClient(ip, port)
            bot.set_tcp_connection(await tcpClient.connect())
            self.botnetDB.add_bot(bot)

            self.syslog.log(f"Bot added to DB: nick: {nick}, ip: {ip} port: {port}", level=logger.LogLevel.INFO)
            self.syslog.log(f"Number of bots: {len(self.botnetDB.get_bots())}", level=logger.LogLevel.INFO)

            await asyncio.sleep(0.5)
            bot.get_tcp_connection().send_command(f"IDENTIFY: {self.ircNick}")


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

    
    async def irc_onCommandSTAT(self, *args, **kwargs):
        irc_connection = args[0]
        filename = kwargs.get('filename')
        nickname = kwargs.get('nickname')
        file_info = await self.get_file_info(filename)

        if file_info is None:
            await irc_connection.send_query(nickname, f"No such file: {filename}")
            return

        modified_time = datetime.datetime.fromtimestamp(file_info['modified']).strftime('%Y-%m-%d %H:%M:%S')
        file_info['modified'] = modified_time
        file_size_mb = file_info['size'] / (1024 * 1024)
        file_info['size'] = f"{round(file_size_mb, 2)} MB"
        await irc_connection.send_query(nickname, f"FILE_INFO {file_info}")


    async def irc_onCommandSEND(self, *args, **kwargs):
        irc_connection = args[0]
        filename = kwargs.get('filename')
        receiver = kwargs.get('receiver')
        nickname = kwargs.get('nickname')
        file_path = os.path.join(self.storageDirectory, filename)

        if not os.path.exists(file_path):
            await irc_connection.send_query(nickname, f"No such file: {filename}")
            return

        bot = self.botnetDB.get_bot(receiver)
        if bot is None:
            await irc_connection.send_query(nickname, f"Bot {receiver} not found")
            return

        connection = bot.get_tcp_connection()
        if connection is None:
            self.syslog.log(f"Bot {receiver} has no connection, trying to use reversed connection", level=logger.LogLevel.WARNING)
            connection = bot.get_reversed_tcp_connection()
        
        if connection is None:
            self.syslog.log(f"Bot {receiver} has no active connections", level=logger.LogLevel.ERROR)
            await irc_connection.send_query(nickname, f"Bot {receiver} has no active connections")
            return  

        if connection.is_sending_data():
            await irc_connection.send_query(nickname, f"Bot {receiver} is busy")
            return

        result = await connection.send_file(file_path)
        await irc_connection.send_query(nickname, f"File {filename} sent to {receiver} in {result['execution_time']} seconds, {result['tput']} MB/s")


    async def list_files(self):
        files = []
        try:
            files = await asyncio.to_thread(os.listdir, self.storageDirectory)
        except Exception as e:
            self.syslog.log(f"Error listing files: {str(e)}", level=logger.LogLevel.ERROR)
        return files


    async def get_file_info(self, filename):
        file_path = os.path.join(self.storageDirectory, filename)
        try:
            file_size = os.path.getsize(file_path)
            file_modified = os.path.getmtime(file_path)
            file_info = {
                'filename': filename,
                'size': file_size,
                'modified': file_modified
            }
            return file_info
        except Exception as e:
            self.syslog.log(f"Error getting file info: {str(e)}", level=logger.LogLevel.ERROR)
            return None
        

    async def tcpServer_onConnectionReceived(self, *args, **kwargs):
        nick = kwargs.get('sender')
        connection = kwargs.get('connection')
        
        bot = self.botnetDB.get_bot(nick)
        if bot is None:
            self.syslog.log(f"Bot not found: nick: {nick}", level=logger.LogLevel.ERROR)
            return
        
        bot.set_reversed_tcp_connection(connection)
        self.syslog.log(f"Reverse connection established with nick: {nick}", level=logger.LogLevel.INFO)


    async def another_loop(self):
        while True:
            await asyncio.sleep(1)
            # self.syslog.log("I'm still alive!", level=logger.LogLevel.DEBUG) 

