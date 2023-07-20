import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_foreign("cairo")

from gi.repository import Gio, Gtk, Adw

from .window import SpeedtestWindow
from .gauge import Gauge # This class isn't used there but it the widget needs to be registered 

class SpeedtestApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id="xyz.ketok.Speedtest",
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action("quit", lambda *_: self.quit(), ["<primary>q"])
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = SpeedtestWindow(application=self)
        win.present()

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

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    app = SpeedtestApplication()
    return app.run(sys.argv)
