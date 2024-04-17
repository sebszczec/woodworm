import asyncio
from time import sleep
from irc import irc_service
from log import logger


async def irc_onConnected(*args, **kwargs):
    irc_connection = args[0]
    irc_connection.join_channel()

async def main():
    syslog = logger.Logger()

    irc_connection = irc_service.IRCConnection('slaugh.pl', 2000, 'woodworm', '#vorest')
    irc_connection.onConnected.subscribe(irc_onConnected)

    irc_connection.connect()
    irc_connection.register_user()
    
    while True:
        await irc_connection.listener()
        await asyncio.sleep(1)
        syslog.log("I'm still alive!", level=logger.LogLevel.DEBUG)
        

if __name__ == "__main__":
    asyncio.run(main())
