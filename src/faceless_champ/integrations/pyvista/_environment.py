"""Preserve host floating-point state around VTK rendering."""

from contextlib import contextmanager
from functools import lru_cache


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
