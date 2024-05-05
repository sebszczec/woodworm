import requests
import logging
import time
from tools import event

class FileDownloader:
    def __init__(self, url):
        self.url = url
        self.onDownloadCompleted = event.Event()
        self.onDownloadProgress = event.Event()


    def download_file(self, **kwargs):
        start_time = time.time()
        try:
            response = requests.get(self.url, stream=True)
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to download {self.url} file. {str(e)}")
            return
        size = 0

        if response.status_code == 200:
            source_size = int(response.headers.get('Content-Length', 0))
            full_size = round(source_size / 1024 / 1024, 2)
            trackProgress = False
            divider = 0
            
            if source_size >= 104857600: # 100MB
                trackProgress = True
                divider = source_size / 10

            savePath = kwargs.get('savePath')

            with open(savePath, 'wb') as file:
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
                        
                        self.onDownloadProgress.notify(filename=self.url, progress=progress, tput=tput, progress_size=progress_size, full_size=full_size, **kwargs)
                        divider += source_size / 10
            
            end_time = time.time()
            execution_time = end_time - start_time
            tput = source_size / 1024 / 1024 / execution_time

            execution_time = round(execution_time, 2)
            tput = round(tput, 2)

            logging.info(f"File {self.url} downloaded successfully. Size: {size} MB, Time: {execution_time} s, Throughput: {tput} MB/s")
            self.onDownloadCompleted.notify(filename=self.url, filesize = full_size, tput = tput, time = execution_time, **kwargs)
            return
        
        logging.error(f"Failed to download {self.url} file.")
