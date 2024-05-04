import aiohttp
import asyncio
import logging

class FileDownloader:
    def __init__(self, url):
        self.url = url

    async def download_file(self, save_path):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                if response.status == 200:
                    with open(save_path, 'wb') as file:
                        while True:
                            chunk = await response.content.read(1024)
                            if not chunk:
                                break
                            file.write(chunk)
                    logging.info(f"File {self.url} downloaded successfully.")
                else:
                    logging.error(f"Failed to download {self.url} file.")

# # Example usage
# async def main():
#     downloader = FileDownloader('https://example.com/file.txt')
#     await downloader.download_file('/path/to/save/file.txt')

# asyncio.run(main())