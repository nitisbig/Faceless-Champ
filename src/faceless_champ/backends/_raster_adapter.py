"""One adapter to existing specialist raster producers and their owned sessions."""

from ..renderer import PillowRenderer


class PillowRasterAdapter:
    def __init__(self, limit_mb=64, arch_session_limit=4):
        self.renderer = PillowRenderer(
            1, frame_cache_mb=0, caption_cache_mb=16, code_cache_mb=16, arch_session_limit=arch_session_limit
        )
        self.limit = round(limit_mb * 1024**2)
        self.text_session = None

    def sprite(self, c, state, factor, age):
        result = self.renderer._sprite(c, state, factor, age)
        # Bound newly retained compatibility sprites/assets without altering the
        # legacy Pillow renderer's cache policy. Large sources bypass retention.
        for name in ("_sprites", "_equations"):
            cache = getattr(self.renderer, name)
            total = sum(v.width * v.height * 4 for v in cache.values())
            while total > self.limit and cache:
                old = cache.pop(next(iter(cache)))
                total -= old.width * old.height * 4
        cache = self.renderer._images
        total = sum(sum(im.width * im.height * 4 for im in frames) for frames, _ in cache.values())
        while total > self.limit and cache:
            frames, _ = cache.pop(next(iter(cache)))
            total -= sum(im.width * im.height * 4 for im in frames)
        while len(self.renderer._fonts) > 128:
            self.renderer._fonts.pop(next(iter(self.renderer._fonts)))
        return result

    def native_text_size(self, c, state):
        if self.text_session is not None:
            return self.text_session.layout(c, state)[0]
        from ._skia_text import text_size

        return text_size(c, state)

    def close(self):
        self.renderer.close()
