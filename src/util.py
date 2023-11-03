from gi.repository import Gio

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
