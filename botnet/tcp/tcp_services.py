import socket
import threading
import os
import asyncio
from log import logger


class TCPConnection:
    def __init__(self, socket) -> None:
        self.socket = socket

    def start(self):
        connection_thread = threading.Thread(target=self.handle_data)
        connection_thread.start()

    def handle_data(self):
        while True:
            try:
                data = self.socket.recv(1024).decode()
            except socket.timeout:
                continue
            except ConnectionResetError:
                break

            if not data:
                continue

            # Handle received data
            if data.startswith("FILE"):
                filename = data.split()[1]
                self.receive_file(self.socket, filename)
            else:
                # Handle other commands
                self.handle_command(self.socket, data)

        self.socket.close()
        # self.clients.remove(client_socket) # place to raise an event

    def send_command(self, command):
        self.socket.send(command.encode())

    def handle_command(self, command):
        # Handle the command here
        self.syslog.log(f"Received command '{command}' from {self.socket.getpeername()[0]}")

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

    def close(self):
        self.socket.close()

class TCPServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.syslog = logger.Logger()

    async def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.syslog.log(f"TCP Server started on {self.host}:{self.port}")

    async def listen_step(self):
        await asyncio.sleep(0.1)
        self.server_socket.settimeout(0.1)
        try:
            client_socket, client_address = self.server_socket.accept()
            self.syslog.log(f"New TCP connection from {client_address[0]}:{client_address[1]}")
            tcp_connection = TCPConnection(client_socket)
            self.clients.append(tcp_connection) 
            tcp_connection.start()
        except socket.timeout:
            return

    async def listen(self):
        self.syslog.log("Listening for incoming TCP connections")
        while True:
            await self.listen_step()
    

class TCPClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = None
        self.tcp_connection = None
        self.syslog = logger.Logger()

    def connect(self):
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
        
        self.tcp_connection = TCPConnection(self.client_socket)
        self.tcp_connection.start()
        return True

    def get_tcp_connection(self):
        return self.tcp_connection