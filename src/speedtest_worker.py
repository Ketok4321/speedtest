import threading
import asyncio
import gi

from gi.repository import GLib

from .speedtest import ping, download, upload, perform_test

class SpeedtestWorker(threading.Thread):
    def __init__(self, view, server):
        super().__init__(name="SpeedtestWorker", daemon=True)

        self.stop_event = threading.Event()
        self.view = view
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

    async def do_run(self): # TODO: Try except
        GLib.idle_add(setattr, self.view, "ping", str(round(await ping(self.server), 1)) + "ms")

        def dlCallback(speed, progress):
            self.view.updateGauge(self.view.download, speed)
            self.view.progress.remove_css_class("up")
            self.view.progress.add_css_class("dl")
            self.view.progress.set_fraction(progress)
        
        def upCallback(speed, progress):
            self.view.updateGauge(self.view.upload, speed)
            self.view.progress.remove_css_class("dl")
            self.view.progress.add_css_class("up")
            self.view.progress.set_fraction(progress)

        await perform_test(download, self.server, lambda *args: GLib.idle_add(dlCallback, *args), 1 / 30)
        await perform_test(upload, self.server, lambda *args: GLib.idle_add(upCallback, *args), 1 / 30)