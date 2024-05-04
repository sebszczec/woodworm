from web import http_services
import asyncio
import logging
import os

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

async def downloader_onDownloadCompleted(*args, **kwargs):
    nickname = kwargs.get('owner')
    filename = kwargs.get('filename')
    filesize = kwargs.get('filesize')
    tput = kwargs.get('tput')
    time = kwargs.get('time')
    logging.info(f"File {filename} downloaded successfully. Size: {filesize} MB, Time: {time} s, Throughput: {tput} MB/s")


async def downloader_onDownloadProgress(*args, **kwargs):
    nickname = kwargs.get('owner')
    filename = kwargs.get('filename')
    progress = kwargs.get('progress')
    tput = kwargs.get('tput')
    progress_size = kwargs.get('progress_size')
    full_size = kwargs.get('full_size')
    logging.info(f"Downloading {filename}: {progress}%, {progress_size} out of {full_size} MB, Throughput: {tput} MB/s")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter())
    logger.removeHandler(logger.handlers[0])
    logger.addHandler(handler)


    url = 'http://ipv4.download.thinkbroadband.com/1GB.zip'
    filename = url.split('/')[-1]
    path = '/home/slaugh/Downloads/d1'
    savePath = os.path.join(path, filename)

    downloader = http_services.FileDownloader("Fdsfsd", "me")
    downloader.onDownloadCompleted.subscribe(downloader_onDownloadCompleted)
    downloader.onDownloadProgress.subscribe(downloader_onDownloadProgress)
    downloader.download_file(savePath)
                
    pass