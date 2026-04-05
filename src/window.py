import threading
import logging

from gi.repository import GObject, Gio, Gtk, Adw, GLib

from .util import bind_with_mapping, fetch_connection_details

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/window.ui")
class SpeedtestWindow(Adw.ApplicationWindow):
    __gtype_name__ = "SpeedtestWindow"

    view_switcher = Gtk.Template.Child()

    loading_view = Gtk.Template.Child()
    offline_view = Gtk.Template.Child()
    main_view = Gtk.Template.Child()
    
    start_view = Gtk.Template.Child()
    test_view = Gtk.Template.Child()
    connection_details_view = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.on_test_end = None

        action = Gio.SimpleAction.new("show_connection_details", None)
        action.connect("activate", lambda *_: self.show_connection_details_clicked())
        self.add_action(action)
    
    def set_view(self, view):
        self.view_switcher.set_visible_child(view)

    def start_test(self):
        self.main_view.push(self.test_view)

    def show_connection_details(self, ipv4, ipv6, isp, dns):
        self.connection_details_view.set_connection_info(ipv4, ipv6, isp, dns)
        self.main_view.push(self.connection_details_view)

    @Gtk.Template.Callback()
    def end_test(self, *_):
        if self.on_test_end:
            self.on_test_end()

    def show_connection_details_clicked(self, *_):
        self.connection_details_view.set_connection_info("", "", "", "")
        self.main_view.push(self.connection_details_view)
        threading.Thread(target=self._background_fetch, daemon=True).start()

    def _background_fetch(self):
        try:
            info = fetch_connection_details()
            GLib.idle_add(self._apply_connection_info, info)
        except Exception as e:
            import traceback
            traceback.print_exc()
            GLib.idle_add(self._apply_error_info)

    def _apply_connection_info(self, info):
        self.connection_details_view.set_connection_info(
            info.get("ipv4"),
            info.get("ipv6"),
            info.get("isp"),
            info.get("dns")
        )
        return False

    def _apply_error_info(self):
        self.connection_details_view.set_connection_info(
            _("Error fetching data"),
            _("Error fetching data"),
            _("Error fetching data"),
            _("Error fetching data")
        )
        return False

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/preferences.ui")
class SpeedtestPreferencesDialog(Adw.PreferencesDialog):
    __gtype_name__ = "SpeedtestPreferencesDialog"

    theme = Gtk.Template.Child()
    gauge_scale = Gtk.Template.Child()

    SCALES = [100, 250, 500, 1000, 10000]

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)

        self.app = app

        self.gauge_scale.set_model(Gtk.StringList.new(list(map(lambda s: f"{s}Mbps", self.SCALES))))

        app.settings.bind("theme", self.theme, "selected", Gio.SettingsBindFlags.DEFAULT)
        bind_with_mapping(app.settings, "gauge-scale", self.gauge_scale, "selected", Gio.SettingsBindFlags.DEFAULT, self.SCALES.index, self.SCALES.__getitem__)

        self.theme.connect("notify::selected", lambda *_: app.load_theme())

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

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/views/connection_details.ui")
class ConnectionDetailsView(Adw.NavigationPage):
    __gtype_name__ = "ConnectionDetailsView"

    ipv4 = GObject.Property(type=str, default="")
    ipv6 = GObject.Property(type=str, default="")
    isp = GObject.Property(type=str, default="")
    dns = GObject.Property(type=str, default="")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_connection_info(self, ipv4, ipv6, isp, dns):
        self.ipv4 = ipv4 or _("Not available")
        self.ipv6 = ipv6 or _("Not available")
        self.isp = isp or _("Not available")
        self.dns = dns or _("Not available")