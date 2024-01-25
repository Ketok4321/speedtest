import threading
import asyncio
import time

from dataclasses import dataclass

from gi.repository import GLib

DURATION = 15
OVERHEAD_COMPENSATION = 1.06

@dataclass
class TestResults:
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
        
        self.start_time = 0
        self.last_label_update = 0

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
            view = self.app.win.test_view

            timeout = None

            def on_event(type):
                nonlocal timeout

                if type == "ping":
                    view.ping = f"{self.results.ping:.1f}ms"
                    view.jitter = f"{self.results.jitter:.1f}ms"
                elif type == "download_start":
                    timeout = view.download.get_frame_clock().connect("before-paint", lambda *_: self.update(view.download, self.results.total_dl, False))
                    
                    view.progress.remove_css_class("up")
                    view.progress.add_css_class("dl")
                    view.download.add_css_class("active")
                    
                    self.start_time = time.time()
                elif type == "download_end":
                    view.download.get_frame_clock().disconnect(timeout)
                    view.download.remove_css_class("active")
                elif type == "upload_start":
                    timeout = view.upload.get_frame_clock().connect("before-paint", lambda *_: self.update(view.upload, self.results.total_up, True))
                    
                    view.progress.remove_css_class("dl")
                    view.progress.add_css_class("up")
                    view.upload.add_css_class("active")
                    
                    self.start_time = time.time()
                elif type == "upload_end":
                    view.upload.get_frame_clock().disconnect(timeout)
                    view.upload.remove_css_class("active")

            GLib.idle_add(self.app.win.test_view.progress.set_visible, True)
            self.results = TestResults()
            await self.app.backend.start(self.server, self.results, lambda type: GLib.idle_add(on_event, type), DURATION)
            GLib.idle_add(self.app.win.test_view.progress.set_visible, False)
        except Exception as e:
            print(e)
            GLib.idle_add(self.app.win.set_view, self.app.win.offline_view)
    
    def update(self, gauge, total, part_two):
        view = self.app.win.test_view

        current_duration = time.time() - self.start_time
        value = total * OVERHEAD_COMPENSATION / current_duration

        if current_duration > 1:
            speedMb = round(value / 125_000, 1)
            if time.time() - self.last_label_update >= 0.075:
                gauge.value = str(speedMb) + "Mbps"
                self.last_label_update = time.time()
            gauge.fill = min(speedMb / self.app.settings.get_int("gauge-scale"), 1.0)

        view.progress.set_fraction(current_duration / DURATION * 0.5 + (0.5 if part_two else 0.0))

        return not self.stop_event.is_set()
    
    async def perform_test(self, test, streams):
        GLib.idle_add(self.app.win.test_view.progress.set_visible, True)

        self.start_time = time.time()

        GLib.idle_add(self.app.win.test_view.progress.set_visible, False)
