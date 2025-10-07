import socket
from time import sleep
from tools import event
import logging

class IRCConnection:

    def __init__(self, server, domain, port, nickname, channel):
        self.server = server
        self.domain = domain
        self.port = port
        self.nickname = nickname
        self.channel = channel
        self.IRC = None
        self.MSG_LEN = 2048
        self.isConnected = False
        self.isLooped = False
        self.onConnected = event.Event()
        self.onBroadcastRequested = event.Event()
        self.onSpreadDetected = event.Event()
        self.onSomeoneLeftChannel = event.Event()
        self.onCommandLS = event.Event()
        self.onCommandSTAT = event.Event()
        self.onCommandSEND = event.Event()
        self.onCommandHELP = event.Event()
        self.onCommandSTATUS = event.Event()
        self.onCommandWGET = event.Event()
        self.onCommandSHUTDOWN = event.Event()
        self.onCommandFILES = event.Event()


    def connect(self):
        logging.info(f"Connecting to {self.server}:{self.port}")
        self.IRC = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.IRC.connect((self.server, self.port))
        self.isLooped = True
        logging.info("Connected to IRC server")

    def stop(self):
        self.send_data("QUIT")
        self.isConnected = False
        self.isLooped = False
        self.IRC.close()
        self.IRC = None

        logging.info("IRC connection closed")

    def is_connected(self):
        if self.IRC is None:
            return False
        
        return self.isConnected
            

    def register_user(self):        
        self.send_data(f'USER {self.nickname} {self.domain} {self.domain} :{self.nickname}')
        self.send_data(f'NICK {self.nickname}')


    def join_channel(self):        
        self.send_data(f'JOIN {self.channel}')


    def send_data(self, command):
        self.IRC.send(bytes(command + "\r\n", "UTF-8"))


    def send_message(self, message):
        if self.is_connected() is False:
            return
        
        self.send_data(f'PRIVMSG {self.channel} :{message}')

    
    def send_query(self, nickname, message):
        if self.is_connected() is False:
            return
        
        self.send_data(f'PRIVMSG {nickname} :{message}')


    def listen_step(self, delay):
        sleep(delay)
            
        self.IRC.settimeout(0.1)
        try:
            received = self.IRC.recv(self.MSG_LEN).decode("UTF-8")
        except socket.timeout:
            return

        if len(received) == 0:
            return

        received = received.strip('\r\n')
        buffer = received.split("\r\n")
        
        for ircmsg in buffer:
            if ircmsg.startswith("PING :"):
                self.handle_ping()
                continue
            
            if self.isConnected is False and ("End of /MOTD command" in ircmsg or "376" in ircmsg):
                self.isConnected = True
                self.onConnected.notify(self)
                continue

            if self.handle_channel_commands(ircmsg):
                continue

            if "PRIVMSG" in ircmsg:
                self.handle_priv_message(ircmsg)
                continue

            logging.info(ircmsg)
            

    def listen(self, delay):
        while self.isLooped is True:
            self.listen_step(delay)


    def handle_channel_commands(self, ircmsg):
        if "PING" in ircmsg:
            self.handle_ping()
            return True

        if "BROADCAST" in ircmsg:
            self.handle_broadcast_request()
            return True

        if "SPREAD" in ircmsg:
            self.handle_spread_detected(ircmsg)
            return True

        if "PART" in ircmsg or "QUIT" in ircmsg:
            self.handle_part(ircmsg)
            return True

        if "JOIN" in ircmsg:
            self.handle_join()
            return True
        
        return False


    def handle_ping(self):
        self.send_data("PONG :pingisn")
        logging.info("PONG :pingisn")


    def handle_broadcast_request(self):
        self.onBroadcastRequested.notify(self)


    def handle_spread_detected(self, ircmsg):
        logging.debug(f"{ircmsg}")
        try:
            ip = ircmsg.split("ip:")[1].split(" ")[0]
            port = ircmsg.split("port:")[1].split()[0].strip('\r\n')

            ircNick = ircmsg.split('!', 1)[0][1:]
        except:
            logging.error("Error parsing SPREAD message")
            return

        self.onSpreadDetected.notify(self, ip = ip, port = port, ircNick = ircNick)


    def handle_part(self, ircmsg):
        ircNick = ircmsg.split('!', 1)[0][1:]
        self.onSomeoneLeftChannel.notify(self, ircNick = ircNick)


    def handle_join(self):
        logging.debug("JOIN detected, sending BROADCAST")
        self.send_message("BROADCAST")


    def handle_priv_message(self, ircmsg):
        nickname = ircmsg.split('!', 1)[0][1:]
        message = ircmsg.split('PRIVMSG', 1)[1].split(':', 1)[1]
        self.handle_priv_command(nickname, message)
        # logging.debug(f"Name: {nickname}, Message: {message}")

    
    def handle_priv_command(self, nickname, command):
        if "HELP" in command:
            self.onCommandHELP.notify(self, nickname=nickname)
            return
        
        if "LS" in command:
            self.onCommandLS.notify(self, nickname=nickname)
            return
        
        if "SEND" in command:
            try:
                receiver = command.split('SEND', 1)[1].split(' ', 2)[1]
                filename = command.split('SEND', 1)[1].split(' ', 2)[2]
            except:
                logging.error("Error parsing SEND command")
                return
            
            logging.info(f"SEND command received: {filename} to {receiver}")
            self.onCommandSEND.notify(self, filename=filename, receiver=receiver, nickname=nickname)
            return


        if "STATUS" in command:
            self.onCommandSTATUS.notify(self, nickname=nickname)
            return


        if "STAT" in command:
            try:
                filename = command.split('STAT', 1)[1].split(' ', 1)[1]
            except:
                logging.error("Error parsing STAT command")
                return
            self.onCommandSTAT.notify(self, filename=filename, nickname=nickname)
            return
        
        if "WGET" in command:
            try:
                url = command.split('WGET', 1)[1].split(' ', 1)[1]
            except:
                logging.error("Error parsing WGET command")
                return
            self.onCommandWGET.notify(self, url=url, nickname=nickname)
            return
        
        if "SHUTDOWN" in command:
            self.onCommandSHUTDOWN.notify(self, nickname=nickname)
            return
        
        if "FILES" in command:
            try:
                command = command.split('FILES ', 1)[1]
            except Exception as e:
                logging.error(f"Error while handling FILES command: {e}")
                return
            files = command
            self.onCommandFILES.notify(self, nickname=nickname, files=files)
            return
        
        #logging.warning(f"Unknown command: {command} from {nickname}")



