"""Public renderer protocol, factories, provenance and compatibility aliases."""

from __future__ import annotations

from functools import wraps
from typing import Protocol

from PIL import Image as PILImage

from .backends.pillow import PillowRenderer
from .components import Text
from .subtitles import Captions
from .timeline import Renderable, Scene
from .typography import DEFAULT_FONT

# Preserve the defining public path for pickles, discovery and legacy adapters.
PillowRenderer.__module__ = __name__


class Renderer(Protocol):
    def validate(self, node: Renderable) -> None: ...
    def frame(self, node: Renderable, time: float, size: tuple[int, int]) -> PILImage.Image: ...


def create_renderer(backend="pillow", *, antialias=2, **options):
    """Create an owned renderer. Optional backends are imported only on request."""
    gpu = options.pop("gpu", None)
    if backend == "pillow":
        return PillowRenderer(antialias, **options)
    if backend == "skia":
        from .backends.skia import SkiaRenderer

        return SkiaRenderer(antialias, **options)
    if backend == "moderngl":
        from .backends.moderngl import ModernGLRenderer

        return ModernGLRenderer(antialias, gpu=gpu, **options)
    if backend == "auto":
        from .backends._auto import AutoRenderer

        return AutoRenderer(antialias, gpu=gpu, **options)
    raise ValueError("backend must be pillow, skia, moderngl or auto")


def rendering_identity(backend="pillow", node=None, *, renderer=None):
    """Portable render provenance without importing an optional native library."""
    from importlib.metadata import PackageNotFoundError, version

    if backend not in {"pillow", "skia", "moderngl", "auto"}:
        raise ValueError("backend must be pillow, skia, moderngl or auto")
    requested = backend
    runtime = getattr(renderer, "identity", None)
    if runtime is not None:
        backend = runtime.get("backend", backend)
    packages = (
        ("Pillow",)
        if backend == "pillow"
        else ("Pillow", "skia-python", "numpy")
        if backend == "skia"
        else ("Pillow", "moderngl", "glcontext", "numpy")
    )
    versions = {}
    for name in packages:
        try:
            versions[name] = version(name)
        except PackageNotFoundError:
            versions[name] = "unavailable"
    identity = {"backend": backend, "versions": versions, "device": "cpu"}
    if runtime is not None:
        identity.update(runtime)
    elif backend in {"moderngl", "auto"}:
        identity.update(device="unresolved", resolved=False)
    if requested in {"moderngl", "auto"}:
        identity["requested_backend"] = requested
    if node is not None:
        import hashlib
        from pathlib import Path

        from .surfaces import Surface

        fonts, engines, surfaces = {}, set(), set()

        def visit(current):
            _ = current.duration
            if isinstance(current, Scene):
                for entry in current.entries:
                    c = entry.component
                    if isinstance(c, (Text, Captions)):
                        path = Path(c.font or DEFAULT_FONT).resolve()
                        if str(path) not in fonts:
                            fonts[str(path)] = (
                                hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "missing"
                            )
                        engines.add(getattr(c, "text_engine", "pillow"))
                    if isinstance(c, Surface):
                        surfaces.add("vector")
            else:
                for child in current.children:
                    visit(child)

        visit(node)
        identity.update(fonts=fonts, text_engines=sorted(engines), retained_surfaces=sorted(surfaces))
    return identity


def validate_composition(node):
    """Validate authoring/assets without selecting or loading an optional backend."""
    with PillowRenderer(1) as renderer:
        renderer.validate(node, backend="structural")


def managed_renderer(antialias=1):
    """Close renderers created by an export/preview helper, including failures."""

    def decorate(function):
        @wraps(function)
        def owned(*args, **kwargs):
            if kwargs.get("renderer") is not None:
                return function(*args, **kwargs)
            settings = kwargs.get("settings")
            aa = settings.antialias if settings is not None else kwargs.get("antialias", antialias)
            backend = settings.backend if settings is not None else kwargs.get("backend", "pillow")
            gpu = settings.gpu if settings is not None else kwargs.get("gpu")
            with create_renderer(backend, antialias=aa, gpu=gpu) as renderer:
                return function(*args, **{**kwargs, "renderer": renderer})

        return owned

    return decorate
