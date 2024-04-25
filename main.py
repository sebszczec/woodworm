import asyncio
import woodworm
import sys
import asyncio
import woodworm
import logging
import json

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
    with open('config.json') as f:
        config = json.load(f)

    pathToFiles = config['general']['pathToFiles']
    ircNick = config['irc']['nick']
    channel = config['irc']['channel']
    domain = config['irc']['domain']
    ircServer = config['irc']['server']
    ircServerPort = int(config['irc']['port'])
    tcpPort = int(config['general']['tcpPort'])

    ftpPort = int(config['ftp']['port'])
    ftpUser = config['ftp']['user']
    ftpPassword = config['ftp']['password']
    ftpPassiveRange = range(int(config['ftp']['passiveRangeStart']), int(config['ftp']['passiveRangeStop']))

    
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter())
    logger.removeHandler(logger.handlers[0])
    logger.addHandler(handler)

    worm = woodworm.Woodworm(config)
    asyncio.run(worm.start(debug=False))
    
