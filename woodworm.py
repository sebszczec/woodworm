import asyncio
from time import sleep
from irc import irc_service
from context import context
from botnet import botnet_database
from botnet.tcp import tcp_services
import socket
import os
import threading
import datetime
from ftp import ftp_services
from web import http_services
import logging


class Woodworm:
    def __init__(self, config):
        self.botnetDB = botnet_database.BotnetDatabase()
        self.pathToFiles = config['general']['pathToFiles']
        self.ircNick = config['irc']['nick']
        self.channel = config['irc']['channel']
        self.domain = config['irc']['domain']
        self.ircServer = config['irc']['server']
        self.ircServerPort = int(config['irc']['port'])
        self.tcpPort = int(config['general']['tcpPort'])
        self.ftpPort = int(config['ftp']['port'])
        self.ftpUser = config['ftp']['user']
        self.ftpPassword = config['ftp']['password']
        self.ftpPassiveRange = range(int(config['ftp']['passiveRangeStart']), int(config['ftp']['passiveRangeStop']))
        self.my_ip = socket.gethostbyname(socket.gethostname())


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
        self.irc_connection.onCommandHELP.subscribe(self.irc_onCommandHELP)
        self.irc_connection.onCommandSTATUS.subscribe(self.irc_onCommandSTATUS)
        self.irc_connection.onCommandWGET.subscribe(self.irc_onCommandWGET)
        self.irc_connection.onCommandSHUTDOWN.subscribe(self.irc_onCommandSHUTDOWN)
        
        self.ftp = ftp_services.FTPServer(self.my_ip, self.ftpPort, self.ftpUser, self.ftpPassword, self.ftpPassiveRange, self.pathToFiles)


    async def start(self, debug):
        await self.irc_connection.connect()
        await self.irc_connection.register_user()
        await self.tcp_server.start()
    
        if not debug:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.irc_connection.listen(0.0))
                tg.create_task(self.tcp_server.listen(0.0))
                tg.create_task(self.ftp.start())
        else:
            self.ftp.startT()
            while True:
                await self.irc_connection.listen_step(0.0)
                await self.tcp_server.listen_step(0.0)


    async def irc_onConnected(self, *args, **kwargs):
        irc_connection = args[0]
        await irc_connection.join_channel()


    async def irc_onBroadcastRequested(self, *args, **kwargs):
        irc_connection = args[0]
        logging.debug("Broadcast requested")
        logging.debug("SPREADING...")
        await irc_connection.send_message(f"SPREAD ip:{self.myContext.get_ip()} port:{self.myContext.get_port()}")


    async def irc_onSpreadDetected(self, *args, **kwargs):
        irc_connection = args[0]
        ip = kwargs.get('ip')
        port = kwargs.get('port')
        nick = kwargs.get('ircNick')
        logging.debug(f"SPREAD DETECTED: nick:{nick}, ip:{ip} port:{port}")

        if self.botnetDB.get_bot(nick) is None:
            bot = context.Context(nick, ip, port)
            tcpClient = tcp_services.TCPClient(ip, port)
            tcpSession = await tcpClient.connect()
            if tcpSession is not None:
                bot.set_tcp_session(tcpSession)
                bot.get_tcp_session().get_data_link().set_download_path(self.pathToFiles)
                bot.get_tcp_session().identify(self.ircNick)
                bot.get_tcp_session().onSendingFinished.subscribe(self.tcpSession_onSendingFinished)
                bot.get_tcp_session().onSendingProgress.subscribe(self.tcpSession_onSendingProgress)
            else:
                logging.error(f"Failed to TCP connect to bot: nick: {nick}, ip: {ip} port: {port}")

            bot.get_reversed_tcp_session().onSendingFinished.subscribe(self.tcpSession_onSendingFinished)
            bot.get_reversed_tcp_session().onSendingProgress.subscribe(self.tcpSession_onSendingProgress)
                                 
            self.botnetDB.add_bot(bot)

            logging.info(f"Bot added to DB: nick: {nick}, ip: {ip} port: {port}")
            logging.info(f"Number of bots: {len(self.botnetDB.get_bots())}")
            

    async def irc_onSomeoneLeftChannel(self, *args, **kwargs):
        nick = kwargs.get('ircNick')
        if self.botnetDB.get_bot(nick) is not None:
            self.botnetDB.remove_bot(self.botnetDB.get_bot(nick))
            logging.info(f"Bot removed from DB: nick: {nick}")
            logging.info(f"Number of bots: {len(self.botnetDB.get_bots())}")


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

        file_path = os.path.join(self.pathToFiles, filename)

        if not os.path.exists(file_path):
            await irc_connection.send_query(nickname, f"No such file: {filename}")
            return

        bot = self.botnetDB.get_bot(receiver)
        if bot is None:
            await irc_connection.send_query(nickname, f"Bot {receiver} not found")
            return

        tcpSession = bot.get_tcp_session()

        if not tcpSession.isActive:
            logging.warning(f"Bot {receiver} has no connection, trying to use reversed connection")
            tcpSession = bot.get_reversed_tcp_session()

        if not tcpSession.isActive:
            logging.error(f"Bot {receiver} has no active connections")
            await irc_connection.send_query(nickname, f"Bot {receiver} has no active connections")
            return  

        if tcpSession.isSendingData:
            await irc_connection.send_query(nickname, f"Bot {receiver} is busy sending other file")
            return
        coro = asyncio.to_thread(tcpSession.send_file, filename=file_path, nickname=nickname, receiver=receiver)
        # thread = threading.Thread(target=tcpSession.send_file, kwargs={'filename' : file_path, 'nickname': nickname, 'receiver': receiver})
        task = asyncio.create_task(coro)
        # thread.start()
        
        await irc_connection.send_query(nickname, f"Transfer of {filename} to {receiver} started")


    async def irc_onCommandHELP(self, *args, **kwargs):
        irc_connection = args[0]
        nickname = kwargs.get('nickname')
        await irc_connection.send_query(nickname, "HELP: HELP, LS, SEND, STATUS, STAT")


    async def irc_onCommandSTATUS(self, *args, **kwargs):
        irc_connection = args[0]
        nickname = kwargs.get('nickname')
        await irc_connection.send_query(nickname, f"STATUS: {len(self.botnetDB.get_bots())} bots connected")

        for bot in self.botnetDB.get_bots().values():
            info = f"BOT: {bot.get_ircNick()} {bot.get_ip()}:{bot.get_port()}"
            tcpSession = bot.get_tcp_session()
            if tcpSession.isActive:
                info += f" TCP connection: [active]"
            else:
                info += f" TCP connection: [inactive]"
            
            tcpSession = bot.get_reversed_tcp_session()
            if tcpSession.isActive:
                info += f" Reversed TCP connection: [active]"
            else:
                info += f" Reversed TCP connection: [inactive]"
            
            await irc_connection.send_query(nickname, info)


    async def irc_onCommandWGET(self, *args, **kwargs):
        irc_connection = args[0]
        nickname = kwargs.get('nickname')
        url = kwargs.get('url')
        filename = url.split('/')[-1]
        savePath = os.path.join(self.pathToFiles, filename)
        
        downloader = http_services.FileDownloader(url)
        downloader.onDownloadCompleted.subscribe(self.downloader_onDownloadCompleted)
        downloader.onDownloadProgress.subscribe(self.downloader_onDownloadProgress)

        download_thread = asyncio.to_thread(downloader.download_file, savePath, nickname=nickname)
        task = asyncio.create_task(download_thread)
        await irc_connection.send_query(nickname, f"Downloading of {url} started")


    async def irc_onCommandSHUTDOWN(self, *args, **kwargs):
        irc_connection = args[0]
        nickname = kwargs.get('nickname')
        await irc_connection.send_query(nickname, "Shutting down...")
        await asyncio.sleep(1)
        quit(0)


    async def downloader_onDownloadCompleted(self, *args, **kwargs):
        irc_connection = self.irc_connection
        nickname = kwargs.get('nickname')
        filename = kwargs.get('filename')
        filesize = kwargs.get('filesize')
        tput = kwargs.get('tput')
        time = kwargs.get('time')
        await irc_connection.send_query(nickname, f"File {filename} downloaded successfully. Size: {filesize} MB, Time: {time} s, Throughput: {tput} MB/s")


    async def downloader_onDownloadProgress(self, *args, **kwargs):
        irc_connection = self.irc_connection
        nickname = kwargs.get('nickname')
        filename = kwargs.get('filename')
        progress = kwargs.get('progress')
        tput = kwargs.get('tput')
        progress_size = kwargs.get('progress_size')
        full_size = kwargs.get('full_size')
        await irc_connection.send_query(nickname, f"Downloading {filename}: {progress}%, {progress_size} out of {full_size} MB, Throughput: {tput} MB/s")


    async def list_files(self):
        files = []
        try:
            files = os.listdir(self.pathToFiles)
        except Exception as e:
            logging.error(f"Error listing files: {str(e)}")
        return files


    async def get_file_info(self, filename):
        file_path = os.path.join(self.pathToFiles, filename)
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
            logging.error(f"Error getting file info: {str(e)}")
            return None
        

    async def tcpServer_onConnectionReceived(self, *args, **kwargs):
        nick = kwargs.get('sender')
        connection = kwargs.get('connection')
        linkType = kwargs.get('linkType')
        
        bot = self.botnetDB.get_bot(nick)
        if bot is None:
            logging.error(f"Bot not found: nick: {nick}")
            await asyncio.sleep(0.5)
            if linkType == tcp_services.TCPConnection.LinkType.DATA:
                connection.send_command(f"DAUTH-REQ {nick}")
            else:
                connection.send_command(f"CAUTH-REQ {nick}")
            return
        
        tcpReversedSession = bot.get_reversed_tcp_session()
        tcpReversedSession.isActive = True

        connection.set_download_path(self.pathToFiles)
        connection.linkType = linkType
        
        if linkType == tcp_services.TCPConnection.LinkType.DATA:
            tcpReversedSession.set_data_link(connection)
            connection.isLoop = False
            connection.send_command(f"DSTOP_LOOP")
        else:
            tcpReversedSession.set_control_link(connection)

        logging.info(f"Reverse {linkType} connection established with nick: {nick}")


    async def tcpSession_onSendingFinished(self, *args, **kwargs):
        filename = kwargs.get('file')
        nickname = kwargs.get('nickname')
        receiver = kwargs.get('receiver')
        tput = kwargs.get('tput')
        execution_time = kwargs.get('execution_time')
        await self.irc_connection.send_query(nickname, f"File {filename} sent to {receiver} in {execution_time} seconds, {tput} MB/s")


    async def tcpSession_onSendingProgress(self, *args, **kwargs):
        nickname = kwargs.get('nickname')
        filename = kwargs.get('file')
        progress = kwargs.get('progress')
        receiver = kwargs.get('receiver')
        tput = kwargs.get('tput')
        progress_size = kwargs.get('progress_size')
        full_size = kwargs.get('full_size')
        await self.irc_connection.send_query(nickname, f"Sending {filename} to {receiver}: {progress}%, {progress_size} out of {full_size} MB, Throughput: {tput} MB/s")


    async def another_loop(self):
        while True:
            await asyncio.sleep(1)
            # logging.debug("I'm still alive!") 

    