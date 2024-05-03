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
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter())
    logger.removeHandler(logger.handlers[0])
    logger.addHandler(handler)

    if len(sys.argv) > 1:
        config_file = sys.argv[1]
        logger.info(f"Using custom config file: {config_file}")
    else:
        config_file = 'config.json'

    with open(config_file) as f:
        config = json.load(f)

    worm = woodworm.Woodworm(config)
    try:
        asyncio.run(worm.start(debug=False))   
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}")
        sys.exit(1)
    
