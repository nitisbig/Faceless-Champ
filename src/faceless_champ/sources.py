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
