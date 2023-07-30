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
    win = None
    speedtest = Speedtest(secure=True)

    def __init__(self):
        super().__init__(application_id="xyz.ketok.Speedtest", flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        
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

        self.test_again_action.set_enabled(False)
        thread = threading.Thread(target=self.do_start, daemon=True)
        thread.start()
    
    def do_start(self): # TODO: Try except
        view = self.win.test_view
        
        self.speedtest.get_best_server() # This measures ping

        view.ping = str(round(self.speedtest.results.ping)) + "ms"
        dl = self.speedtest.download(lambda *args, speed=None, end=None, **kwargs: GLib.idle_add(lambda: view.updateDownload(speed)) if end else None)
        up = self.speedtest.upload(lambda *args, speed=None, end=None, **kwargs: GLib.idle_add(lambda: view.updateUpload(speed)) if end else None)
        GLib.idle_add(lambda: view.updateDownload(dl))
        GLib.idle_add(lambda: view.updateUpload(up))
        GLib.idle_add(lambda: self.test_again_action.set_enabled(True))
    
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
