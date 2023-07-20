import threading

from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Adw

from .speedtest import Speedtest

def toMb(speed):
    return round(speed / 1_000_000)

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/window.ui")
class SpeedtestWindow(Adw.ApplicationWindow):
    __gtype_name__ = "SpeedtestWindow"

    view_switcher = Gtk.Template.Child()

    start_view = Gtk.Template.Child()
    test_view = Gtk.Template.Child()

    test_thread = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.get_application().create_action("start", self.on_start_action)
        self.get_application().create_action("cancel", self.on_cancel_action)

    def on_start_action(self, widget, _):
        self.view_switcher.set_visible_child(self.test_view)

        test_thread = threading.Thread(target=self.test_view.start)
        test_thread.daemon = True
        test_thread.start()

    
    def on_cancel_action(self, widget, _):
        # TODO: Abort the thread

        self.view_switcher.set_visible_child(self.start_view)

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/views/start.ui")
class StartView(Gtk.Box):
    __gtype_name__ = "StartView"

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
    
    def start(self): # TODO: Try except
        speedtest = Speedtest(secure=True)
        speedtest.get_best_server() # This measures ping

        self.ping = str(round(speedtest.results.ping)) + "ms"
        dl = speedtest.download(self.callback(self.download))
        up = speedtest.upload(self.callback(self.upload))
        self.callback(self.download)(0, 0, end=True, speed=dl)
        self.callback(self.upload)(0, 0, end=True, speed=up)

    def callback(self, object):
        def result(i, request_count, speed=None, start=False, end=False):
            if end:
                speedMb = toMb(speed)

                def why_the_fuck_doesnt_python_support_multiline_lambdas():
                    object.label = str(speedMb) + "Mbps"
                    object.fill = min(toMb(speed) / 100, 1.0)

                GLib.idle_add(why_the_fuck_doesnt_python_support_multiline_lambdas)
        return result
