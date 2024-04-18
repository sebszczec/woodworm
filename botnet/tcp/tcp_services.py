import socket
import threading
import os
import asyncio
from log import logger

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
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()
        except socket.timeout:
            return

    async def listen(self):
        self.syslog.log("Listening for incoming TCP connections")
        while True:
            await self.listen_step()

    def handle_client(self, client_socket):
        self.clients.append(client_socket)

        while True:
            try:
                data = client_socket.recv(1024).decode()
                if not data:
                    break

                # Handle received data
                if data.startswith("SEND_FILE"):
                    filename = data.split()[1]
                    self.receive_file(client_socket, filename)
                elif data.startswith("RECEIVE_FILE"):
                    filename = data.split()[1]
                    self.send_file(client_socket, filename)
                else:
                    # Handle other commands
                    self.handle_command(client_socket, data)

            except ConnectionResetError:
                break

        client_socket.close()
        self.clients.remove(client_socket)

    def receive_file(self, client_socket, filename):
        with open(filename, "wb") as file:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                file.write(data)

        self.syslog.log(f"Received file '{filename}' from {client_socket.getpeername()[0]}")

    def send_file(self, client_socket, filename):
        if not os.path.exists(filename):
            client_socket.send("FILE_NOT_FOUND".encode())
            return

        with open(filename, "rb") as file:
            for data in file:
                client_socket.send(data)

        self.syslog.log(f"Sent file '{filename}' to {client_socket.getpeername()[0]}")

    def handle_command(self, client_socket, command):
        # Handle the command here
        self.syslog.log(f"Received command '{command}' from {client_socket.getpeername()[0]}")


class TCPClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = None
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
        
        return True

    def send_command(self, command):
        self.client_socket.send(command.encode())

    def send_file(self, filename):
        self.client_socket.send(f"SEND_FILE {filename}".encode())
        with open(filename, "rb") as file:
            for data in file:
                self.client_socket.send(data)
        self.syslog.log(f"Sent file '{filename}' to {self.host}")

    def receive_file(self, filename):
        self.client_socket.send(f"RECEIVE_FILE {filename}".encode())
        response = self.client_socket.recv(1024).decode()
        if response == "FILE_NOT_FOUND":
            self.syslog.log(f"File '{filename}' not found on the server")
            return
        with open(filename, "wb") as file:
            while True:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                file.write(data)
        self.syslog.log(f"Received file '{filename}' from {self.host}")

    def close(self):
        self.client_socket.close()