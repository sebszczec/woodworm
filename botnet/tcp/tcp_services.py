import socket
import threading
import os
from tools import event
import time
import logging
from enum import Enum

class TCPConnection:
    class LinkType(Enum):
        UNKNOWN = 0
        DATA = 1
        CONTROL = 2

    def __init__(self, socket, linkType) -> None:
        self.parent = None
        self.socket = socket
        self.linkType = linkType
        self.socketInfo = self.socket.getpeername()
        self.onConnectionClosed = event.Event()
        self.onIdentifyCommandReceived = event.Event()
        self.isSendingData = False
        self.lock = threading.Lock()
        self.downloadPath = '.'
        self.MAX_AUTH_RETRANSMISSIONS = 3
        self.retransmissions = 0
        self.isLoop = True

    def get_link_type(self):
        return self.linkType

    def set_download_path(self, path):
        self.downloadPath = path

    def is_sending_data(self):
        with self.lock:
            return self.isSendingData

    def start(self):
        thread = threading.Thread(target=self.handle_data)
        thread.start()

    def handle_data(self):
        while True:
            if not self.isLoop:
                return
            try:
                data = self.socket.recv(1024).decode()
            except socket.timeout:
                continue
            except ConnectionResetError:
                break

            if not data:
                break

            self.handle_command(data)
        
        self.socket.close()
        self.onConnectionClosed.notify(self)

    def send_command(self, command):
        self.socket.send(command.encode())

    def handle_command(self, command):
        logging.info(f"{self.linkType}: Received TCP command '{command}' from {self.socket.getpeername()[0]}")

        if "CFILE" in command:
            logging.debug(f"{self.linkType}: Proceeding FILE request {command}")
            temp = command.split(' ', 1)[1].split("__")
            filename = temp[0]
            filesize = temp[1]
            self.parent.get_data_link().receive_file(filename, filesize)
            return
        
        if "DIDENTIFY" in command:
            nick = command.split()[1]
            self.onIdentifyCommandReceived.notify(self, sender=nick, linkType=TCPConnection.LinkType.DATA)
            return
        
        if "CIDENTIFY" in command:
            nick = command.split()[1]
            self.onIdentifyCommandReceived.notify(self, sender=nick, linkType=TCPConnection.LinkType.CONTROL)
            return
        
        if "DAUTH-REQ" in command or "CAUTH-REQ" in command:
            if self.retransmissions < self.MAX_AUTH_RETRANSMISSIONS:
                request = command[0] + "IDENTIFY" # command[0] is either 'D' or 'C'
                self.retransmissions = self.retransmissions + 1
                nick = command.split()[1]
                self.send_command(f"{request}: {nick}")
                return
            
            if self.linkType == TCPConnection.LinkType.DATA:
                self.isLoop = False

            logging.info("{self.linkType}: Max AUTH retransmissions received, ingoring IDENTIFY procedure")
            return

        if "DSTOP_LOOP" in command:
            self.isLoop = False
            return

    def send_binary_data(self, data):
        self.socket.send(data)


    def receive_file(self, filename, filesize):
        logging.debug(f"{self.linkType}: Receiving file '{filename}'")
        file = os.path.join(self.downloadPath, filename)
        size = 0
        with open(file, "wb") as file:
            while True:
                try:
                    data = self.socket.recv(1024)
                except socket.timeout:
                    continue
                
                if not data:
                    break
                file.write(data)

                size = size + len(data)
                if size >= int(filesize):
                    break

        logging.info(f"Received file '{filename}'")

    def get_socket_info(self):
        return self.socketInfo

    def close(self):
        self.socket.close()


