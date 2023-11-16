import threading
import asyncio

from gi.repository import GLib, Gtk

class FetchWorker(threading.Thread):
    def __init__(self, app):
        super().__init__(name="SpeedtestWorker", daemon=True)

        self.stop_event = threading.Event()
        self.app = app

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

    async def do_run(self):
        try:
            self.app.servers = []
            while len(self.app.servers) == 0:
                print("Trying to fetch servers...")
                self.app.servers = await self.app.backend.get_servers(self.app.win.start_view.start_button)

            GLib.idle_add(self.app.win.start_view.server_selector.set_model, Gtk.StringList.new(list(map(lambda s: s.name, self.app.servers))))
            GLib.idle_add(self.app.win.set_view, self.app.win.start_view)

        except Exception as e:
            print(e)
            GLib.idle_add(self.app.win.set_view, self.app.win.offline_view)
