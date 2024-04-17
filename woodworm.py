import asyncio
from time import sleep
from irc import irc_service
from log import logger

syslog = logger.Logger()

async def irc_onConnected(*args, **kwargs):
    irc_connection = args[0]
    await irc_connection.join_channel()

async def another_loop():
    while True:
        await asyncio.sleep(1)
        syslog.log("I'm still alive!", level=logger.LogLevel.DEBUG) 

async def main():
    irc_connection = irc_service.IRCConnection('slaugh.pl', 'slaugh.pl', 2000, 'woodworm', '#vorest')
    irc_connection.onConnected.subscribe(irc_onConnected)

    await irc_connection.connect()
    await irc_connection.register_user()
    
    async with asyncio.TaskGroup() as tg:
        tg.create_task(irc_connection.listen())
        tg.create_task(another_loop())
        

if __name__ == "__main__":
    asyncio.run(main())
