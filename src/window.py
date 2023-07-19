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

    download = Gtk.Template.Child()
    upload = Gtk.Template.Child()
    ping = GObject.Property(type=str, default="...")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def start(self): # TODO: Try except
        speedtest = Speedtest(secure=True)
        speedtest.get_best_server() # This measures ping

        self.ping = str(speedtest.results.ping) + "ms"
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
