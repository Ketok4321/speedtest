import cairo
import math

from gi.repository import GObject, Gtk, Adw

@Gtk.Template(resource_path="/xyz/ketok/Speedtest/ui/gauge.ui")
class Gauge(Gtk.Box):
    __gtype_name__ = "Gauge"

    drawing_area = Gtk.Template.Child()

    gradient_1 = Gtk.Template.Child()
    gradient_2 = Gtk.Template.Child()

    label = GObject.Property(type=str)
    value = GObject.Property(type=str, default="...")

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

    def draw(self, da, ctx, width, height):
        IS_LIGHT = not Adw.StyleManager.get_default().get_dark()
        
        ARC_SIZE = min(width, height) * 0.85

        ARC_START = 0.75 * math.pi
        ARC_LENGTH = 1.5 * math.pi

        ARC_THICKNESS = ARC_SIZE * 0.125

        ARC_CENTER = height / 2 + ARC_THICKNESS / 2

        def gdk_color_to_tuple(color):
            return color.red, color.green, color.blue, color.alpha

        UNFILLED_COLOR = 0, 0, 0, 0.1 if IS_LIGHT else 0.3
        FILLED_COLOR_1 = gdk_color_to_tuple(self.gradient_1.get_style_context().get_color())
        FILLED_COLOR_2 = gdk_color_to_tuple(self.gradient_2.get_style_context().get_color())

        ctx.set_line_width(ARC_THICKNESS)

        ctx.set_source_rgba(*UNFILLED_COLOR)
        ctx.arc(width / 2, ARC_CENTER, ARC_SIZE / 2, ARC_START, ARC_START + ARC_LENGTH)
        ctx.stroke()

        filled = cairo.LinearGradient(0.0, 0.0, 0.0, height)
        filled.add_color_stop_rgba(height, *FILLED_COLOR_1)
        filled.add_color_stop_rgba(0, *FILLED_COLOR_2)

        ctx.set_source(filled)
        ctx.arc(width / 2, ARC_CENTER, ARC_SIZE / 2, ARC_START, ARC_START + ARC_LENGTH * self.fill)
        ctx.stroke()

Gauge.set_css_name("gauge")