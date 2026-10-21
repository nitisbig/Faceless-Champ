"""One adapter to existing specialist raster producers and their owned sessions."""

from contextlib import ExitStack

from .._rendering.raster import RasterPainter


class PillowRasterAdapter:
    def __init__(self, limit_mb=64, arch_session_limit=4, *, isolate_arch=False):
        self.painter = RasterPainter(
            source_cache_mb=0,
            raster_cache_mb=limit_mb,
            caption_cache_mb=16,
            code_cache_mb=16,
            arch_session_limit=arch_session_limit,
        )
        self.text_session = None
        self._owns_text = False
        self.painter.isolate_sources = isolate_arch

    @property
    def measurement(self):
        return self.painter.measurement

    def sprite(self, c, state, factor, age):
        from ..components import Text
        from ..paths import VectorPath

        if (isinstance(c, Text) and c.text_engine == "skia") or (isinstance(c, VectorPath) and not c.portable):
            result = self._native_sprite(c, state, factor)
        else:
            result = self.painter.sprite(c, state, factor, age)
        return result

    def _native_sprite(self, c, state, factor):
        import math

        from .._portable import guard_size
        from ..components import Text
        from ._native import image_to_pillow, load_skia
        from ._skia_paint import draw_shape

        s = load_skia()
        if isinstance(c, Text):
            if self.text_session is None:
                from ._skia_text import TextSession

                self.text_session, self._owns_text = TextSession(), True
            width, height = self.text_session.layout(c, state)[0]
        else:
            sw = max(1, round(state["stroke_width"]))
            width, height = math.ceil(state["width"]) + 2 * sw, math.ceil(state["height"]) + 2 * sw
        size = max(1, math.ceil(width * factor)), max(1, math.ceil(height * factor))
        guard_size(size)
        surface = s.Surface(*size)
        canvas = surface.getCanvas()
        canvas.scale(factor, factor)
        if isinstance(c, Text):
            self.text_session.paint(canvas, c, state)
        else:
            canvas.translate(width / 2, height / 2)
            draw_shape(s, canvas, c, state, 1)
        return image_to_pillow(surface.makeImageSnapshot(), s)

    def native_text_size(self, c, state):
        if self.text_session is not None:
            return self.text_session.layout(c, state)[0]
        from ._skia_text import text_size

        return text_size(c, state)

    def close(self):
        with ExitStack() as cleanup:
            if self._owns_text:
                cleanup.callback(self.text_session.close)
                self._owns_text = False
            cleanup.callback(self.painter.close)
