"""Optional GPU configuration and explicit capability probing; no native imports."""

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version

from .components import finite


@dataclass(frozen=True)
class GPUOptions:
    context_backend: str = "auto"
    device_index: int | None = None
    texture_cache_mb: float = 256
    working_mb: float = 512
    frame_cache_mb: float = 64

    def __post_init__(self):
        if self.context_backend not in {"auto", "egl"}:
            raise ValueError("context_backend must be auto or egl")
        if self.device_index is not None and (
            isinstance(self.device_index, bool) or not isinstance(self.device_index, int) or self.device_index < 0
        ):
            raise ValueError("device_index must be a nonnegative integer")
        for name in ("texture_cache_mb", "working_mb", "frame_cache_mb"):
            object.__setattr__(self, name, finite(getattr(self, name), name, 1 if name == "working_mb" else 0))


def renderer_capabilities(backend="moderngl", *, probe=False, gpu=None):
    """Describe contracts offline. Only probe=True may create a native context."""
    if backend not in {"pillow", "skia", "moderngl", "auto"}:
        raise ValueError("Unknown rendering backend")
    packages = {"pillow": ("Pillow",), "skia": ("skia-python",), "moderngl": ("moderngl", "glcontext", "numpy")}
    versions = {}
    for name in packages.get(backend, ("Pillow", "skia-python", "moderngl", "glcontext", "numpy")):
        try:
            versions[name] = version(name)
        except PackageNotFoundError:
            versions[name] = "unavailable"
    result = {
        "backend": backend,
        "versions": versions,
        "probed": False,
        "installed": all(v != "unavailable" for v in versions.values()) if backend != "auto" else True,
        "features": ["composition", "masks", "effects", "procedural", "particles", "transitions"],
        "unsupported_features": ["native_text", "compound_paths", "path_masks"] if backend == "pillow" else [],
    }
    if probe and backend in {"moderngl", "auto"}:
        from .backends.moderngl import ModernGLRenderer

        try:
            with ModernGLRenderer(1, gpu=gpu) as renderer:
                result.update(renderer.identity, available=True)
        except (RuntimeError, ValueError, OSError) as exc:
            result.update(available=False, error=str(exc))
        result["probed"] = True
    return result


__all__ = ["GPUOptions", "renderer_capabilities"]
