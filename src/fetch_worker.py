import threading
import asyncio

from gi.repository import GLib, Gtk

class FetchWorker(threading.Thread):
    def __init__(self, app):
        super().__init__(name="FetchWorker", daemon=True)

        self.stop_event = threading.Event()
        self.app = app
        self.servers = []

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
        GLib.idle_add(self.app.win.set_view, self.app.win.loading_view)

        try:
            self.servers = []
            while len(self.servers) == 0:
                print("Trying to fetch servers...")
                self.servers = await self.app.backend.get_servers()

            GLib.idle_add(self.app.win.start_view.server_selector.set_model, Gtk.StringList.new(list(map(lambda s: s.name, self.servers))))
            GLib.idle_add(self.app.win.main_view.pop)
            GLib.idle_add(self.app.win.set_view, self.app.win.main_view)
        except Exception as e:
            print(e)
            GLib.idle_add(self.app.win.set_view, self.app.win.offline_view)
