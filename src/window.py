from gi.repository import GObject, Gtk, Adw

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/window.ui")
class SpeedtestWindow(Adw.ApplicationWindow):
    __gtype_name__ = "SpeedtestWindow"

    back_button = Gtk.Template.Child()

    view_switcher = Gtk.Template.Child()

    start_view = Gtk.Template.Child()
    test_view = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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

    progress = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def updateGauge(self, object, speed):
        speedMb = round(speed / 125_000, 1)
        object.value = str(speedMb) + "Mbps"
        object.fill = min(speedMb / 100, 1.0)
    
    def reset(self):
        for obj in self.download, self.upload:
            obj.value = "..."
            obj.fill = 0.0
        self.ping = "..."
        self.progress.set_fraction(0.0)
