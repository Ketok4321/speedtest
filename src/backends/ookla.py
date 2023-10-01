import time
import asyncio
import aiohttp
import websockets

from urllib.parse import urljoin

from ..garbage import GarbageReader

DOWNLOAD_SIZE = 100

DURATION = 15
DL_STREAMS = 6
UP_STREAMS = 3

class OoklaServer:
    def __init__(self, country, name, sponsor, url, host, **_):
        self.name = f"{country}, {name} ({sponsor})"
        self.host = host
        self.uploadURL = url
        self.downloadURL = urljoin(url, "download")

class OoklaBackend:
    def __init__(self, user_agent):
        self.headers = {
            "Accept-Encoding": "identity",
            "User-Agent": user_agent,
        }

    async def get_servers(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.speedtest.net/api/js/servers?limit=20&https_functional=true") as response:
                servers = await response.json()
                servers = list(map(lambda x: OoklaServer(**x), servers))

                return servers
    
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
        def parse(response):
            response = response.split(" ")
            return int(response[1])

        async with websockets.connect('wss://' + server.host + "/ws?") as websocket:
            pings = []
            jitters = []
            
            await websocket.send("PING ")
            response = await websocket.recv()
            start = time.time()
            offset = parse(response)

            for i in range(10):
                await websocket.send(f"PING {round((time.time() - start) * 1000)}")
                response = await websocket.recv()
                pings.append(parse(response) - offset)
                offset = parse(response)
                if i != 0:
                    jitters.append(abs(pings[i] - pings[i - 1]))
            
            return sum(pings) / len(pings), sum(jitters) / len(jitters)
    
    async def download(self, server, res):
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(server.downloadURL + "?size=" + str(DOWNLOAD_SIZE * 1_000_000), headers=self.headers) as response:
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
