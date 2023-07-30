from gi.repository import GObject, Gtk, Adw

def toMb(speed):
    return round(speed / 1_000_000)

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def updateGauge(self, object, speed):
        speedMb = toMb(speed)
        object.label = str(speedMb) + "Mbps"
        object.fill = min(toMb(speed) / 100, 1.0)

    def updateDownload(self, speed):
        self.updateGauge(self.download, speed)

    def updateUpload(self, speed):
        self.updateGauge(self.upload, speed)
