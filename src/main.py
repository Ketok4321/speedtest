import sys
import gi
import threading

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_foreign("cairo")

from gi.repository import GLib, Gio, Gtk, Adw

from .window import SpeedtestWindow
from .gauge import Gauge # This class isn't used there but it the widget needs to be registered 
from .speedtest_worker import SpeedtestWorker

class SpeedtestApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id="xyz.ketok.Speedtest", flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        
        self.servers = None
        self.win = None

        self.create_action("quit", lambda *_: self.quit(), ["<primary>q"])
        self.create_action("about", self.on_about_action)
        self.create_action("start", self.on_start_action)
        self.create_action("back", self.on_back_action)
        self.create_action("retry_connect", self.on_retry_connect_action)

    def do_activate(self):
        self.win = self.props.active_window
        if not self.win:
            self.win = SpeedtestWindow(application=self)
        self.win.present()

        if not self.fetch_servers():
            self.win.view_switcher.set_visible_child(self.win.offline_view)

    def fetch_servers(self):
        #if not self.speedtest.check_internet_connection():
        #    return False

        #try:
        #    self.servers = self.speedtest.get_servers()
        #except Exception as e:
        #    return False

        #self.win.start_view.server_selector.set_model(Gtk.StringList.new(list(map(lambda x: "{} ({}, {})".format(x["name"], x["location"], x["country"]), self.servers))))
        return True

    def on_about_action(self, widget, _): #TODO: Credit speedtest-cli and ookla
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name="Speedtest",
                                application_icon="xyz.ketok.Speedtest",
                                developer_name="Ketok",
                                version="0.1.0",
                                developers=["Ketok"],
                                copyright="© 2023 Ketok")
        about.present()

    def on_start_action(self, widget, _):
        #if not self.speedtest.check_internet_connection():
        #    self.win.view_switcher.set_visible_child(self.win.offline_view)
        #    return

        self.win.view_switcher.set_visible_child(self.win.test_view)
        self.win.back_button.set_visible(True)

        server_id = 0#self.servers[self.win.start_view.server_selector.get_selected()]["id"]

        self.win.test_view.reset()

        self.worker = SpeedtestWorker(self.win.test_view)
        self.worker.start()
    
    def on_back_action(self, widget, _):
        self.worker.stop_event.set() # TODO: wait for the thread to stop?

        self.win.view_switcher.set_visible_child(self.win.start_view)
        self.win.back_button.set_visible(False)
    
    def on_retry_connect_action(self, widget, _):
        if self.fetch_servers():
            self.win.view_switcher.set_visible_child(self.win.start_view)
        else:
            self.win.offline_view.toast_overlay.add_toast(Adw.Toast.new("Couldn't reconnect"))

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)
        
        return action

def main(version):
    app = SpeedtestApplication()
    return app.run(sys.argv)
