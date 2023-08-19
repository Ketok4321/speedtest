import threading
import asyncio
import gi
import time

from gi.repository import GLib

from .speedtest import ping, download, upload

DURATION = 15
REQUEST_COUNT = 3

class SpeedtestWorker(threading.Thread):
    def __init__(self, win, server):
        super().__init__(name="SpeedtestWorker", daemon=True)

        self.stop_event = threading.Event()
        self.win = win
        self.server = server

    def run(self):
        event_loop = asyncio.new_event_loop()

        event_loop.run_until_complete(self.run_async())

        event_loop.close()

    async def run_async(self):
        task = asyncio.create_task(self.do_run())

        while not task.done():
            if self.stop_event.is_set():
                task.cancel()
                break
            
            await asyncio.sleep(0)
        
        for task in asyncio.all_tasks():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def do_run(self):
        try:
            view = self.win.test_view

            _ping = await ping(self.server)

            GLib.idle_add(setattr, view, "ping", str(round(_ping)) + "ms")

            GLib.idle_add(view.progress.set_visible, True)

            view.progress.remove_css_class("up")
            view.progress.add_css_class("dl")
            self.start_time = time.time()
            self.total = [0]
            timeout = GLib.timeout_add(1000 / 30, lambda: self.update(view.download))
            await self.perform_test(download)
            GLib.source_remove(timeout)

            view.progress.remove_css_class("dl")
            view.progress.add_css_class("up")
            self.start_time = time.time()
            self.total = [0]
            timeout = GLib.timeout_add(1000 / 30, lambda: self.update(view.upload))
            await self.perform_test(upload)
            GLib.source_remove(timeout)

            GLib.idle_add(view.progress.set_visible, False)
        except Exception as e:
            print(e)
            GLib.idle_add(self.win.set_view, self.win.offline_view)
    
    def update(self, gauge):
        view = self.win.test_view

        current_duration = time.time() - self.start_time
        value = self.total[0] / current_duration

        if current_duration <= 1:
            return not self.stop_event.is_set()
        
        view.updateGauge(gauge, value)
        view.progress.set_fraction(current_duration / DURATION)

        return not self.stop_event.is_set()
    
    async def perform_test(self, test):
        tasks = []

        timeout = asyncio.create_task(asyncio.sleep(DURATION))

        for _ in range(REQUEST_COUNT):
            tasks.append(asyncio.create_task(test(self.server, self.total)))
            await asyncio.sleep(0.3)

        await timeout

        for t in tasks:
            t.cancel()
