from gi.repository import GObject, Gio, Gtk, Adw, GLib

from .util import bind_with_mapping
from .const import Config

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/window.ui")
class SpeedtestWindow(Adw.ApplicationWindow):
    __gtype_name__ = "SpeedtestWindow"

    start_page = Gtk.Template.Child()
    test_page = Gtk.Template.Child()
    nav_view = Gtk.Template.Child()
    new_toast_overlay = Gtk.Template.Child()

    view_switcher = Gtk.Template.Child()

    start_view = Gtk.Template.Child()
    test_view = Gtk.Template.Child()
    test_page = Gtk.Template.Child()
    offline_view = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if Config.DEVEL:
            self.add_css_class("devel")

        self.test_page.connect("hidden", self.go_back)

        try:
            builder = Gtk.Builder.new_from_resource("/xyz/ketok/Speedtest/ui/help-overlay.ui")
            self.set_help_overlay(builder.get_object("help_overlay"))
        except:
            print("Error")

    def go_back(self, new):
        if self.test_view.in_progress:
            toast = Adw.Toast.new(_("Discarded session"))
            toast.set_button_label(_("Undo"))
            toast.set_action_name("app.push-thing")
            self.new_toast_overlay.add_toast(toast)

    def push_thing(self, _1, _2):
        self.nav_view.push_by_tag("test_page")

    def set_view(self, view):
        if (view == self.offline_view):
            if self.nav_view.get_visible_page().get_tag() == "test_page":
                self.nav_view.pop()
            self.view_switcher.set_visible_child(view)
            return

        if (view == self.start_view):
            if self.nav_view.get_visible_page().get_tag() == "test_page":
                self.nav_view.pop()
            self.view_switcher.set_visible_child(view)
            return

        if (view == self.test_view and self.nav_view.get_visible_page().get_tag() != "test_page"):
            self.nav_view.push_by_tag("test_page")

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/preferences.ui")
class SpeedtestPreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = "SpeedtestPreferencesWindow"

    gauge_scale = Gtk.Template.Child()

    SCALES = [100, 250, 500, 1000]

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)

        self.app = app

        self.gauge_scale.set_model(Gtk.StringList.new(list(map(lambda s: f"{s}Mbps", self.SCALES))))

        bind_with_mapping(app.settings, "gauge-scale", self.gauge_scale, "selected", Gio.SettingsBindFlags.DEFAULT, self.SCALES.index, self.SCALES.__getitem__)

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/views/start.ui")
class StartView(Gtk.Box):
    __gtype_name__ = "StartView"

    server_selector = Gtk.Template.Child()
    start_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.server_selector,connect("notify::model", lambda: self.start_button.set_sensitive(True))

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/views/test.ui")
class TestView(Adw.BreakpointBin):
    __gtype_name__ = "TestView"

    download = Gtk.Template.Child()
    upload = Gtk.Template.Child()
    ping = GObject.Property(type=str, default="...")
    jitter = GObject.Property(type=str, default="...")
    server = GObject.Property(type=str)
    in_progress = GObject.Property(type=bool, default=False)

    progress = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def reset(self):
        for obj in self.download, self.upload:
            obj.value = "..."
            obj.fill = 0.0
        self.ping = "..."
        self.jitter = "..."
        self.progress.set_fraction(0.0)
        self.in_progress = False

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/views/offline.ui")
class OfflineView(Gtk.Box):
    __gtype_name__ = "OfflineView"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
