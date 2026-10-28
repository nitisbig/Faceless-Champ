"""Raster integrations: immutable input descriptors and renderer-owned sessions.

Descriptors must be deepcopy-safe and contain inputs, never live native handles.
Sessions return independent straight-alpha RGBA/sRGB Pillow images at opened size.
``frame_key`` is pure content identity; it never replaces the sampling timestamp.
"""

from __future__ import annotations

from collections.abc import Hashable
from copy import deepcopy
from dataclasses import dataclass, field
from itertools import count
from numbers import Real
from typing import Protocol

from PIL.Image import Image

from .components import Component, finite


class RasterSession(Protocol):
    def frame(self, source_time: float) -> Image: ...

    def close(self) -> None: ...


class RasterSource(Protocol):
    intrinsic_size: tuple[int, int]
    duration: float | None
    fingerprint: str
    requirements: tuple[str, ...]

    def frame_key(self, source_time: float) -> Hashable: ...

    def open(self, size: tuple[int, int]) -> RasterSession: ...


class Viewport(Component):
    """Place a raster source on the scene clock without advancing the cursor."""

    def __init__(self, source: RasterSource, *, width=None, height=None, source_start=0, **kwargs):
        super().__init__(**kwargs)
        size = getattr(source, "intrinsic_size", None)
        if (
            not isinstance(size, tuple)
            or len(size) != 2
            or any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in size)
        ):
            raise ValueError("Source intrinsic_size must be two positive integers")
        if not hasattr(source, "duration"):
            raise TypeError("Source needs duration (positive seconds or None)")
        duration = source.duration
        if duration is not None and (isinstance(duration, bool) or not isinstance(duration, Real)):
            raise TypeError("Source duration must be numeric seconds or None")
        if duration is not None and finite(duration, "source duration", 0) == 0:
            raise ValueError("source duration must be positive or None")
        if not isinstance(getattr(source, "fingerprint", None), str) or not source.fingerprint:
            raise ValueError("Source needs a nonempty fingerprint")
        requirements = getattr(source, "requirements", None)
        if not isinstance(requirements, tuple) or any(not isinstance(r, str) for r in requirements):
            raise ValueError("Source requirements must be a tuple of strings")
        if not callable(getattr(source, "frame_key", None)) or not callable(getattr(source, "open", None)):
            raise TypeError("Source needs frame_key() and open()")
        if (width is None) != (height is None):
            raise ValueError("Specify both width and height, or neither")
        self.width = finite(size[0] if width is None else width, "width", 0.001)
        self.height = finite(size[1] if height is None else height, "height", 0.001)
        self.source_start = finite(source_start, "source_start", 0)
        if duration is not None and self.source_start > duration:
            raise ValueError("source_start exceeds source duration")
        self.source = source

    def source_time(self, age):
        time = self.source_start + max(0, finite(age, "component age"))
        return min(time, self.source.duration) if self.source.duration is not None else time

    def frame_key(self, age):
        return self.source.fingerprint, self.source.frame_key(self.source_time(age))


_legacy_identities = count()


@dataclass(frozen=True, eq=False)
class _LegacySource:
    """Private bridge; legacy domain endpoint/quantization policies stay authoritative."""

    component: object
    _identity: int = field(default_factory=lambda: next(_legacy_identities), repr=False)

    @property
    def intrinsic_size(self):
        return max(1, round(self.component.width)), max(1, round(self.component.height))

    @property
    def duration(self):
        duration = getattr(self.component, "duration", None)
        if duration is None:
            return None
        remaining = duration - getattr(self.component, "source_start", 0)
        return remaining if remaining > 0 else None

    @property
    def fingerprint(self):
        identity = getattr(self.component, "fingerprint", None)
        return str(identity) if identity is not None else f"legacy:{type(self.component).__module__}:{self._identity}"

    @property
    def requirements(self):
        return tuple(getattr(self.component, "raster_requirements", ()))

    def frame_key(self, source_time):
        return self.component.frame_key(source_time)

    def open(self, size):
        from .backends._raster_adapter import PillowRasterAdapter

        component = deepcopy(self.component)
        adapter = PillowRasterAdapter(isolate_arch=True)

        class Session:
            def frame(self, source_time):
                result = adapter.sprite(component, component.state(), size[0] / component.width, source_time)
                return result.copy() if result.size == size else result.resize(size)

            def close(self):
                adapter.close()

        return Session()


def source_from_component(component):
    """Internal descriptor bridge for existing fixed domain viewports."""
    return _LegacySource(component)


# ---------------------------------------------------------------------------
# Function-based sources
# ---------------------------------------------------------------------------


def _code_identity(fn) -> str:
    """Stable identity for a function: module, qualified name, bytecode and constants."""
    import hashlib

    target = getattr(fn, "__func__", fn)
    code = getattr(target, "__code__", None)
    parts = [getattr(target, "__module__", ""), getattr(target, "__qualname__", type(target).__qualname__)]
    if code is not None:
        parts += [code.co_code.hex(), repr(code.co_consts), repr(code.co_names)]
        for cell in getattr(target, "__closure__", None) or ():
            try:
                parts.append(repr(cell.cell_contents))
            except ValueError:
                parts.append("<empty>")
    else:
        parts.append(repr(target))
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:24]


