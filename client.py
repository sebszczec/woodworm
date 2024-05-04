from web import http_services
import asyncio
import os


if __name__ == "__main__":
    url = 'http://ipv4.download.thinkbroadband.com/5MB.zip'
    filename = url.split('/')[-1]
    path = '/home/slaugh/Downloads/d1'
    savePath = os.path.join(path, filename)

    downloader = http_services.FileDownloader(url)
    asyncio.run(downloader.download_file(savePath))
                
    pass