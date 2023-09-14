import sys
import gi
import asyncio
import threading

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_foreign("cairo")

from gi.repository import GLib, Gio, Gtk, Adw

from .window import SpeedtestWindow
from .gauge import Gauge # This class isn't used there but it the widget needs to be registered
from .backends.ookla import OoklaBackend
from .speedtest_worker import SpeedtestWorker

class SpeedtestApplication(Adw.Application):
    def __init__(self, version):
        super().__init__(application_id="xyz.ketok.Speedtest", flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        
        self.backend = OoklaBackend(f"KetokSpeedtest/{version}")
        self.servers = None
        self.win = None
        self.version = version

        self.create_action("quit", lambda *_: self.quit(), ["<primary>q", "<primary>w"])
        self.create_action("about", self.on_about_action)
        self.create_action("start", self.on_start_action)
        self.create_action("back", self.on_back_action)
        self.create_action("retry_connect", self.on_retry_connect_action)

    def do_activate(self):
        self.win = self.props.active_window
        if not self.win:
            self.win = SpeedtestWindow(application=self)
        self.win.present()

        thread = threading.Thread(target=self.fetch_servers, daemon=True)
        thread.start()

    def fetch_servers(self):
        GLib.idle_add(self.win.set_view, self.win.loading_view)

        try:
            event_loop = asyncio.new_event_loop()

            self.servers = []
            while len(self.servers) == 0: # A proper fix would probably be better but this works too
                print("Trying to fetch servers...")
                self.servers = event_loop.run_until_complete(self.backend.get_servers())

            event_loop.close()

            GLib.idle_add(self.win.start_view.server_selector.set_model, Gtk.StringList.new(list(map(lambda s: s.name, self.servers))))
            GLib.idle_add(self.win.set_view, self.win.start_view)
        except Exception as e:
            print(e)
            GLib.idle_add(self.win.set_view, self.win.offline_view)

    def on_about_action(self, widget, _):
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name="Speedtest",
                                application_icon="xyz.ketok.Speedtest",
                                developer_name="Ketok",
                                version=self.version,
                                issue_url="https://github.com/Ketok4321/speedtest/issues",
                                developers=["Ketok"],
                                copyright="© 2023 Ketok",
                                license_type=Gtk.License.GPL_3_0)
        
        about.add_credit_section("Backend by", ["Librespeed"])

        about.present()

    def on_start_action(self, widget, _):
        self.win.set_view(self.win.test_view)

        server = self.servers[self.win.start_view.server_selector.get_selected()]

        self.win.test_view.reset()
        self.win.test_view.server = server.name

        self.worker = SpeedtestWorker(self.backend, self.win, server)
        self.worker.start()
    
    def on_back_action(self, widget, _):
        self.worker.stop_event.set()

        self.win.set_view(self.win.start_view)
    
    def on_retry_connect_action(self, widget, _):
        thread = threading.Thread(target=self.fetch_servers, daemon=True)
        thread.start()

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)
        
        return action

def main(version):
    app = SpeedtestApplication(version)
    return app.run(sys.argv)