class TCPSession:
    def __init__(self):
        self.dataLink = None
        self.controlLink = None
        self.isActive = False
        self.isSendingData = False
        self.lock = threading.Lock()
        self.onSendingFinished = event.Event()
        self.onSendingProgress = event.Event()

    def set_data_link(self, dataLink : TCPConnection):
        self.dataLink = dataLink
        self.dataLink.linkType = TCPConnection.LinkType.DATA
        self.dataLink.parent = self
        self.dataLink.onConnectionClosed.subscribe(self.onConnectionClosed)

    def get_data_link(self):
        return self.dataLink
    
    def set_control_link(self, controlLink : TCPConnection):
        self.controlLink = controlLink
        self.controlLink.linkType = TCPConnection.LinkType.CONTROL
        self.controlLink.parent = self

    def get_control_link(self):
        return self.controlLink
    
    def identify(self, ircNick):
        self.dataLink.send_command(f"DIDENTIFY {ircNick}")
        self.controlLink.send_command(f"CIDENTIFY {ircNick}")
        pass

    def onConnectionClosed(self, *args, **kwargs):
        logging.debug(f"TCP connection close detected, closing session")
        self.isActive = False

    def send_command(self, command):
        self.controlLink.send_command(command)

    def send_file(self, **kwargs):
        with self.lock:
            self.isSendingData = True

        filename = kwargs.get("filename")
        logging.info(f"Sending file '{filename}'")
        filesize = os.path.getsize(filename)
        report_filesize = int(filesize) / 1024 / 1024
        name = os.path.basename(filename)

        start_time = time.time()
        progress_start_time = start_time

        self.send_command(f"CFILE {name}__{filesize}")

        trackProgress = False
        divider = 0
        size = 0
        progress_step = 0
        last_progress_size = 0

        if filesize >= 104857600: # 100MB
            trackProgress = True
            divider = filesize / 10
            progress_step = divider

        with open(filename, "rb") as file:
            for data in file:
                self.get_data_link().send_binary_data(data)
                size = size + len(data)
                if trackProgress and size >= divider:
                    progress = int((size / filesize) * 100)
                    tmpSize = size / 1024 / 1024
                    end_time = time.time()
                    execution_time = end_time - progress_start_time
                    progress_size = tmpSize - last_progress_size

                    progress_start_time = end_time
                    last_progress_size = tmpSize
                    
                    tput = progress_size / execution_time   
                    tput = round(tput, 2)
                    progress_size = round(progress_size, 2) 
                    
                    self.onSendingProgress.notify(file=name, progress=progress, tput=tput, progress_size=round(tmpSize, 2), full_size=round(report_filesize, 2), **kwargs)
                    divider += progress_step

        end_time = time.time()
        execution_time = end_time - start_time
        tput = report_filesize / execution_time

        execution_time = round(execution_time, 2)
        tput = round(tput, 2)

        logging.info(f"Sent file '{name}' in {execution_time} seconds, {tput} MB/s")

        with self.lock:
            self.isSendingData = False

        self.onSendingFinished.notify(self, file=name, tput=tput, execution_time=execution_time, **kwargs)

class TCPServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.onConnectionRegistered = event.Event()

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        logging.info(f"TCP Server started on {self.host}:{self.port}")

    def listen_step(self, delay):
        time.sleep(delay)
        self.server_socket.settimeout(1)
        try:
            client_socket, client_address = self.server_socket.accept()
            client_socket.settimeout(5)
            logging.info(f"New TCP connection from {client_address[0]}:{client_address[1]}")
            tcp_connection = TCPConnection(client_socket, TCPConnection.LinkType.UNKNOWN)
            tcp_connection.onConnectionClosed.subscribe(self.tcpConnection_onConnectionClosed)
            tcp_connection.onIdentifyCommandReceived.subscribe(self.tpcConnection_onIdentifyCommandReceived)
            self.clients.append(tcp_connection)
            tcp_connection.start()
        except socket.timeout:
            return

    def listen(self, delay):
        logging.info("Listening for incoming TCP connections")
        while True:
            self.listen_step(delay)

    def tcpConnection_onConnectionClosed(self, *args, **kwargs):
        connection = args[0]
        info = connection.get_socket_info()
        logging.info(f"TCP connection {info[0]}:{info[1]} closed")
        self.clients.remove(connection)

    def tpcConnection_onIdentifyCommandReceived(self, *args, **kwargs):
        connection = args[0]
        sender = kwargs.get("sender")
        linkType = kwargs.get("linkType")
        self.onConnectionRegistered.notify(self, connection=connection, sender=sender, linkType=linkType)
    

class TCPClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def __connect(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)
        try:
            client_socket.connect((self.host, int(self.port)))
            logging.info(f"TCP Connected to {self.host}:{self.port}")
        except ConnectionRefusedError:
            logging.info(f"TCP Connection to {self.host}:{self.port} refused")
            return None
        except socket.timeout:
            logging.info(f"TCP Connection to {self.host}:{self.port} timed out")
            return None
        
        return client_socket

    def connect(self):
        data_link_socket = self.__connect()
        control_link_socket = self.__connect()

        if data_link_socket is None or control_link_socket is None:
            return None 
        
        data_connection = TCPConnection(data_link_socket, TCPConnection.LinkType.DATA)
        data_connection.start()

        control_connection = TCPConnection(control_link_socket, TCPConnection.LinkType.CONTROL)
        control_connection.start()

        tcpSession = TCPSession()
        tcpSession.set_data_link(data_connection)
        tcpSession.set_control_link(control_connection)
        tcpSession.isActive = True

        return tcpSession