import threading
import asyncio
import time

from gi.repository import GLib

from .speedtest import ping, download, upload

DURATION = 15
DL_STREAMS = 6
UP_STREAMS = 3
OVERHEAD_COMPENSATION = 1.06

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

            _ping, jitter = await ping(self.server)

            GLib.idle_add(view.update_ping, _ping, jitter)

            GLib.idle_add(view.progress.remove_css_class, "up")
            GLib.idle_add(view.progress.add_css_class, "dl")
            GLib.idle_add(view.download.add_css_class, "active")
            timeout = GLib.timeout_add(1000 / 30, lambda: self.update(view.download, False))
            await self.perform_test(download, DL_STREAMS)
            GLib.idle_add(view.download.remove_css_class, "active")
            GLib.source_remove(timeout)

            GLib.idle_add(view.progress.remove_css_class, "dl")
            GLib.idle_add(view.progress.add_css_class, "up")
            GLib.idle_add(view.upload.add_css_class, "active")
            timeout = GLib.timeout_add(1000 / 30, lambda: self.update(view.upload, True))
            await self.perform_test(upload, UP_STREAMS)
            GLib.idle_add(view.upload.remove_css_class, "active")
            GLib.source_remove(timeout)
        except Exception as e:
            print(e)
            GLib.idle_add(self.win.set_view, self.win.offline_view)
    
    def update(self, gauge, part_two):
        view = self.win.test_view

        current_duration = time.time() - self.start_time
        value = self.total[0] * OVERHEAD_COMPENSATION / current_duration

        if current_duration > 1:
            view.update_gauge(gauge, value)
        view.progress.set_fraction(current_duration / DURATION * 0.5 + (0.5 if part_two else 0.0))

        return not self.stop_event.is_set()
    
    async def perform_test(self, test, streams):
        GLib.idle_add(self.win.test_view.progress.set_visible, True)

        self.start_time = time.time()
        self.total = [0]

        tasks = []

        timeout = asyncio.create_task(asyncio.sleep(DURATION))

        for _ in range(streams):
            tasks.append(asyncio.create_task(test(self.server, self.total)))
            await asyncio.sleep(0.3)

        await timeout

        GLib.idle_add(self.win.test_view.progress.set_visible, False)

        for t in tasks:
            t.cancel()
