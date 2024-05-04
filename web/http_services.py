import requests
import logging
import time
import asyncio
from tools import event

class FileDownloader:
    def __init__(self, url, owner):
        self.url = url
        self.owner = owner
        self.onDownloadCompleted = event.Event()
        self.onDownloadProgress = event.Event()


    def download_file(self, save_path):
        start_time = time.time()
        try:
            response = requests.get(self.url, stream=True)
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to download {self.url} file. {str(e)}")
            return
        size = 0

        if response.status_code == 200:
            source_size = int(response.headers.get('Content-Length', 0))
            trackProgress = False
            divider = 0
            
            if source_size >= 104857600: # 100MB
                trackProgress = True
                divider = source_size / 10


            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
                    size = size + len(chunk)
                    if trackProgress and size >= divider:
                        progress = int((size / source_size) * 100)
                        end_time = time.time()
                        execution_time = end_time - start_time
                        progress_size = size / 1024 / 1024
                        tput = progress_size / execution_time
                        tput = round(tput, 2)
                        progress_size = round(progress_size, 2)
                        full_size = round(source_size / 1024 / 1024, 2)

                        asyncio.run(self.onDownloadProgress.notify(owner=self.owner, filename=self.url, progress=progress, tput=tput, progress_size=progress_size, full_size=full_size))
                        divider += source_size / 10
            
            end_time = time.time()
            execution_time = end_time - start_time
            size = size / 1024 / 1024
            tput = size/ execution_time

            size = round(size, 2)
            execution_time = round(execution_time, 2)
            tput = round(tput, 2)

            logging.info(f"File {self.url} downloaded successfully. Size: {size} MB, Time: {execution_time} s, Throughput: {tput} MB/s")
            asyncio.run(self.onDownloadCompleted.notify(owner = self.owner, filename=self.url, filesize = size, tput = tput, time = execution_time))
            return
        
        logging.error(f"Failed to download {self.url} file.")
