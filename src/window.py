from gi.repository import GObject, Gio, Gtk, Adw

from .util import bind_with_mapping

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/window.ui")
class SpeedtestWindow(Adw.ApplicationWindow):
    __gtype_name__ = "SpeedtestWindow"

    header_bar = Gtk.Template.Child()
    back_button = Gtk.Template.Child()
    menu_button = Gtk.Template.Child()

    view_switcher = Gtk.Template.Child()

    loading_view = Gtk.Template.Child()
    start_view = Gtk.Template.Child()
    test_view = Gtk.Template.Child()
    offline_view = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def set_view(self, view):
        self.view_switcher.set_transition_type(Gtk.StackTransitionType.SLIDE_UP_DOWN if view == self.test_view or self.view_switcher.get_visible_child() == self.test_view else Gtk.StackTransitionType.CROSSFADE)

        self.view_switcher.set_visible_child(view)

        if view == self.test_view:
            self.header_bar.set_title_widget(None)
            self.header_bar.remove_css_class("flat")
        else:
            # This should be replaced with the `show-title` property after Libadwiata 1.4
            self.header_bar.set_title_widget(Gtk.Box())
            self.header_bar.add_css_class("flat")

        self.back_button.set_visible(view == self.test_view)
        self.menu_button.set_visible(view != self.test_view)

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/preferences.ui")
class SpeedtestPreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = "SpeedtestPreferencesWindow"

    theme = Gtk.Template.Child()
    gauge_scale = Gtk.Template.Child()

    SCALES = [100, 250, 500, 1000]

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)

        self.app = app

        self.gauge_scale.set_model(Gtk.StringList.new(list(map(lambda s: f"{s}Mbps", self.SCALES))))

        app.settings.bind("theme", self.theme, "selected", Gio.SettingsBindFlags.DEFAULT)
        bind_with_mapping(app.settings, "gauge-scale", self.gauge_scale, "selected", Gio.SettingsBindFlags.DEFAULT, self.SCALES.index, self.SCALES.__getitem__)

        self.theme.connect("notify::selected", lambda *_: app.load_theme())

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/views/start.ui")
class StartView(Gtk.Box):
    __gtype_name__ = "StartView"

    server_selector = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/views/test.ui")
class TestView(Gtk.Box):
    __gtype_name__ = "TestView"

    download = Gtk.Template.Child()
    upload = Gtk.Template.Child()
    ping = GObject.Property(type=str, default="...")
    jitter = GObject.Property(type=str, default="...")
    server = GObject.Property(type=str)

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

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/views/offline.ui")
class OfflineView(Gtk.Box):
    __gtype_name__ = "OfflineView"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
