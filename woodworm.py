from time import sleep
from irc import irc_service
from context import context
from botnet import botnet_database
from botnet.tcp import tcp_services
import socket
import os
import threading
from ftp import ftp_services
import logging
import displacement_handler
import command_handler
from tools import timer


class Woodworm:
    def __init__(self, config):
        self.isLooped = True
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

        self.getFileListTimer = timer.Timer(60, self.timer_onGetFilesTimeout, False)

        self.myContext = context.Context(self.ircNick, self.my_ip, self.tcpPort, self.pathToFiles)

        self.tcp_server = tcp_services.TCPServer(self.my_ip, self.tcpPort)        
        self.tcp_server.onConnectionRegistered.subscribe(self.tcpServer_onConnectionReceived)

        self.irc_connection = irc_service.IRCConnection(self.ircServer, self.domain, self.ircServerPort, self.ircNick, self.channel)
        self.irc_connection.onConnected.subscribe(self.irc_onConnected)
        self.irc_connection.onCommandSHUTDOWN.subscribe(self.irc_onCommandSHUTDOWN)

        self.displacement_handler = displacement_handler.DisplacementHandler(self.myContext, self.botnetDB, self.irc_connection)
        self.command_handler = command_handler.CommandHandler(self.myContext, self.botnetDB, self.irc_connection)
        
        self.ftp = ftp_services.FTPServer(self.my_ip, self.ftpPort, self.ftpUser, self.ftpPassword, self.ftpPassiveRange, self.pathToFiles)

        self.getFileListTimer.start()


    def start(self, debug):
        self.irc_connection.connect()
        self.irc_connection.register_user()
        self.tcp_server.start()
    
        if not debug:
            ftpThread = threading.Thread(target=self.ftp.run)
            ftpThread.setDaemon(True)
            ftpThread.start()

            ircThread = threading.Thread(target=self.irc_connection.listen, args=(0.0,))
            ircThread.setDaemon(True)
            ircThread.start()

            tcpThread = threading.Thread(target=self.tcp_server.listen, args=(0.0,))
            tcpThread.setDaemon(True)
            tcpThread.start()

            while self.isLooped:
                sleep(0.1)

        else:
            while True:
                self.irc_connection.listen_step(0.0)
                self.tcp_server.listen_step(0.0)


    def irc_onConnected(self, *args, **kwargs):
        irc_connection = args[0]
        irc_connection.join_channel()


    def irc_onCommandSHUTDOWN(self, *args, **kwargs):
        irc_connection = args[0]
        nickname = kwargs.get('nickname')
        irc_connection.send_query(nickname, "Shutting down...")
      
        self.getFileListTimer.stop()

        self.irc_connection.stop()
        self.tcp_server.stop()

        for bot in self.botnetDB.get_bots().values():
            tcpSession = bot.get_tcp_session()
            if tcpSession.isActive:
                tcpSession.isActive = False
                tcpSession.stop()
            tcpSession = bot.get_reversed_tcp_session()
            if tcpSession.isActive:
                tcpSession.isActive = False
                tcpSession.stop()  
        sleep(1)
        self.isLooped = False
        

    def tcpServer_onConnectionReceived(self, *args, **kwargs):
        nick = kwargs.get('sender')
        connection = kwargs.get('connection')
        linkType = kwargs.get('linkType')
        
        bot = self.botnetDB.get_bot(nick)
        if bot is None:
            logging.warning(f"Bot not found: nick: {nick}")
            sleep(0.5)
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


    def timer_onGetFilesTimeout(self, *args, **kwargs):
        logging.debug("timer_onGetFilesTimeout expired")
        for bot in self.botnetDB.get_bots().keys():
            self.irc_connection.send_query(bot, "LS")
     


    def another_loop(self):
        while True:
            pass
            # logging.debug("I'm still alive!") 

    