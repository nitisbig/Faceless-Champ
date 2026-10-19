"""Optional headless compositor. Native imports occur only on construction."""

import hashlib
import sys
import threading
from importlib.resources import files

from .._render_state import ByteCache
from ..gpu import GPUOptions
from ..timeline import Scene


class ModernGLRenderer:
    def __init__(self, antialias=1, *, gpu=None):
        if antialias not in (1, 2, 3, 4):
            raise ValueError("antialias must be 1, 2, 3, or 4")
        if gpu is not None and not isinstance(gpu, GPUOptions):
            raise TypeError("gpu must be GPUOptions or None")
        self.gpu, self.antialias = gpu or GPUOptions(), antialias
        self._thread = threading.get_ident()
        self._closed = False
        self.ctx = self.device = self.raster = None
        self.frames = ByteCache(round(self.gpu.frame_cache_mb * 1024**2))
        try:
            import moderngl

            from .._compositor import Compositor
            from ._gl.device import GLDevice
            from ._raster_adapter import PillowRasterAdapter

            options = (
                {"backend": "egl"} if self.gpu.context_backend == "egl" or sys.platform.startswith("linux") else {}
            )
            if self.gpu.device_index is not None:
                options["device_index"] = self.gpu.device_index
            self.ctx = moderngl.create_standalone_context(require=330, **options)
            self.device = GLDevice(self.ctx, moderngl, self.gpu)
            self.raster = PillowRasterAdapter(64, isolate_arch=True)
            self.compositor = Compositor(self.device, self.raster, antialias)
            # Exercise the floating-point target now, before the exporter starts.
            with self.device.surface((2, 2)):
                pass
            with self.ctx:
                info = self.ctx.info
            driver = " ".join(str(info.get(k, "")) for k in ("GL_VENDOR", "GL_RENDERER", "GL_VERSION"))
            resource = files("faceless_champ.backends._gl").joinpath("shaders")
            digest = hashlib.sha256(
                b"".join(p.read_bytes() for p in sorted(resource.iterdir(), key=lambda p: p.name))
            ).hexdigest()
            self.identity = {
                "backend": "moderngl",
                "resolved": True,
                "device": "software"
                if any(word in driver.lower() for word in ("llvmpipe", "softpipe", "swrast", "software", "swiftshader"))
                else "gpu",
                "vendor": info.get("GL_VENDOR"),
                "renderer": info.get("GL_RENDERER"),
                "driver": info.get("GL_VERSION"),
                "context_backend": options.get("backend", "native"),
                "shader_hash": digest,
                "color_pipeline": "encoded-srgb-composition/linear-effects-v1",
            }
            self.stats = self.device.stats
            self.stats["frame_cache_hits"] = 0
        except BaseException as exc:
            self.close()
            if not isinstance(exc, Exception):
                raise
            raise RuntimeError(
                "ModernGL backend unavailable. Install faceless-champ[gpu]; on Linux provide "
                "working EGL/OpenGL drivers. Use backend='auto' for fidelity-preserving fallback. "
                f"Details: {exc}"
            ) from exc

    def _check(self):
        if threading.get_ident() != self._thread:
            raise RuntimeError("ModernGLRenderer must be used and closed on its owning thread")
        if self._closed:
            raise RuntimeError("ModernGLRenderer is closed")

    def __enter__(self):
        self._check()
        return self

    def __exit__(self, *exc):
        self.close()

    def validate(self, node):
        self._check()
        self.raster.renderer.validate(node, backend="skia")

    def _signature(self, node, time):
        if isinstance(node, Scene):
            node.build()
            return (
                node.canvas,
                tuple(
                    (
                        e.component,
                        e.start,
                        e.end,
                        e.start <= time and (e.end is None or time < e.end),
                        tuple(e.state_at(time).items()),
                        self.raster.renderer_age_key(e.component, max(0, time - e.start)),
                        max(0, time - e.start)
                        if e.component.effects is not None
                        and (e.component.effects.distortion is not None or e.component.effects.light_sweep is not None)
                        else None,
                    )
                    for e in node.entries
                ),
            )
        from .._composition_plan import composition_plan

        parts, progress = composition_plan(node, time, (node.canvas.width, node.canvas.height))
        return (
            node.canvas,
            progress,
            getattr(node, "transition", None),
            getattr(node, "effects", None),
            time
            if getattr(getattr(node, "effects", None), "light_sweep", None)
            or getattr(getattr(node, "effects", None), "distortion", None)
            else None,
            tuple((p.viewport, p.background, self._signature(p.node, p.time)) for p in parts),
        )

    def frame(self, node, time, size):
        self._check()
        import math

        from .._portable import guard_size

        if not math.isfinite(time):
            raise ValueError("Frame time must be finite")
        guard_size(size)
        signature = size, self._signature(node, time)
        cached = self.frames.get(node)
        if cached is not None and cached[0] == signature:
            self.stats["frame_cache_hits"] += 1
            return cached[1].copy()
        frame = self.compositor.frame(node, time, size)
        cost = size[0] * size[1] * 4
        if cost <= self.frames.limit:
            self.frames.put(node, (signature, frame.copy()), cost)
        return frame

    def close(self):
        if self._closed:
            return
        if threading.get_ident() != self._thread:
            raise RuntimeError("ModernGLRenderer must be closed on its owning thread")
        if self.raster is not None:
            self.raster.close()
        if self.device is not None:
            self.device.close()
        if self.ctx is not None:
            self.ctx.release()
        self.frames.clear()
        self._closed = True


__all__ = ["ModernGLRenderer"]
