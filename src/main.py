import sys
import gi
import threading

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_foreign("cairo")

from gi.repository import GLib, Gio, Gtk, Adw

from .window import SpeedtestWindow
from .gauge import Gauge # This class isn't used there but it the widget needs to be registered 
from .speedtest import Speedtest

class SpeedtestApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id="xyz.ketok.Speedtest", flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        
        self.speedtest = Speedtest()
        self.servers = self.speedtest.get_servers()
        self.win = None

        self.create_action("quit", lambda *_: self.quit(), ["<primary>q"])
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action)
        self.create_action("start", self.on_start_action)
        self.test_again_action = self.create_action("test_again", self.on_test_again_action)

    def do_activate(self):
        self.win = self.props.active_window
        if not self.win:
            self.win = SpeedtestWindow(application=self)
        self.win.present()

        self.win.start_view.server_selector.set_model(Gtk.StringList.new(list(map(lambda x: "{} ({}, {})".format(x["name"], x["location"], x["country"]), self.servers))))

    def on_about_action(self, widget, _): #TODO: Credit speedtest-cli and ookla
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name="Speedtest",
                                application_icon="xyz.ketok.Speedtest",
                                developer_name="Ketok",
                                version="0.1.0",
                                developers=["Ketok"],
                                copyright="© 2023 Ketok")
        about.present()

    def on_preferences_action(self, widget, _):
        print("app.preferences action activated")

    def on_start_action(self, widget, _):
        self.win.view_switcher.set_visible_child(self.win.test_view)
        self.win.back_button.set_visible(True)

        server_id = self.servers[self.win.start_view.server_selector.get_selected()]["id"]

        self.test_again_action.set_enabled(False)
        thread = threading.Thread(target=self.do_start, args=[server_id], daemon=True)
        thread.start()
    
    def do_start(self, server_id): # TODO: Try except
        view = self.win.test_view
        view.reset()

        def callback(update):
            match update:
                case { "type": "ping", "ping": { "latency": latency } }:
                    view.ping = str(round(latency, 1)) + "ms"
                case { "type": "download", "download": { "bandwidth": bandwidth, "progress": progress } }:
                    view.updateGauge(view.download, bandwidth)
                    view.progress.remove_css_class("up")
                    view.progress.add_css_class("dl")
                    view.progress.set_fraction(progress)
                case { "type": "upload", "upload": { "bandwidth": bandwidth, "progress": progress } }:
                    view.updateGauge(view.upload, bandwidth)
                    view.progress.remove_css_class("dl")
                    view.progress.add_css_class("up")
                    view.progress.set_fraction(progress)

        self.speedtest.start(server_id, lambda update: GLib.idle_add(callback, update))

        GLib.idle_add(self.test_again_action.set_enabled, True)
    
    def on_test_again_action(self, widget, _):
        self.win.view_switcher.set_visible_child(self.win.start_view)
        self.win.back_button.set_visible(False)

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
