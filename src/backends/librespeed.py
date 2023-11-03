import time
import asyncio
import aiohttp

from urllib.parse import urljoin

from ..garbage import GarbageReader

DOWNLOAD_SIZE = 100

DURATION = 15
DL_STREAMS = 6
UP_STREAMS = 3

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

    async def get_servers(self):
        async with aiohttp.ClientSession() as session:
            async def check_server(server, results):
                try:
                    async with session.get(server.pingURL, timeout=aiohttp.ClientTimeout(total=2.0)) as _:
                        results.append(server)
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    pass
        
            async with session.get("https://librespeed.org/backend-servers/servers.php") as response:
                servers = await response.json()
                servers = list(map(lambda x: LibrespeedServer(**x), servers))    

                results = []

                task = asyncio.gather(*[check_server(s, results) for s in servers])
                
                while len(results) < 15 and not task.done():
                    await asyncio.sleep(0)

                return results
    
    async def start(self, server, res, notify):
        async def perform_test(test, streams, res):
            tasks = []

            timeout = asyncio.create_task(asyncio.sleep(DURATION))

            for _ in range(streams):
                tasks.append(asyncio.create_task(test(server, res)))
                await asyncio.sleep(0.3)

            await timeout

            for t in tasks:
                t.cancel()

        res.ping, res.jitter = await self.ping(server)
        notify("ping")

        notify("download_start")
        await perform_test(self.download, DL_STREAMS, res)
        notify("download_end")

        notify("upload_start")
        await perform_test(self.upload, UP_STREAMS, res)
        notify("upload_end")

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
    
    async def download(self, server, res):
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(server.downloadURL + "?ckSize=" + str(DOWNLOAD_SIZE), headers=self.headers) as response:
                    async for data in response.content.iter_any():
                        res.total_dl += len(data)

    async def upload(self, server, res):
        def callback(size):
            res.total_up += size
        
        async with aiohttp.ClientSession() as session:
            while True:
                reader = GarbageReader(callback)
                async with session.post(server.uploadURL, headers=self.headers, data=reader) as response:
                    await response.read()
