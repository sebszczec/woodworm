from botnet.tcp import tcp_services
import socket
import asyncio

PATH = 'home/slaugh/Downloads/d2'

async def start_server():
    host = socket.gethostbyname(socket.gethostname())
    port = 1234

    server = tcp_services.TCPServer(host, port)
    await server.start()
    await server.listen(0.0)

if __name__ == "__main__":
    asyncio.run(start_server())

    