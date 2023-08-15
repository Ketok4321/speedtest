import os
import asyncio
import time
import aiohttp
import io

CHUNK_SIZE = 100 # in mb?
UPLOAD_SIZE = 1024 # in KiB
REQUEST_COUNT = 3
MAX_DURATION = 15

garbage = os.urandom(UPLOAD_SIZE * 1024)

url = "https://speedtest.kamilszczepanski.com"
headers = {
    "User-Agent": "ketok-speedtest/dev",
    "Accept-Encoding": "identity",
}

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

async def ping(): #TODO: jitter and other stuff
    async with aiohttp.ClientSession() as session:
        pings = []
        for i in range(10):
            start = time.time()
            async with session.get(url + "/empty.php", headers=headers) as response:
                pings.append(time.time() - start)
    return sum(pings) / len(pings) * 1000

async def download(total):
    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(url + "/garbage.php?ckSize=" + str(CHUNK_SIZE), headers=headers) as response:
                async for data in response.content.iter_any():
                    total[0] += len(data)

async def upload(total):
    async with aiohttp.ClientSession() as session:
        while True:
            def callback(size):
                total[0] += size
            reader = GarbageReader(callback)
            async with session.post(url + "/empty.php", headers=headers, data=reader) as response:
                while reader.tell() < reader.length - 1:
                    await asyncio.sleep(0)

async def perform_test(test, callback, interval):
    total = [0]

    start_time = time.time()

    tasks = []

    for i in range(REQUEST_COUNT):
        tasks.append(asyncio.create_task(test(total)))
        await asyncio.sleep(0.3) # speedtest-go uses 200, the website uses 300

    while True: # if done, do it again until MAX_DURATION
        elapsed_time = time.time() - start_time
        if elapsed_time >= MAX_DURATION:
            for t in tasks: t.cancel()
            break

        speed = total[0] / elapsed_time
        callback(speed)
        await asyncio.sleep(interval)
