import requests
import logging
import time
from tools import event

class FileDownloader:
    def __init__(self, url):
        self.url = url
        self.onDownloadCompleted = event.Event()
        self.onDownloadProgress = event.Event()


    def download_file(self, savePath, **kwargs):
        start_time = time.time()
        progress_start_time = start_time
        last_progress_size = 0
        try:
            response = requests.get(self.url, stream=True)
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to download {self.url} file. {str(e)}")
            return
        size = 0

        if response.status_code == 200:
            source_size = int(response.headers.get('Content-Length', 0))
            full_size = source_size / 1024 / 1024
            trackProgress = False
            divider = 0
            progress_step = 0
            
            if source_size >= 104857600: # 100MB
                trackProgress = True
                divider = source_size / 10
                progress_step = divider

            with open(savePath, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
                    size = size + len(chunk)

                    if trackProgress and size >= divider:
                        progress = int((size / source_size) * 100)
                        tmpSize = size / 1024 / 1024
                        end_time = time.time()
                        execution_time = end_time - progress_start_time
                        progress_size = tmpSize - last_progress_size

                        progress_start_time = end_time
                        last_progress_size = tmpSize
                        
                        tput = progress_size / execution_time   
                        tput = round(tput, 2)
                        progress_size = round(progress_size, 2)   
                        
                        self.onDownloadProgress.notify(filename=self.url, progress=progress, tput=tput, progress_size=round(tmpSize, 2), full_size=round(full_size, 2), **kwargs)
                        divider += progress_step
            
            end_time = time.time()
            execution_time = end_time - start_time
            tput = full_size / execution_time

            execution_time = round(execution_time, 2)
            tput = round(tput, 2)

            logging.info(f"File {self.url} downloaded successfully. Size: {size} MB, Time: {execution_time} s, Throughput: {tput} MB/s")
            self.onDownloadCompleted.notify(filename=self.url, filesize = round(full_size, 2), tput = tput, time = execution_time, **kwargs)
            return
        
        logging.error(f"Failed to download {self.url} file.")
