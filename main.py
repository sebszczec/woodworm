import asyncio
import woodworm
import sys
import asyncio
import woodworm

if __name__ == "__main__":
    if __name__ == "__main__":
        if len(sys.argv) != 7:
            print("Usage: python main.py <pathToFiles> <ircNick> <channel> <domain> <ircServer> <ircServerPort>")
            sys.exit(1)

        pathToFiles = sys.argv[1]
        ircNick = sys.argv[2]
        channel = sys.argv[3]
        domain = sys.argv[4]
        ircServer = sys.argv[5]
        ircServerPort = int(sys.argv[6])

        worm = woodworm.Woodworm(pathToFiles, ircNick, channel, domain, ircServer, ircServerPort)
        asyncio.run(worm.start(debug=False))
