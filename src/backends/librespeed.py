import time
import io
import os
import asyncio
import aiohttp

from urllib.parse import urljoin

DOWNLOAD_SIZE = 100
UPLOAD_SIZE = 20

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

class LibrespeedServer:
    def __init__(self, name, server, pingURL, dlURL, ulURL, **_):
        if not (server.startswith("https:") or server.startswith("http:")):
            server = "https:" + server
        
        self.name = name
        self.server = server
        self.pingURL = urljoin(server + "/", pingURL)
        self.downloadURL = urljoin(server + "/", dlURL)
        self.uploadURL = urljoin(server + "/", ulURL)

class LibrespeedBackend:
    def __init__(self, user_agent):
        self.headers = {
            "Accept-Encoding": "identity",
            "User-Agent": user_agent,
        }

    async def get_servers(self): #TODO: Change how this works to take more time on worse connections and less on better ones, while returning the same amount of servers in both cases
        async with aiohttp.ClientSession() as session:
            async def check_server(server):
                try:
                    start = time.time()
                    async with session.get(server.pingURL, timeout=aiohttp.ClientTimeout(total=0.75)) as _:
                        return time.time() - start
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    return -1
        
            async with session.get("https://librespeed.org/backend-servers/servers.php") as response:
                servers = await response.json()
                servers = list(map(lambda x: LibrespeedServer(**x), servers))    

                pings = await asyncio.gather(*[check_server(s) for s in servers])
                
                servers = list(zip(pings, servers))
                servers.sort(key=lambda t: t[0])
                servers = [s for p, s in servers if p != -1]

                return servers

    async def ping(self, server):
        async with aiohttp.ClientSession() as session:
            pings = []
            jitters = []
            for i in range(10):
                start = time.time()
                async with session.get(server.pingURL, headers=self.headers) as _:
                    pings.append(time.time() - start)
                
                if i != 0:
                    jitters.append(abs(pings[i] - pings[i - 1]))
        return sum(pings) / len(pings) * 1000, sum(jitters) / len(jitters) * 1000
    
    async def download(self, server, total):
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(server.downloadURL + "?ckSize=" + str(DOWNLOAD_SIZE), headers=self.headers) as response:
                    async for data in response.content.iter_any():
                        total[0] += len(data)

    async def upload(self, server, total):
        def callback(size):
            total[0] += size
        
        async with aiohttp.ClientSession() as session:
            while True:
                reader = GarbageReader(callback)
                async with session.post(server.uploadURL, headers=self.headers, data=reader) as response:
                    await response.read()
