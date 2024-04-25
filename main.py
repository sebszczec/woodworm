import asyncio
import woodworm
import sys
import asyncio
import woodworm
import logging

class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    green = "\x1b[32;20m"
    reset = "\x1b[0m"
    format = "%(asctime)s %(levelname)s: %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

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

    
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter())
    logger.removeHandler(logger.handlers[0])
    logger.addHandler(handler)

    worm = woodworm.Woodworm(pathToFiles, ircNick, channel, domain, ircServer, ircServerPort, tcpPort)
    asyncio.run(worm.start(debug=False))
    
