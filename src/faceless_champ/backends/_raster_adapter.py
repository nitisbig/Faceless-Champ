"""One adapter to existing specialist raster producers and their owned sessions."""

from contextlib import contextmanager
from functools import lru_cache

from ..renderer import PillowRenderer


@lru_cache(maxsize=1)
def _fenv_api():
    """Look up the host's optional C99 floating-point environment API lazily."""
    import ctypes

    try:
        process = ctypes.CDLL(None)
        get, put = process.fegetenv, process.fesetenv
    except (AttributeError, OSError):
        return None
    for function in (get, put):
        function.argtypes = (ctypes.c_void_p,)
        function.restype = ctypes.c_int
    return get, put


@contextmanager
def _preserve_float_environment():
    # VTK capped clipping can leave floating-point exception status behind.
    # Native Skia curves/text can disappear afterwards on Linux x86. Preserve
    # the complete caller environment, including status, rather than changing
    # its rounding mode or assuming which exception constants a host uses.
    api = _fenv_api()
    if api is None:
        yield
        return
    import ctypes

    # fenv_t is opaque. Overallocate aligned storage (the supported POSIX host
    # layouts use at most a few hundred bytes), without encoding its ABI fields.
    environment = (ctypes.c_longdouble * 128)()
    get, put = api
    saved = get(ctypes.byref(environment)) == 0
    try:
        yield
    finally:
        if saved:
            put(ctypes.byref(environment))


class PillowRasterAdapter:
    def __init__(self, limit_mb=64, arch_session_limit=4):
        self.renderer = PillowRenderer(
            1, frame_cache_mb=0, caption_cache_mb=16, code_cache_mb=16, arch_session_limit=arch_session_limit
        )
        self.limit = round(limit_mb * 1024**2)
        self.text_session = None

    def sprite(self, c, state, factor, age):
        from ..arch import ArchChamp

        if isinstance(c, ArchChamp):
            with _preserve_float_environment():
                result = self.renderer._sprite(c, state, factor, age)
        else:
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
