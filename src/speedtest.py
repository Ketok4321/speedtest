import os
import asyncio
import time
import aiohttp
import io

from urllib.parse import urljoin

DOWNLOAD_SIZE = 100
UPLOAD_SIZE = 20

HEADERS = {
    "Accept-Encoding": "identity",
    "User-Agent": "ketok-speedtest/dev",
}

garbage = os.urandom(UPLOAD_SIZE * 1000 * 1000)

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

class Server:
    def __init__(self, name, server, pingURL, dlURL, ulURL, **_):
        if not (server.startswith("https:") or server.startswith("http:")):
            server = "https:" + server
        
        self.name = name
        self.server = server
        self.pingURL = urljoin(server + "/", pingURL)
        self.downloadURL = urljoin(server + "/", dlURL)
        self.uploadURL = urljoin(server + "/", ulURL)

async def get_servers():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://librespeed.org/backend-servers/servers.php") as response:
            servers = await response.json()
            servers = list(map(lambda x: Server(**x), servers))    

            await asyncio.gather(*[check_server(s) for s in servers])

            servers = list(filter(lambda s: s.ping != -1, servers))
            
            servers.sort(key=lambda s: s.ping)

            return servers

async def check_server(server):
    async with aiohttp.ClientSession() as session:
        try:
            start = time.time()
            async with session.get(server.pingURL, timeout=aiohttp.ClientTimeout(total=0.5)) as _:
                server.ping = time.time() - start
        except (aiohttp.ClientError, asyncio.TimeoutError):
            server.ping = -1

async def ping(server):
    async with aiohttp.ClientSession() as session:
        pings = []
        jitters = []
        for i in range(10):
            start = time.time()
            async with session.get(server.pingURL, headers=HEADERS) as _:
                pings.append(time.time() - start)
            
            if i != 0:
                jitters.append(abs(pings[i] - pings[i - 1]))
    return sum(pings) / len(pings) * 1000, sum(jitters) / len(jitters) * 1000

async def download(server, total):
    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(server.downloadURL + "?ckSize=" + str(DOWNLOAD_SIZE), headers=HEADERS) as response:
                async for data in response.content.iter_any():
                    total[0] += len(data)

async def upload(server, total):
    def callback(size):
        total[0] += size
    
    async with aiohttp.ClientSession() as session:
        while True:
            reader = GarbageReader(callback)
            async with session.post(server.uploadURL, headers=HEADERS, data=reader) as response:
                await response.read()
