import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_foreign("cairo")

from gi.repository import GLib, Gio, Gtk, Adw

from .conf import *
from .window import SpeedtestWindow, SpeedtestPreferencesDialog
from .gauge import Gauge # This class isn't used there but it the widget needs to be registered
from .fetch_worker import FetchWorker
from .test_worker import TestWorker

from .backends.librespeed import LibrespeedBackend

class SpeedtestApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, resource_base_path="/xyz/ketok/Speedtest", flags=Gio.ApplicationFlags.DEFAULT_FLAGS)

        self.win = None
        self.settings = Gio.Settings("xyz.ketok.Speedtest")
        self.backend = None
        self.fetch_worker = None
        self.test_worker = None

        self.create_action("quit", lambda *_: self.quit(), ["<primary>q", "<primary>w"])
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action, ["<primary>comma"])
        self.create_action("start", self.on_start_action)
        self.create_action("retry_connect", self.on_retry_connect_action)

    def do_activate(self):
        self.load_theme()

        self.win = self.props.active_window
        if not self.win:
            self.win = SpeedtestWindow(application=self)
            self.win.on_test_end = lambda: self.test_worker.stop_event.set()
            if DEVEL:
                self.win.add_css_class("devel")

            self.settings.bind("width", self.win, "default-width", Gio.SettingsBindFlags.DEFAULT)
            self.settings.bind("height", self.win, "default-height", Gio.SettingsBindFlags.DEFAULT)

            self.win.present()

        self.load_backend()

    def load_theme(self):
        THEMES = [Adw.ColorScheme.DEFAULT, Adw.ColorScheme.FORCE_LIGHT, Adw.ColorScheme.FORCE_DARK]
        Adw.StyleManager.get_default().set_color_scheme(THEMES[self.settings.get_int("theme")])

    def load_backend(self):
        if self.fetch_worker:
            self.fetch_worker.stop_event.set()
            self.fetch_worker.join()

        self.backend = LibrespeedBackend(f"KetokSpeedtest/{VERSION}")

        self.fetch_worker = FetchWorker(self)
        self.fetch_worker.start()

    def on_about_action(self, widget, __):
        about = Adw.AboutDialog(application_name=_("Speedtest"),
                                application_icon=APP_ID,
                                developer_name="Ketok",
                                version=VERSION,
                                issue_url="https://github.com/Ketok4321/speedtest/issues",
                                developers=["Ketok"],
                                copyright="© 2023 Ketok",
                                license_type=Gtk.License.GPL_3_0)
        
        about.add_credit_section(_("Backend by"), ["Librespeed"])

        about.present(self.win)
    
    def on_preferences_action(self, widget, _):
        if self.win.main_view.get_visible_page() == self.win.test_view: # TODO: deactivate this action insead of disabling it
            return
        SpeedtestPreferencesDialog(self).present(self.win)

    def on_start_action(self, widget, _):
        self.win.start_test()

        server = self.fetch_worker.servers[self.win.start_view.server_selector.get_selected()]

        self.win.test_view.reset()
        self.win.test_view.server = server.name

        self.test_worker = TestWorker(self, server)
        self.test_worker.start()
    
    def on_retry_connect_action(self, widget, _):
        self.load_backend()

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)
        
        return action

def main():
    app = SpeedtestApplication()
    return app.run(sys.argv)
