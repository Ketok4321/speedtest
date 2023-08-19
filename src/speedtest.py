import os
import asyncio
import time
import aiohttp
import io

from urllib.parse import urljoin

DOWNLOAD_SIZE = 100
UPLOAD_SIZE = 10

HEADERS = {
    "Accept-Encoding": "identity",
    "User-Agent": "ketok-speedtest/dev",
}

garbage = os.urandom(UPLOAD_SIZE * 1000 * 1000)

class Server:
    def __init__(self, name, server, pingURL, dlURL, ulURL, **_):
        if not (server.startswith("https:") or server.startswith("http:")):
            server = "https:" + server
        
        self.name = name
        self.server = server
        self.pingURL = urljoin(server + "/", pingURL)
        self.downloadURL = urljoin(server + "/", dlURL)
        self.uploadURL = urljoin(server + "/", ulURL)

async def get_servers(): #TODO: do this in the background
    async with aiohttp.ClientSession() as session:
        async with session.get("https://librespeed.org/backend-servers/servers.php") as response:
            servers = await response.json()
            servers = list(map(lambda x: Server(**x), servers))    

            await asyncio.gather(*[check_server(s) for s in servers])

            servers = list(filter(lambda s: s.ping != -1, servers))
            
            servers.sort(key=lambda s: s.ping)

            return servers

class GarbageReader(io.IOBase):
    def __init__(self, read_callback=None):
        self.__read_callback = read_callback
        super().__init__()
        self.length = len(garbage)
        self.pos = 0

    def seekable(self):
        return True

    def writable(self):
        return False

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def read(self, size=None):
        if not size:
            size = self.length - self.tell()

        old_pos = self.tell()
        self.pos = old_pos + size

        if self.__read_callback:
            self.__read_callback(size)

        return garbage[old_pos:self.pos]

async def check_server(server):
    async with aiohttp.ClientSession() as session:
        try:
            start = time.time()
            task = asyncio.create_task(session.get(server.pingURL))

            while not task.done():
                if time.time() - start > 0.75:
                    task.cancel()
                    server.ping = -1
                    return
                await asyncio.sleep(0)
            
            task.result().close()
            server.ping = time.time() - start
            return
        except aiohttp.ClientError:
            server.ping = -1
            return

async def ping(server): #TODO: jitter and other stuff
    async with aiohttp.ClientSession() as session:
        pings = []
        for i in range(10):
            start = time.time()
            async with session.get(server.pingURL, headers=HEADERS) as response:
                pings.append(time.time() - start)
    return sum(pings) / len(pings) * 1000

async def download(server, total):
    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(server.downloadURL + "?ckSize=" + str(DOWNLOAD_SIZE), headers=HEADERS) as response:
                async for data in response.content.iter_any():
                    total[0] += len(data)

async def upload(server, total):
    async with aiohttp.ClientSession() as session:
        while True:
            def callback(size):
                total[0] += size
            reader = GarbageReader(callback)
            async with session.post(server.uploadURL, headers=HEADERS, data=reader) as response:
                while reader.tell() < reader.length - 1:
                    await asyncio.sleep(0)
