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
from .const import Config

from .backends.librespeed import LibrespeedBackend

class SpeedtestApplication(Adw.Application):

    troubleshooting = "OS: {os}\nApplication version: {wv}\nGTK: {gtk}\nlibadwaita: {adw}\nApp ID: {app_id}\nProfile: {profile}\nLanguage: {lang}"

    def __init__(self, version):
        super().__init__(application_id="xyz.ketok.Speedtest", flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        
        self.servers = None
        self.win = None
        self.version = Config.VERSION
        self.settings = Gio.Settings("xyz.ketok.Speedtest")
        self.fetch_worker = None
        self.test_worker = None

        self.create_action("quit", lambda *_: self.quit(), ["<primary>q"])
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action, ["<primary>comma"])
        self.create_action("start", self.on_start_action, ["<Primary>Return"])
        self.create_action("back", self.on_back_action)
        self.create_action("retry_connect", self.on_retry_connect_action)

        self.set_accels_for_action("win.show-help-overlay", ["<Primary>question"])

        gtk_version = str(Gtk.MAJOR_VERSION) + "." + str(Gtk.MINOR_VERSION) + "." + str(Gtk.MICRO_VERSION)
        adw_version = str(Adw.MAJOR_VERSION) + "." + str(Adw.MINOR_VERSION) + "." + str(Adw.MICRO_VERSION)
        os_string = GLib.get_os_info("NAME") + " " + GLib.get_os_info("VERSION")
        lang = GLib.environ_getenv(GLib.get_environ(), "LANG")

        self.troubleshooting = self.troubleshooting.format( os = os_string, wv = Config.VERSION, gtk = gtk_version, adw = adw_version, profile = Config.PROFILE, app_id = "xyz.ketok.Speedtest", lang = lang )

    def do_activate(self):
        self.win = self.props.active_window
        if not self.win:
            self.win = SpeedtestWindow(application=self)
        self.win.present()
        self.create_action("push-thing", self.win.push_thing)

        self.load_backend()

    def load_backend(self):
        if self.fetch_worker:
            self.fetch_worker.stop_event.set()
            self.fetch_worker.join()

        self.backend = LibrespeedBackend(f"KetokSpeedtest/{self.version}")

        self.fetch_worker = FetchWorker(self)
        self.fetch_worker.start()

    def on_about_action(self, widget, __):
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name=_("Speedtest"),
                                application_icon="xyz.ketok.Speedtest",
                                developer_name="Ketok",
                                version=Config.VERSION,
                                issue_url="https://github.com/Ketok4321/speedtest/issues",
                                developers=["Ketok"],
                                # Translators: do one of the following, one per line: Your Name, Your Name <email@email.org>, Your Name https://websi.te
                                translator_credits=_("translator-credits"),
                                copyright="© 2023 Ketok",
                                license_type=Gtk.License.GPL_3_0,
                                debug_info=self.troubleshooting)

        about.add_credit_section(_("Contributors"), [
            # Contributors: do one of the following, one per line: Your Name, Your Name <email@email.org>, Your Name https://websi.te
            "kramo https://kramo.hu",
            "skøldis <speedtest@turtle.garden>"
        ])
        
        about.add_acknowledgement_section(_("Backend by"), ["Librespeed https://librespeed.org/"])

        about.present()
    
    def on_preferences_action(self, widget, _):
        SpeedtestPreferencesWindow(self, transient_for=self.props.active_window).present()

    def on_start_action(self, widget, _1):
        if self.win.test_view.in_progress and self.win.nav_view.get_visible_page().get_tag() == "test_page":
            toast = Adw.Toast.new(_("Session already in progress"))
            self.win.new_toast_overlay.add_toast(toast)
            return

        if self.win.nav_view.get_visible_page().get_tag() == "test_page" or self.win.view_switcher.get_visible_child() == self.win.offline_view:
            toast = Adw.Toast.new(_("Cannot start new session"))
            self.win.new_toast_overlay.add_toast(toast)
            return

        self.win.set_view(self.win.test_view)

        if self.win.test_view.in_progress:
            toast = Adw.Toast.new(_("Session already in progress"))
            self.win.new_toast_overlay.add_toast(toast)
            return

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
