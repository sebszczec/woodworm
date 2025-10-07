import logging
from context import context
from botnet.tcp import tcp_services

class DisplacementHandler:
    def __init__(self, context, botnetDB, irc_connection):
        self.myContext = context
        self.botnetDB = botnetDB
        self.irc_connection = irc_connection

        self.irc_connection.onBroadcastRequested.subscribe(self.irc_onBroadcastRequested)
        self.irc_connection.onSpreadDetected.subscribe(self.irc_onSpreadDetected)
        self.irc_connection.onSomeoneLeftChannel.subscribe(self.irc_onSomeoneLeftChannel)


    def irc_onBroadcastRequested(self, *args, **kwargs):
        irc_connection = args[0]
        logging.debug("Broadcast requested")
        logging.debug("SPREADING...")
        irc_connection.send_message(f"SPREAD ip:{self.myContext.get_ip()} port:{self.myContext.get_port()}")

    
    def irc_onSpreadDetected(self, *args, **kwargs):
        ip = kwargs.get('ip')
        port = kwargs.get('port')
        nick = kwargs.get('ircNick')
        logging.debug(f"SPREAD DETECTED: nick:{nick}, ip:{ip} port:{port}")

        if self.botnetDB.get_bot(nick) is None:
            bot = context.Context(nick, ip, port)
            
            self.botnetDB.add_bot(bot)
            logging.info(f"Bot added to DB: nick: {nick}, ip: {ip} port: {port}")
            logging.info(f"Number of bots: {len(self.botnetDB.get_bots())}")

            tcpClient = tcp_services.TCPClient(ip, port)
            tcpSession = tcpClient.connect()
            if tcpSession is not None:
                bot.set_tcp_session(tcpSession)
                bot.get_tcp_session().get_data_link().set_download_path(self.myContext.pathToFiles)
                bot.get_tcp_session().identify(self.myContext.ircNick)
                bot.get_tcp_session().onSendingFinished.subscribe(self.tcpSession_onSendingFinished)
                bot.get_tcp_session().onSendingProgress.subscribe(self.tcpSession_onSendingProgress)
                bot.get_tcp_session().onFileReceived.subscribe(self.tcpSession_onFileReceived)
            else:
                logging.error(f"Failed to TCP connect to bot: nick: {nick}, ip: {ip} port: {port}")

            bot.get_reversed_tcp_session().onSendingFinished.subscribe(self.tcpSession_onSendingFinished)
            bot.get_reversed_tcp_session().onSendingProgress.subscribe(self.tcpSession_onSendingProgress)
            bot.get_reversed_tcp_session().onFileReceived.subscribe(self.tcpSession_onFileReceived)
            

    def irc_onSomeoneLeftChannel(self, *args, **kwargs):
        nick = kwargs.get('ircNick')
        if self.botnetDB.get_bot(nick) is not None:
            self.botnetDB.remove_bot(self.botnetDB.get_bot(nick))
            logging.info(f"Bot removed from DB: nick: {nick}")
            logging.info(f"Number of bots: {len(self.botnetDB.get_bots())}")


    def tcpSession_onSendingFinished(self, *args, **kwargs):
        filename = kwargs.get('file')
        nickname = kwargs.get('nickname')
        receiver = kwargs.get('receiver')
        tput = kwargs.get('tput')
        execution_time = kwargs.get('execution_time')
        self.irc_connection.send_query(nickname, f"File {filename} sent to {receiver} in {execution_time} seconds, {tput} Mb/s")


    def tcpSession_onSendingProgress(self, *args, **kwargs):
        nickname = kwargs.get('nickname')
        filename = kwargs.get('file')
        progress = kwargs.get('progress')
        receiver = kwargs.get('receiver')
        tput = kwargs.get('tput')
        progress_size = kwargs.get('progress_size')
        full_size = kwargs.get('full_size')
        self.irc_connection.send_query(nickname, f"Sending {filename} to {receiver}: {progress}%, {progress_size} out of {full_size} MB, Throughput: {tput} Mb/s")

    
    def tcpSession_onFileReceived(self, *args, **kwargs):
        filename = kwargs.get('filename')
        self.irc_connection.send_message(f"File {filename} received")
