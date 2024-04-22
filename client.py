from botnet.tcp import tcp_services
import socket
import asyncio
import os

PATH = '/home/slaugh/Downloads/d1'
FILENAME = "jeden.jpg"

async def start_client():
    host = socket.gethostbyname(socket.gethostname())
    port = 1234

    client = tcp_services.TCPClient(host, port)
    new_socket = await client.connect()

    file = os.path.join(PATH, FILENAME)
    new_socket.send_file(file)


if __name__ == "__main__":
    asyncio.run(start_client())