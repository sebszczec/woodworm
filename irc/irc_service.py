import socket
from ..log import logger

class IRCConnection:
    def __init__(self, server, port, nickname, channel):
        self.server = server
        self.port = port
        self.nickname = nickname
        self.channel = channel
        self.IRC = None

    def connect(self):
        self.IRC = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.IRC.connect((self.server, self.port))

    def send_data(self, command):
        self.IRC.send(bytes(command + "\n", "UTF-8"))

    def listener(self):
        self.send_data(f'USER {self.nickname} slaugh.pl slaugh.pl :{self.nickname}')
        self.send_data(f'NICK {self.nickname}')
        while True:
            ircmsg = self.IRC.recv(2048).decode("UTF-8")
            ircmsg = ircmsg.strip('\r\n')
            if "PRIVMSG" in ircmsg:
                name = ircmsg.split('!', 1)[0][1:]
                message = ircmsg.split('PRIVMSG', 1)[1].split(':', 1)[1]
                logger.log(f"Name: {name}, Message: {message}")
            if ircmsg.startswith("PING :"):
                logger.log("Pinged!")
                self.IRC.send(bytes("PONG :pingisn", "UTF-8"))
            else:
                logger.log(ircmsg)



