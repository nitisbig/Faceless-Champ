"""Pillow frame execution over the shared plan and owned raster painter."""

from __future__ import annotations

from collections import OrderedDict

from PIL import Image as PILImage

from .._rendering.raster import RasterPainter
from ..components import finite
from ..timeline import Renderable, Scene


class PillowRenderer(RasterPainter):
    def __init__(self, antialias=2, *, frame_cache_mb=64, caption_cache_mb=32, code_cache_mb=32, arch_session_limit=4):
        if antialias not in (1, 2, 3, 4):
            raise ValueError("antialias must be 1, 2, 3, or 4")
        self.antialias = antialias
        self._scene_frames = OrderedDict()
        self._frame_cache_limit = round(finite(frame_cache_mb, "frame_cache_mb", 0) * 1024**2)
        self._frame_cache_bytes = 0
        super().__init__(
            source_cache_mb=frame_cache_mb,
            caption_cache_mb=caption_cache_mb,
            code_cache_mb=code_cache_mb,
            arch_session_limit=arch_session_limit,
        )
        self._effect_session = None
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            if self._effect_session is not None:
                device, raster, _ = self._effect_session
                try:
                    raster.close()
                finally:
                    device.close()
                    self._effect_session = None
        finally:
            try:
                super().close()
            finally:
                self._scene_frames.clear()
                self._frame_cache_bytes = 0

    def validate(self, node, *, backend="pillow"):
        if self._closed:
            raise RuntimeError("PillowRenderer is closed")
        super().validate(node, backend=backend)

    def frame(self, node: Renderable, time: float, size: tuple[int, int]) -> PILImage.Image:
        if self._closed:
            raise RuntimeError("PillowRenderer is closed")
        from ..effects import needs_compositor

        if needs_compositor(node):
            if self._effect_session is None:
                from .._compositor import Compositor
                from .._cpu_device import CPUDevice
                from ..backends._raster_adapter import PillowRasterAdapter

                device, raster = CPUDevice(), PillowRasterAdapter()
                self._effect_session = device, raster, Compositor(device, raster, self.antialias)
            return self._effect_session[2].frame(node, time, size)
        if isinstance(node, Scene):
            node.build()
            return self._scene(node, time, size)
        from .._rendering.composition import composition_frame

        return composition_frame(self, node, time, size)

    def _scene(self, scene, time, size):
        from .._rendering.evaluate import evaluate_frame, render_signature
        from ._pillow_paint import paint_scene

        signature = size, render_signature(scene, time, self.measurement)
        cached = self._scene_frames.get(scene)
        if cached is not None and cached[0] == signature:
            self._scene_frames.move_to_end(scene)
            return cached[1].copy()
        frame = evaluate_frame(scene, time, geometry=False)
        result = paint_scene(frame, size, self.antialias, self)
        # One frame per scene within an LRU byte budget. Copies protect caller edits.
        previous = self._scene_frames.pop(scene, None)
        if previous is not None:
            self._frame_cache_bytes -= previous[1].width * previous[1].height * 4
        cost = result.width * result.height * 4
        if cost <= self._frame_cache_limit:
            while self._frame_cache_bytes + cost > self._frame_cache_limit:
                _, (_, old) = self._scene_frames.popitem(last=False)
                self._frame_cache_bytes -= old.width * old.height * 4
            self._scene_frames[scene] = (signature, result.copy())
            self._frame_cache_bytes += cost
        return result
