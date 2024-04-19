import asyncio
import woodworm
import sys
import asyncio
import woodworm

if __name__ == "__main__":
    if len(sys.argv) != 8:
        print("Usage: python main.py <pathToFiles> <ircNick> <channel> <domain> <ircServer> <ircServerPort> <tcpPort>")
        print (f"{len(sys.argv)}")
        sys.exit(1)

    pathToFiles = sys.argv[1]
    ircNick = sys.argv[2]
    channel = sys.argv[3]
    domain = sys.argv[4]
    ircServer = sys.argv[5]
    ircServerPort = int(sys.argv[6])
    tcpPort = int(sys.argv[7])

    worm = woodworm.Woodworm(pathToFiles, ircNick, channel, domain, ircServer, ircServerPort, tcpPort)
    asyncio.run(worm.start(debug=False))
