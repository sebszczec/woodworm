import asyncio
import woodworm

if __name__ == "__main__":
    pathToFiles = "/home/slaugh/Downloads"
    ircNick = "woodworm"
    channel = "#vorest"
    domain = "slaugh.pl"
    ircServerPort = 2000
    worm = woodworm.Woodworm(pathToFiles, ircNick, channel, domain, ircServerPort)
    asyncio.run(worm.start()) 