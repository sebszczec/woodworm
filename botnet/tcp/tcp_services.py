import socket
import threading
import os

class TCPServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server started on {self.host}:{self.port}")

        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"New connection from {client_address[0]}:{client_address[1]}")
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

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

        print(f"Received file '{filename}' from {client_socket.getpeername()[0]}")

    def send_file(self, client_socket, filename):
        if not os.path.exists(filename):
            client_socket.send("FILE_NOT_FOUND".encode())
            return

        with open(filename, "rb") as file:
            for data in file:
                client_socket.send(data)

        print(f"Sent file '{filename}' to {client_socket.getpeername()[0]}")

    def handle_command(self, client_socket, command):
        # Handle the command here
        print(f"Received command '{command}' from {client_socket.getpeername()[0]}")


class TCPClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = None

    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        print(f"Connected to {self.host}:{self.port}")

    def send_command(self, command):
        self.client_socket.send(command.encode())

    def send_file(self, filename):
        self.client_socket.send(f"SEND_FILE {filename}".encode())
        with open(filename, "rb") as file:
            for data in file:
                self.client_socket.send(data)
        print(f"Sent file '{filename}' to {self.host}")

    def receive_file(self, filename):
        self.client_socket.send(f"RECEIVE_FILE {filename}".encode())
        response = self.client_socket.recv(1024).decode()
        if response == "FILE_NOT_FOUND":
            print(f"File '{filename}' not found on the server")
            return
        with open(filename, "wb") as file:
            while True:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                file.write(data)
        print(f"Received file '{filename}' from {self.host}")

    def close(self):
        self.client_socket.close()