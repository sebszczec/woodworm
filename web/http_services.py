import requests
import logging
import time
import asyncio
from tools import event

class FileDownloader:
    def __init__(self, url, owner):
        self.url = url
        self.owner = owner
        self.onDownloadCompeted = event.Event()


    def download_file(self, save_path):
        start_time = time.time()
        response = requests.get(self.url, stream=True)
        size = 0

        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
                    size = size + len(chunk)
            
            end_time = time.time()
            execution_time = end_time - start_time
            tput = size / 1024 / 1024 / execution_time

            logging.info(f"File {self.url} downloaded successfully. Size: {size}, Time: {execution_time}, Throughput: {tput} MB/s")
            asyncio.run(self.onDownloadCompeted.notify(owner = self.owner, filename=self.url, filesize = size, tput = tput, time = execution_time))
            return
        
        logging.error(f"Failed to download {self.url} file.")