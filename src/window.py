from gi.repository import GObject, Gio, Gtk, Adw

# I have shamelessly stole it from https://gitlab.gnome.org/GNOME/pygobject/-/issues/98
def bind_with_mapping(self, key, widget, prop, flags, key_to_prop, prop_to_key):
    """
    Recreate g_settings_bind_with_mapping from scratch.
    This method was shamelessly stolen from Robert Park's
    gottengeography who shamelessly stolen it from John Stowers'
    gnome-tweak-tool on May 14, 2012.
    """
    self._ignore_key_changed = False

    def key_changed(settings, key):
        if self._ignore_key_changed:
            return
        self._ignore_prop_changed = True
        widget.set_property(prop, key_to_prop(self[key]))
        self._ignore_prop_changed = False

    def prop_changed(widget, param):
        if self._ignore_prop_changed:
            return
        self._ignore_key_changed = True
        self[key] = prop_to_key(widget.get_property(prop))
        self._ignore_key_changed = False

    if not (flags & (Gio.SettingsBindFlags.SET | Gio.SettingsBindFlags.GET)): # ie Gio.SettingsBindFlags.DEFAULT
       flags |= Gio.SettingsBindFlags.SET | Gio.SettingsBindFlags.GET

    if flags & Gio.SettingsBindFlags.GET:
        key_changed(self, key)
        if not (flags & Gio.SettingsBindFlags.GET_NO_CHANGES):
            self.connect('changed::' + key, key_changed)
    if flags & Gio.SettingsBindFlags.SET:
        widget.connect('notify::' + prop, prop_changed)
    if not (flags & Gio.SettingsBindFlags.NO_SENSITIVITY):
        self.bind_writable(key, widget, "sensitive", False)

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/window.ui")
class SpeedtestWindow(Adw.ApplicationWindow):
    __gtype_name__ = "SpeedtestWindow"

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

        self.back_button.set_visible(view == self.test_view)
        self.menu_button.set_visible(view != self.test_view)

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/preferences.ui")
class SpeedtestPreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = "SpeedtestPreferencesWindow"

    gauge_scale = Gtk.Template.Child()
    backend = Gtk.Template.Child()

    SCALES = [100, 1000]
    BACKENDS = ["librespeed.org", "speedtest.net"]

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)

        self.gauge_scale.set_model(Gtk.StringList.new(list(map(lambda s: f"{s}Mbps", self.SCALES))))
        self.backend.set_model(Gtk.StringList.new(self.BACKENDS))

        bind_with_mapping(app.settings, "gauge-scale", self.gauge_scale, "selected", Gio.SettingsBindFlags.DEFAULT, self.SCALES.index, self.SCALES.__getitem__)
        bind_with_mapping(app.settings, "backend", self.backend, "selected", Gio.SettingsBindFlags.DEFAULT, self.BACKENDS.index, self.BACKENDS.__getitem__)

        self.backend.connect("notify::selected", lambda *_: app.fetch_servers())

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
