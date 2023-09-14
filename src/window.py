from gi.repository import GObject, Gtk, Adw

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/window.ui")
class SpeedtestWindow(Adw.ApplicationWindow):
    __gtype_name__ = "SpeedtestWindow"

    back_button = Gtk.Template.Child()

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
    
    def update_ping(self, ping, jitter):
        self.ping = f"{ping:.1f}ms"
        self.jitter = f"{jitter:.1f}ms"

    def update_gauge(self, object, speed):
        speedMb = round(speed / 125_000, 1)
        object.value = str(speedMb) + "Mbps"
        object.fill = min(speedMb / 100, 1.0)
    
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
