import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_foreign("cairo")

from gi.repository import GLib, Gio, Gtk, Adw

from .window import SpeedtestWindow, SpeedtestPreferencesWindow
from .gauge import Gauge # This class isn't used there but it the widget needs to be registered
from .fetch_worker import FetchWorker
from .test_worker import TestWorker

from .backends.librespeed import LibrespeedBackend
from .backends.ookla import OoklaBackend

class SpeedtestApplication(Adw.Application):
    def __init__(self, version):
        super().__init__(application_id="xyz.ketok.Speedtest", flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        
        self.servers = None
        self.win = None
        self.version = version
        self.settings = Gio.Settings("xyz.ketok.Speedtest")
        self.fetch_worker = None
        self.test_worker = None

        self.create_action("quit", lambda *_: self.quit(), ["<primary>q", "<primary>w"])
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action, ["<primary>comma"])
        self.create_action("start", self.on_start_action)
        self.create_action("back", self.on_back_action)
        self.create_action("retry_connect", self.on_retry_connect_action)

    def do_activate(self):
        self.load_theme()

        self.win = self.props.active_window
        if not self.win:
            self.win = SpeedtestWindow(application=self)
        self.win.present()

        self.load_backend()

    def load_theme(self):
        THEMES = [Adw.ColorScheme.DEFAULT, Adw.ColorScheme.FORCE_LIGHT, Adw.ColorScheme.FORCE_DARK]
        Adw.StyleManager.get_default().set_color_scheme(THEMES[self.settings.get_int("theme")])

    def load_backend(self):
        if self.fetch_worker:
            self.fetch_worker.stop_event.set()
            self.fetch_worker.join()

        self.backend = (OoklaBackend if self.settings.get_string("backend") == "speedtest.net" else LibrespeedBackend)(f"KetokSpeedtest/{self.version}")

        self.fetch_worker = FetchWorker(self)
        self.fetch_worker.start()

    def on_about_action(self, widget, __):
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name=_("Speedtest"),
                                application_icon="xyz.ketok.Speedtest",
                                developer_name="Ketok",
                                version=self.version,
                                issue_url="https://github.com/Ketok4321/speedtest/issues",
                                developers=["Ketok"],
                                copyright="© 2023 Ketok",
                                license_type=Gtk.License.GPL_3_0)
        
        about.add_credit_section(_("Backend by"), ["Librespeed"])

        about.present()
    
    def on_preferences_action(self, widget, _):
        if self.win.view_switcher.get_visible_child() == self.win.test_view:
            return
        SpeedtestPreferencesWindow(self, transient_for=self.props.active_window).present()

    def on_start_action(self, widget, _):
        self.win.set_view(self.win.test_view)

        server = self.servers[self.win.start_view.server_selector.get_selected()]

        self.win.test_view.reset()
        self.win.test_view.server = server.name

        self.test_worker = TestWorker(self.backend, self.win, server, self.settings)
        self.test_worker.start()
    
    def on_back_action(self, widget, _):
        self.test_worker.stop_event.set()

        self.win.set_view(self.win.start_view)
    
    def on_retry_connect_action(self, widget, _):
        self.load_backend()

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
