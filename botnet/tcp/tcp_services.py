import socket
import threading
import os
import asyncio
from tools import event
import time
import logging
from enum import Enum

class TCPConnection:
    class LinkType(Enum):
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

    def get_link_type(self):
        return self.linkType

    def set_download_path(self, path):
        self.downloadPath = path

    def is_sending_data(self):
        with self.lock:
            return self.isSendingData

    def start(self):
        connection_thread = asyncio.to_thread(self.handle_data)
        task = asyncio.create_task(connection_thread)

    def handle_data(self):
        while True:
            try:
                data = self.socket.recv(1024).decode()
            except socket.timeout:
                continue
            except ConnectionResetError:
                break

            if not data:
                break

            # Handle received data
            if data.startswith("FILE"):
                logging.debug(f"Proceeding FILE request {data}")
                temp = data.split(' ', 1)[1].split("__")
                filename = temp[0]
                filesize = temp[1]

                self.send_command("READY TO RECEIVE")

                self.receive_file(filename, filesize)
            else:
                # Handle other commands
                self.handle_command(data)
        
        self.socket.close()
        asyncio.run(self.onConnectionClosed.notify(self))

    def send_command(self, command):
        self.socket.send(command.encode())

    def handle_command(self, command):
        logging.info(f"Received TCP command '{command}' from {self.socket.getpeername()[0]}")
        
        if "IDENTIFY" in command:
            nick = command.split()[1]
            asyncio.run(self.onIdentifyCommandReceived.notify(self, sender=nick))
            return
        
        if "AUTH-REQ" in command:
            if self.retransmissions < self.MAX_AUTH_RETRANSMISSIONS:
                self.retransmissions = self.retransmissions + 1
                nick = command.split()[1]
                self.send_command(f"IDENTIFY: {nick}")
                return
            
            logging.info("Max AUTH retransmissions received, ingoring IDENTIFY procedure")
            return

    async def send_file(self, filename):
        with self.lock:
            self.isSendingData = True

        logging.debug(f"Sending file '{filename}'")
        filesize = os.path.getsize(filename)
        name = os.path.basename(filename)
        self.send_command(f"FILE {name}__{filesize}")

        try:
            data = self.socket.recv(1024).decode()
            if data.startswith("READY TO RECEIVE"):
                logging.debug(f"Received READY TO RECEIVE")
        except socket.timeout:
            pass
        
        start_time = time.time()

        with open(filename, "rb") as file:
            for data in file:
                self.socket.send(data)

        end_time = time.time()
        execution_time = end_time - start_time
        tput = int(filesize) / 1024 / 1024 / execution_time

        execution_time = round(execution_time, 2)
        tput = round(tput, 2)

        logging.info(f"Sent file '{name}' in {execution_time} seconds, {tput} MB/s")

        with self.lock:
            self.isSendingData = False

        return {"tput": tput, "execution_time": execution_time}

    def receive_file(self, filename, filesize):
        logging.debug(f"Receiving file '{filename}'")
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

    def set_data_link(self, dataLink : TCPConnection):
        self.dataLink = dataLink
        self.dataLink.parent = self
        self.dataLink.onConnectionClosed.subscribe(self.onConnectionClosed)

    def get_data_link(self):
        return self.dataLink
    
    def set_control_link(self, controlLink : TCPConnection):
        self.controlLink = controlLink
        self.controlLink.parent = self

    def get_control_link(self):
        return self.controlLink
    
    def identify(self, ircNick):
        self.dataLink.send_command(f"IDENTIFY {ircNick}")
        pass

    async def onConnectionClosed(self, *args, **kwargs):
        self.isActive = False


class TCPServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.onConnectionRegistered = event.Event()

    async def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        logging.info(f"TCP Server started on {self.host}:{self.port}")

    async def listen_step(self, delay):
        await asyncio.sleep(delay)
        self.server_socket.settimeout(1)
        try:
            client_socket, client_address = self.server_socket.accept()
            client_socket.settimeout(5)
            logging.info(f"New TCP connection from {client_address[0]}:{client_address[1]}")
            tcp_connection = TCPConnection(client_socket, TCPConnection.LinkType.DATA)
            tcp_connection.onConnectionClosed.subscribe(self.tcpConnection_onConnectionClosed)
            tcp_connection.onIdentifyCommandReceived.subscribe(self.tpcConnection_onIdentifyCommandReceived)
            self.clients.append(tcp_connection)
            tcp_connection.start()
        except socket.timeout:
            return

    async def listen(self, delay):
        logging.info("Listening for incoming TCP connections")
        while True:
            await self.listen_step(delay)

    async def tcpConnection_onConnectionClosed(self, *args, **kwargs):
        connection = args[0]
        info = connection.get_socket_info()
        logging.info(f"TCP connection {info[0]}:{info[1]} closed")
        self.clients.remove(connection)

    async def tpcConnection_onIdentifyCommandReceived(self, *args, **kwargs):
        connection = args[0]
        sender = kwargs.get("sender")
        await self.onConnectionRegistered.notify(self, connection=connection, sender=sender)
    

class TCPClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def __connect(self):
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

    async def connect(self):
        data_link_socket = await self.__connect()

        if data_link_socket is None:
            return None 
        
        tcp_connection = TCPConnection(data_link_socket, TCPConnection.LinkType.DATA)
        tcp_connection.start()

        tcpSession = TCPSession()
        tcpSession.set_data_link(tcp_connection)
        tcpSession.isActive = True

        return tcpSession