def _to_rgba(result, size):
    """Convert a PIL image or numpy array (HxW, HxWx3/4; uint8 or floats 0-1) to RGBA at size."""
    from PIL import Image as PILImage

    if isinstance(result, PILImage.Image):
        image = result
    else:
        try:
            import numpy as np
        except ImportError as exc:  # pragma: no cover - numpy is optional
            raise TypeError("frame functions must return a PIL image (numpy is not installed)") from exc
        array = np.asarray(result)
        if array.dtype.kind == "f":
            array = (np.clip(array, 0, 1) * 255).round()
        array = array.astype("uint8")
        if array.ndim == 2:
            image = PILImage.fromarray(array, "L")
        elif array.ndim == 3 and array.shape[2] in (3, 4):
            image = PILImage.fromarray(array, "RGBA" if array.shape[2] == 4 else "RGB")
        else:
            raise TypeError("frame arrays must be HxW, HxWx3 or HxWx4")
    image = image.convert("RGBA")
    if image.size != tuple(size):
        image = image.resize(tuple(size), PILImage.Resampling.LANCZOS)
    return image


class FunctionSource:
    """A RasterSource from a plain function ``fn(t, size) -> PIL image | numpy array``.

    ``t`` is the source time in seconds; ``size`` is the requested pixel size
    (width, height). Return pixels at that size, or any size (they are resized).
    Wrap it in a Viewport to place it::

        def plasma(t, size):
            ...return an image...

        view = Viewport(FunctionSource(plasma, size=(640, 360), duration=6), width=960, height=540)

    ``fps`` quantizes time so identical frames are cached (None renders every
    sample). ``key`` should change when the function depends on outside data;
    by default the identity comes from the function's code and closure values.
    ``setup(size)`` may return per-session state passed as ``fn(t, size, state)``.
    """

    def __init__(
        self,
        fn,
        *,
        size=(640, 360),
        duration=None,
        fps=None,
        key=None,
        setup=None,
        requirements=(),
        name=None,
    ):
        if not callable(fn):
            raise TypeError("FunctionSource needs a callable fn(t, size)")
        if setup is not None and not callable(setup):
            raise TypeError("setup must be callable")
        if len(size) != 2 or any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in size):
            raise ValueError("size must be two positive integers")
        if duration is not None and finite(duration, "duration", 0) == 0:
            raise ValueError("duration must be positive or None")
        if fps is not None:
            fps = finite(fps, "fps", 0.000001)
        if not isinstance(requirements, tuple) or any(not isinstance(r, str) for r in requirements):
            raise ValueError("requirements must be a tuple of strings")
        self.fn, self.setup = fn, setup
        self.intrinsic_size = (int(size[0]), int(size[1]))
        self.duration = None if duration is None else float(duration)
        self.fps = fps
        self.requirements = requirements
        self.name = name or getattr(fn, "__name__", "function")
        identity = _code_identity(fn) + (_code_identity(setup) if setup else "")
        self.fingerprint = f"function:{self.name}:{identity}:{key!r}:{self.fps}"

    def __deepcopy__(self, memo):
        # Functions are immutable inputs; share them instead of copying closures.
        return self

    def __repr__(self):
        return f"FunctionSource({self.name}, size={self.intrinsic_size}, duration={self.duration}, fps={self.fps})"

    def frame_key(self, source_time):
        if self.fps is None:
            return round(float(source_time), 6)
        return round(float(source_time) * self.fps + 1e-9)

    def _time(self, source_time):
        return self.frame_key(source_time) / self.fps if self.fps is not None else float(source_time)

    def open(self, size):
        size = (int(size[0]), int(size[1]))
        source = self
        state = self.setup(size) if self.setup is not None else None

        class Session:
            def frame(self, source_time):
                t = source._time(source_time)
                result = source.fn(t, size) if source.setup is None else source.fn(t, size, state)
                if result is None:
                    raise ValueError(f"{source.name} returned None; return a PIL image or numpy array")
                return _to_rgba(result, size)

            def close(self):
                close = getattr(state, "close", None)
                if callable(close):
                    close()

        return Session()

    def viewport(self, **kwargs):
        """A Viewport showing this source (accepts Viewport/Component options)."""
        return Viewport(self, **kwargs)


def raster_source(*, size=(640, 360), duration=None, fps=None, key=None, setup=None, requirements=()):
    """Decorator turning ``fn(t, size)`` into a FunctionSource::

    @raster_source(size=(800, 450), duration=4, fps=30)
    def waves(t, size):
        ...
    """

    def wrap(fn):
        return FunctionSource(
            fn, size=size, duration=duration, fps=fps, key=key, setup=setup, requirements=requirements
        )

    return wrap
