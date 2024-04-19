import socket
import threading
import os
import asyncio
from log import logger
from tools import event

class TCPConnection:
    def __init__(self, socket) -> None:
        self.syslog = logger.Logger()
        self.socket = socket
        self.socketInfo = self.socket.getpeername()
        self.onConnectionClosed = event.Event()
        self.onIdentifyCommandReceived = event.Event()

    async def start(self):
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
                filename = data.split()[1]
                self.receive_file(self.socket, filename)
            else:
                # Handle other commands
                self.handle_command(data)
        
        self.socket.close()
        asyncio.run(self.onConnectionClosed.notify(self))

    def send_command(self, command):
        self.socket.send(command.encode())

    def handle_command(self, command):
        # Handle the command here
        self.syslog.log(f"Received TCP command '{command}' from {self.socket.getpeername()[0]}")
        nick = command.split()[1]
        asyncio.run(self.onIdentifyCommandReceived.notify(self, sender=nick))

    def send_file(self, filename):
        self.socket.send(f"FILE {filename}".encode())
        with open(filename, "rb") as file:
            for data in file:
                self.socket.send(data)
        self.syslog.log(f"Sent file '{filename}' to {self.host}")

    def receive_file(self, filename):
        with open(filename, "wb") as file:
            while True:
                data = self.socket.recv(1024)
                if not data:
                    break
                file.write(data)
        self.syslog.log(f"Received file '{filename}' from {self.host}")

    def get_socket_info(self):
        return self.socketInfo

    def close(self):
        self.socket.close()


class TCPServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.syslog = logger.Logger()
        self.onConnectionRegistered = event.Event()

    async def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.syslog.log(f"TCP Server started on {self.host}:{self.port}")

    async def listen_step(self, delay):
        await asyncio.sleep(delay)
        self.server_socket.settimeout(0.1)
        try:
            client_socket, client_address = self.server_socket.accept()
            self.syslog.log(f"New TCP connection from {client_address[0]}:{client_address[1]}")
            tcp_connection = TCPConnection(client_socket)
            tcp_connection.onConnectionClosed.subscribe(self.tcpConnection_onConnectionClosed)
            tcp_connection.onIdentifyCommandReceived.subscribe(self.tpcConnection_onIdentifyCommandReceived)
            self.clients.append(tcp_connection)
            await tcp_connection.start()
        except socket.timeout:
            return

    async def listen(self, delay):
        self.syslog.log("Listening for incoming TCP connections")
        while True:
            await self.listen_step(delay)

    async def tcpConnection_onConnectionClosed(self, *args, **kwargs):
        connection = args[0]
        info = connection.get_socket_info()
        self.syslog.log(f"TCP connection {info[0]}:{info[1]} closed")
        self.clients.remove(connection)

    async def tpcConnection_onIdentifyCommandReceived(self, *args, **kwargs):
        connection = args[0]
        sender = kwargs.get("sender")
        await self.onConnectionRegistered.notify(self, connection=connection, sender=sender)
    

class TCPClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = None
        self.syslog = logger.Logger()

    async def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(1)
        try:
            self.client_socket.connect((self.host, int(self.port)))
            self.syslog.log(f"TCP Connected to {self.host}:{self.port}")
        except ConnectionRefusedError:
            self.syslog.log(f"TCP Connection to {self.host}:{self.port} refused")
            return False
        except socket.timeout:
            self.syslog.log(f"TCP Connection to {self.host}:{self.port} timed out")
            return False
        
        tcp_connection = TCPConnection(self.client_socket)
        await tcp_connection.start()
        return tcp_connection
