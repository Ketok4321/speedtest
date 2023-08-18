import threading
import asyncio
import gi

from gi.repository import GLib

from .speedtest import ping, download, upload, perform_test

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

            def dlCallback(speed, progress):
                view.updateGauge(view.download, speed)
                view.progress.remove_css_class("up")
                view.progress.add_css_class("dl")
                view.progress.set_fraction(progress)
            
            def upCallback(speed, progress):
                view.updateGauge(view.upload, speed)
                view.progress.remove_css_class("dl")
                view.progress.add_css_class("up")
                view.progress.set_fraction(progress)

            GLib.idle_add(view.progress.set_visible, True)

            await perform_test(download, self.server, lambda *args: GLib.idle_add(dlCallback, *args), 1 / 30)
            await perform_test(upload, self.server, lambda *args: GLib.idle_add(upCallback, *args), 1 / 30)

            GLib.idle_add(view.progress.set_visible, False)
        except Exception as e:
            print(e)
            GLib.idle_add(self.win.set_view, self.win.offline_view)