import cairo
import math

from gi.repository import GObject, Gtk, Adw

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/gauge.ui")
class Gauge(Adw.Bin):
    __gtype_name__ = "Gauge"

    drawing_area = Gtk.Template.Child()

    label = GObject.Property(type=str)
    value = GObject.Property(type=str, default="...")

    color1 = GObject.Property(type=str)
    color2 = GObject.Property(type=str)

    @GObject.Property(type=float, minimum = 0.0, maximum = 1.0)
    def fill(self):
        return self._fill
    
    @fill.setter
    def fill(self, value):
        self._fill = value
        self.drawing_area.queue_draw()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._fill = 0.0
        
        self.drawing_area.set_draw_func(self.draw)

    def draw(self, da, ctx, width, height): # TODO: Try blue-green color scheme, like in adwaita demo
        IS_LIGHT = not Adw.StyleManager.get_default().get_dark()
        
        ARC_SIZE = min(width, height) * 0.85

        ARC_START = 0.75 * math.pi
        ARC_LENGTH = 1.5 * math.pi

        ARC_THICKNESS = ARC_SIZE * 0.125

        ARC_CENTER = height / 2 + ARC_THICKNESS / 2

        def hex_to_rgb(hexa):
            return tuple(int(hexa[i:i+2], 16) / 255 for i in (0, 2, 4))

        UNFILLED_COLOR = 0, 0, 0, 0.1 if IS_LIGHT else 0.3
        FILLED_COLOR_1 = hex_to_rgb(self.color1)
        FILLED_COLOR_2 = hex_to_rgb(self.color2)

        ctx.set_line_width(ARC_THICKNESS)

        ctx.set_source_rgba(*UNFILLED_COLOR)
        ctx.arc(width / 2, ARC_CENTER, ARC_SIZE / 2, ARC_START, ARC_START + ARC_LENGTH)
        ctx.stroke()

        filled = cairo.LinearGradient(0.0, 0.0, width, 0.0)
        filled.add_color_stop_rgb(0, *FILLED_COLOR_1)
        filled.add_color_stop_rgb(width, *FILLED_COLOR_2)

        ctx.set_source(filled)
        ctx.arc(width / 2, ARC_CENTER, ARC_SIZE / 2, ARC_START, ARC_START + ARC_LENGTH * self.fill)
        ctx.stroke()