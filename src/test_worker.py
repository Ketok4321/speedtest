import threading
import asyncio
import time

from dataclasses import dataclass

from gi.repository import GLib

DURATION = 15
OVERHEAD_COMPENSATION = 1.06

@dataclass
class TestResults:
    stage: int = 0
    start_time: float = 0

    ping: float = 0
    jitter: float = 0
    total_dl: int = 0
    total_up: int = 0

class TestWorker(threading.Thread):
    def __init__(self, app, server):
        super().__init__(name="TestWorker", daemon=True)

        self.stop_event = threading.Event()
        self.app = app
        self.server = server
        
        self.last_label_update = 0

    def run(self):
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)

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
            if task != asyncio.current_task():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def do_run(self):
        try:
            view = self.app.win.test_view

            view.add_tick_callback(lambda *_: self.update(), None)
            self.results = TestResults()
            await self.app.backend.start(self.server, self.results, DURATION)
        except Exception as e:
            print(e)
            GLib.idle_add(self.app.win.set_view, self.app.win.offline_view)

    def update(self):
        view = self.app.win.test_view

        total_duration = time.time() - self.results.start_time

        self.app.win.test_view.progress.set_visible(True)

        if self.results.stage == 1:
            view.ping = f"{self.results.ping:.1f}ms"
            view.jitter = f"{self.results.jitter:.1f}ms"

            view.progress.remove_css_class("up")
            view.progress.add_css_class("dl")
            view.download.add_css_class("active")

            self.update_gauge(view.download, self.results.total_dl, total_duration)
        elif self.results.stage == 2:
            view.download.remove_css_class("active")

            view.progress.remove_css_class("dl")
            view.progress.add_css_class("up")
            view.upload.add_css_class("active")

            self.update_gauge(view.upload, self.results.total_up, total_duration - DURATION)
        elif self.results.stage == 3:
            view.upload.remove_css_class("active")
            self.app.win.test_view.progress.set_visible(False)
            return GLib.SOURCE_REMOVE

        view.progress.set_fraction(total_duration / (DURATION * 2))

        if self.stop_event.is_set():
            return GLib.SOURCE_REMOVE

        return GLib.SOURCE_CONTINUE

    def update_gauge(self, gauge, total, test_duration):
        value = total * OVERHEAD_COMPENSATION / test_duration

        if test_duration > 1:
            speedMb = round(value / 125_000, 1)
            if time.time() - self.last_label_update >= 0.075:
                gauge.value = str(speedMb) + "Mbps"
                self.last_label_update = time.time()
            gauge.fill = min(speedMb / self.app.settings.get_int("gauge-scale"), 1.0)
