from gi.repository import GObject, Gio, Gtk, Adw

from .util import bind_with_mapping

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/window.ui")
class SpeedtestWindow(Adw.ApplicationWindow):
    __gtype_name__ = "SpeedtestWindow"

    view_switcher = Gtk.Template.Child()

    loading_view = Gtk.Template.Child()
    offline_view = Gtk.Template.Child()
    main_view = Gtk.Template.Child()
    
    start_view = Gtk.Template.Child()
    test_view = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.on_test_end = None
    
    def set_view(self, view):
        self.view_switcher.set_visible_child(view)

    def start_test(self):
        self.main_view.push(self.test_view)

    @Gtk.Template.Callback()
    def end_test(self, *_):
        if self.on_test_end:
            self.on_test_end()

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/preferences.ui")
class SpeedtestPreferencesDialog(Adw.PreferencesDialog):
    __gtype_name__ = "SpeedtestPreferencesDialog"

    theme = Gtk.Template.Child()
    gauge_scale = Gtk.Template.Child()
    backend = Gtk.Template.Child()

    SCALES = [100, 250, 500, 1000, 10000]
    BACKENDS = ["librespeed.org", "speedtest.net"]

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)

        self.app = app

        self.gauge_scale.set_model(Gtk.StringList.new(list(map(lambda s: f"{s}Mbps", self.SCALES))))
        self.backend.set_model(Gtk.StringList.new(self.BACKENDS))

        app.settings.bind("theme", self.theme, "selected", Gio.SettingsBindFlags.DEFAULT)
        bind_with_mapping(app.settings, "gauge-scale", self.gauge_scale, "selected", Gio.SettingsBindFlags.DEFAULT, self.SCALES.index, self.SCALES.__getitem__)
        bind_with_mapping(app.settings, "backend", self.backend, "selected", Gio.SettingsBindFlags.DEFAULT, self.BACKENDS.index, self.BACKENDS.__getitem__)

        self.theme.connect("notify::selected", lambda *_: app.load_theme())
        self.backend.connect("notify::selected", lambda *_: app.load_backend())

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/views/start.ui")
class StartView(Adw.NavigationPage):
    __gtype_name__ = "StartView"

    server_selector = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/views/test.ui")
class TestView(Adw.NavigationPage):
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
class OfflineView(Adw.Bin):
    __gtype_name__ = "OfflineView"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
