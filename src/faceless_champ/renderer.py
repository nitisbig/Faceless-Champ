"""Pillow frame renderer with asset caches and bounded frame memory."""

from __future__ import annotations

import math
from collections import OrderedDict
from copy import copy
from functools import wraps
from io import BytesIO
from itertools import pairwise
from typing import Protocol

from PIL import Image as PILImage
from PIL import ImageChops, ImageColor, ImageDraw, ImageFilter, ImageOps

from .arch import ArchChamp
from .charts import Chart
from .charts.drawing import draw_chart
from .chess import ChessChamp
from .components import (
    Arrow,
    Circle,
    Ellipse,
    Equation,
    Icon,
    Image,
    ImageSlot,
    Line,
    Number,
    Polyline,
    Rectangle,
    Shape,
    Text,
    Triangle,
    finite,
)
from .flow import FlowChamp
from .layout import Group, transform_point
from .maps import Map, draw_map
from .motion import style_value
from .os_ui import OSClip
from .playground.playback import PlaygroundView
from .subtitles import Captions
from .timeline import Grid, Layer, Renderable, Scene, Sequence
from .typography import DEFAULT_FONT, load_font
from .web.clip import HtmlClip


class Renderer(Protocol):
    def validate(self, node: Renderable) -> None: ...
    def frame(self, node: Renderable, time: float, size: tuple[int, int]) -> PILImage.Image: ...


def create_renderer(backend="pillow", *, antialias=2, **options):
    """Create an owned renderer. Optional backends are imported only on request."""
    if backend == "pillow":
        return PillowRenderer(antialias, **options)
    if backend == "skia":
        from .backends.skia import SkiaRenderer

        return SkiaRenderer(antialias, **options)
    raise ValueError("backend must be pillow or skia")


def rendering_identity(backend="pillow", node=None):
    """Portable render provenance without importing an optional native library."""
    from importlib.metadata import PackageNotFoundError, version

    if backend not in {"pillow", "skia"}:
        raise ValueError("backend must be pillow or skia")
    packages = ("Pillow",) if backend == "pillow" else ("Pillow", "skia-python", "numpy")
    versions = {}
    for name in packages:
        try:
            versions[name] = version(name)
        except PackageNotFoundError:
            versions[name] = "unavailable"
    identity = {"backend": backend, "versions": versions, "device": "cpu"}
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
            with create_renderer(backend, antialias=aa) as renderer:
                return function(*args, **{**kwargs, "renderer": renderer})

        return owned

    return decorate


class PillowRenderer:
    def __init__(
        self,
        antialias: int = 2,
        *,
        frame_cache_mb: float = 64,
        caption_cache_mb: float = 32,
        code_cache_mb: float = 32,
        arch_session_limit: int = 4,
    ):
        if antialias not in (1, 2, 3, 4):
            raise ValueError("antialias must be 1, 2, 3, or 4")
        self.antialias = antialias
        self._code_sprites = OrderedDict()
        self._code_cache_limit = round(finite(code_cache_mb, "code_cache_mb", 0) * 1024 * 1024)
        self._code_cache_bytes = 0
        self._images = {}
        self._fonts = {}
        self._sprites = {}
        self._equations = {}
        self._math_parser = None
        self._math_vector_parser = None
        self._scene_frames = OrderedDict()
        self._frame_cache_limit = round(finite(frame_cache_mb, "frame_cache_mb", 0) * 1024 * 1024)
        self._frame_cache_bytes = 0
        self._caption_sprites = OrderedDict()
        self._caption_layouts = OrderedDict()
        self._caption_cache_limit = round(finite(caption_cache_mb, "caption_cache_mb", 0) * 1024 * 1024)
        self._caption_cache_bytes = 0
        if isinstance(arch_session_limit, bool) or not isinstance(arch_session_limit, int) or arch_session_limit < 1:
            raise ValueError("arch_session_limit must be a positive integer")
        self._arch_session_limit = arch_session_limit
        self._arch_sessions = OrderedDict()

    def close(self):
        for session in self._arch_sessions.values():
            session.close()
        self._arch_sessions.clear()
        for cache in (
            self._images,
            self._fonts,
            self._sprites,
            self._equations,
            self._scene_frames,
            self._caption_sprites,
            self._caption_layouts,
            self._code_sprites,
        ):
            cache.clear()
        self._frame_cache_bytes = self._caption_cache_bytes = self._code_cache_bytes = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _font(self, component: Text | Captions, size: int):
        path = component.font or DEFAULT_FONT
        weight = getattr(component, "font_weight", None)
        key = (path, size, weight)
        if key not in self._fonts:
            self._fonts[key] = load_font(path, size, weight)
        return self._fonts[key]

    def _image(self, component: Image):
        path = component.path
        if (
            isinstance(component, ImageSlot)
            and path is not None
            and (component.mode == "placeholder" or (component.mode == "auto" and not path.exists()))
        ):
            key = ("placeholder", component)
            if key not in self._images:
                size = (max(1, round(component.width)), max(1, round(component.height)))
                sprite = PILImage.new("RGBA", size, component.placeholder_fill)
                draw = ImageDraw.Draw(sprite)
                draw.rectangle((0, 0, size[0] - 1, size[1] - 1), outline=component.placeholder_stroke, width=2)
                font = load_font(component.placeholder_font, round(component.placeholder_font_size))
                box = draw.multiline_textbbox((0, 0), component.label, font=font, align="center")
                ratio = min(1, (size[0] - 16) / max(1, box[2] - box[0]), (size[1] - 16) / max(1, box[3] - box[1]))
                if ratio < 1:
                    font = load_font(component.placeholder_font, max(1, round(component.placeholder_font_size * ratio)))
                draw.multiline_text(
                    (size[0] / 2, size[1] / 2),
                    component.label,
                    font=font,
                    fill=component.placeholder_color,
                    anchor="mm",
                    align="center",
                )
                self._images[key] = ([sprite], [0.1])
            return self._images[key]
        key = path.resolve() if path is not None else component.source_bytes
        if key not in self._images:
            if path is not None and not path.is_file():
                raise FileNotFoundError(f"Image file not found: {path}")
            if path is not None and path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
                raise ValueError("Images must be PNG, JPEG, WebP, or GIF")
            frames, durations = [], []
            try:
                with PILImage.open(path if path is not None else BytesIO(component.source_bytes)) as source:
                    if source.format not in {"PNG", "JPEG", "WEBP", "GIF"}:
                        raise ValueError("Images must be PNG, JPEG, WebP, or GIF")
                    count = getattr(source, "n_frames", 1) if source.format == "GIF" else 1
                    for index in range(count):
                        source.seek(index)
                        frames.append(ImageOps.exif_transpose(source).convert("RGBA"))
                        durations.append(max(0.01, source.info.get("duration", 100) / 1000))
            except OSError as exc:
                if isinstance(component, ImageSlot):
                    raise ValueError(f"Cannot decode image: {path or 'in-memory source'}") from exc  # noqa: TRY004
                raise
            self._images[key] = (frames, durations)
        return self._images[key]

    def validate(self, node: Renderable, *, backend="pillow") -> None:
        from .gradients import LinearGradient, RadialGradient
        from .paths import VectorPath
        from .surfaces import Surface

        if not isinstance(node, (Scene, Sequence, Grid, Layer)):
            raise TypeError("Expected Scene, Sequence, Grid, or Layer")
        ImageColor.getcolor(node.canvas.bg, "RGBA")
        _ = node.duration
        if isinstance(node, Scene):
            for entry in node.entries:
                c = entry.component
                from .coding import CodingChamp
                from .indicators import ProgressBar

                if c.mask is not None and c.mask.kind == "path" and backend == "pillow":
                    raise ValueError("PathMask requires backend='skia'")
                if isinstance(c, Group) and c.drop_shadow is not None:
                    raise ValueError("Group shadows are not supported; attach a shadow to a surface or leaf")
                if isinstance(c, CodingChamp):
                    continue
                if isinstance(c, ProgressBar):
                    continue
                if isinstance(c, (Group, Surface)):
                    continue
                elif isinstance(c, Map):
                    draw_map(c, entry.initial, min(1, 64 / max(c.width, c.height)))
                elif isinstance(c, Chart):
                    draw_chart(c, entry.initial, 1)
                elif isinstance(c, Equation):
                    ImageColor.getcolor(c.color, "RGBA")
                    self._equation(c, 1)
                elif isinstance(c, (Text, Captions)):
                    if isinstance(c, Text) and c.text_engine == "skia":
                        if backend == "pillow":
                            raise ValueError("Native typography requires backend='skia'")
                        if backend == "skia":
                            from .backends._skia_text import text_size

                            text_size(c, entry.initial)
                    else:
                        self._font(c, round(c.font_size))
                    ImageColor.getcolor(c.color, "RGBA")
                    if isinstance(c, Captions):
                        ImageColor.getcolor(c.highlight_color, "RGBA")
                        ImageColor.getcolor(c.future_color, "RGBA")
                        for phrase in c.phrases:
                            self._caption_sprite(c, 1, phrase[0].start)
                elif isinstance(c, (HtmlClip, OSClip, ChessChamp, PlaygroundView, FlowChamp, ArchChamp)):
                    pass  # Prepared ranges are checked at requested frame time.
                elif isinstance(c, Image):
                    self._image(c)
                    if c.tint is not None:
                        ImageColor.getcolor(c.tint, "RGBA")
                    if isinstance(c, Icon):
                        ImageColor.getcolor(c.color, "RGBA")
                elif isinstance(c, Shape):
                    if isinstance(c, VectorPath) and not c.portable and backend == "pillow":
                        raise ValueError("Compound paths and even_odd fill require backend='skia'")
                    for color in (c.fill, c.stroke):
                        if color is not None and not isinstance(color, (LinearGradient, RadialGradient)):
                            ImageColor.getcolor(color, "RGBA")
                else:
                    raise TypeError(f"Unsupported component: {type(c).__name__}")
        else:
            for child in node.children:
                self.validate(child, backend=backend)

    def frame(self, node: Renderable, time: float, size: tuple[int, int]) -> PILImage.Image:
        if isinstance(node, Scene):
            node.build()
            return self._scene(node, time, size)
        from ._render_state import composition_frame

        return composition_frame(self, node, time, size)

    def _fit(self, node, time, size, bg):
        from ._render_state import fit_frame

        return fit_frame(self, node, time, size, bg)

    def _scene(self, scene, time, size):
        visible = []

        def collect(entries, parents=()):
            for entry in sorted(entries, key=lambda e: e.component.z_index):
                if time < entry.start or (entry.end is not None and time >= entry.end):
                    continue
                state = entry.state_at(time)
                if state["opacity"] <= 0:
                    continue
                if isinstance(entry.component, Group):
                    collect(entry.children, ((entry.component._origin, state),) + parents)
                else:
                    visible.append((entry.component, state, max(0, time - entry.start), parents))

        collect([entry for entry in scene.entries if entry.parent is None])
        signature = (
            scene.canvas,
            size,
            tuple(
                (
                    c,
                    tuple(state.items()),
                    tuple((origin, tuple(parent.items())) for origin, parent in parents),
                    self._caption_state(c, age)
                    if isinstance(c, Captions)
                    else (
                        c.frame_key(age)
                        if isinstance(c, (HtmlClip, OSClip, ChessChamp, PlaygroundView, FlowChamp, ArchChamp))
                        else (age if isinstance(c, Image) and len(self._image(c)[0]) > 1 else None)
                    ),
                )
                for c, state, age, parents in visible
            ),
        )
        cached = self._scene_frames.get(scene)
        if cached is not None and cached[0] == signature:
            self._scene_frames.move_to_end(scene)
            return cached[1].copy()
        aa = self.antialias
        big = (size[0] * aa, size[1] * aa)
        result = PILImage.new("RGBA", big, scene.canvas.bg)
        factor = min(big[0] / scene.canvas.width, big[1] / scene.canvas.height)
        enhanced = any(
            e.component.mask is not None
            or e.component.drop_shadow is not None
            or e.state_at(time)["clip"] != (0, 0, 1, 1)
            or e.state_at(time)["scale_x"] != 1
            or e.state_at(time)["scale_y"] != 1
            for e in scene.entries
        )
        if enhanced:
            result = self._affine_scene(scene, time, big, factor)
        for c, state, age, parents in [] if enhanced else visible:
            sprite = self._sprite(c, state, factor, age)
            w, h = sprite.size
            x, y = state["position"]
            if c.anchor == "top_left":
                # Preserve the existing pixel-rounded unrotated anchor box.
                x += max(1, round(w * state["scale"])) / factor / 2
                y += max(1, round(h * state["scale"])) / factor / 2
            scale = state["scale"]
            rotation, opacity = state["rotation"], state["opacity"]
            for origin, parent in parents:
                x, y = transform_point((x, y), origin, parent)
                scale *= parent["scale"]
                rotation += parent["rotation"]
                opacity *= parent["opacity"]
            if scale != 1:
                sprite = sprite.resize(
                    (max(1, round(w * scale)), max(1, round(h * scale))), PILImage.Resampling.LANCZOS
                )
            x, y = x * factor, y * factor
            if rotation:
                sprite = sprite.rotate(-rotation, resample=PILImage.Resampling.BICUBIC, expand=True)
            if opacity < 1:
                sprite = sprite.copy()
                sprite.putalpha(sprite.getchannel("A").point(lambda a, opacity=opacity: round(a * opacity)))
            result.alpha_composite(sprite, (round(x - sprite.width / 2), round(y - sprite.height / 2)))
        if aa > 1:
            result = result.resize(size, PILImage.Resampling.LANCZOS)
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

    def _affine_scene(self, scene, time, size, factor):
        from .layout import Bounds
        from .motion import inverse, matrix, multiply, point

        base = (factor, 0, 0, factor, 0, 0)

        def warp(sprite, transform):
            return sprite.transform(
                size, PILImage.Transform.AFFINE, inverse(transform), resample=PILImage.Resampling.BICUBIC
            )

        def visit(entry, parent, inherited_opacity=1):
            c, state = entry.component, entry.state_at(time)
            layer = PILImage.new("RGBA", size)
            if isinstance(c, Group) and c.drop_shadow is not None:
                raise ValueError("Group shadows are not supported; attach a shadow to a surface or leaf")
            if time < entry.start or (entry.end is not None and time >= entry.end) or state["opacity"] <= 0:
                return layer
            if isinstance(c, Group):
                world = multiply(parent, matrix(state, c._origin))
                for child in sorted(entry.children, key=lambda e: e.component.z_index):
                    layer.alpha_composite(visit(child, world, inherited_opacity * state["opacity"]))
                if state["clip"] != (0, 0, 1, 1):

                    def evaluated(child):
                        view = copy(child.component)
                        for key, value in child.state_at(time).items():
                            if hasattr(view, key):
                                setattr(
                                    view,
                                    key,
                                    style_value(key, value),
                                )
                        if isinstance(view, Group):
                            view._children = tuple(evaluated(e) for e in child.children)
                        return view

                    boxes = [evaluated(child).bounds for child in entry.children]
                    box = Bounds(
                        min(b.left for b in boxes),
                        min(b.top for b in boxes),
                        max(b.right for b in boxes),
                        max(b.bottom for b in boxes),
                    )
                local_center = c._origin
            else:
                sprite = self._sprite(c, state, factor, max(0, time - entry.start))
                w, h = sprite.width / factor, sprite.height / factor
                local = dict(state)
                if c.anchor == "top_left":
                    local["position"] = (
                        state["position"][0] + w * state["scale"] * state["scale_x"] / 2,
                        state["position"][1] + h * state["scale"] * state["scale_y"] / 2,
                    )
                world = multiply(parent, matrix(local))
                raster = multiply(world, (1 / factor, 0, 0, 1 / factor, -w / 2, -h / 2))
                layer = warp(sprite, raster)
                box = Bounds(-w / 2, -h / 2, w / 2, h / 2)
                local_center = (0, 0)

            def apply_mask(points):
                mask = PILImage.new("L", size)
                draw = ImageDraw.Draw(mask)
                if points:
                    draw.polygon([point(world, x, y) for x, y in points], fill=255)
                layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))

            if c.mask is not None:
                if c.mask.kind == "path":
                    raise ValueError("PathMask requires backend='skia'")
                mw, mh = state["mask_width"], state["mask_height"]
                mx, my = state["mask_position"]
                mx += local_center[0]
                my += local_center[1]
                if not mw or not mh:
                    points = []
                elif c.mask.kind == "ellipse":
                    points = [
                        (mx + mw / 2 * math.cos(i * math.tau / 180), my + mh / 2 * math.sin(i * math.tau / 180))
                        for i in range(180)
                    ]
                else:
                    normalized = c.mask.points if c.mask.kind == "polygon" else ((0, 0), (1, 0), (1, 1), (0, 1))
                    points = [(mx + (x - 0.5) * mw, my + (y - 0.5) * mh) for x, y in normalized]
                apply_mask(points)
            if state["clip"] != (0, 0, 1, 1):
                l, t, r, b = state["clip"]
                apply_mask(
                    []
                    if l == r or t == b
                    else [
                        (box.left + x * box.width, box.top + y * box.height)
                        for x, y in ((l, t), (r, t), (r, b), (l, b))
                    ]
                )
            if c.drop_shadow is not None:
                from ._portable import guard_size

                guard_size(size)
                shadow = c.drop_shadow
                a, b, cc, d, _, _ = world
                dx, dy = shadow.offset
                offset = (a * dx + cc * dy, b * dx + d * dy)
                alpha = layer.getchannel("A").filter(
                    ImageFilter.GaussianBlur(shadow.blur * max(math.hypot(a, b), math.hypot(cc, d)))
                )
                alpha = alpha.transform(
                    size,
                    PILImage.Transform.AFFINE,
                    (1, 0, -offset[0], 0, 1, -offset[1]),
                    resample=PILImage.Resampling.BICUBIC,
                )
                color = ImageColor.getcolor(shadow.color, "RGBA")
                cast = PILImage.new("RGBA", size, (*color[:3], 255))
                cast.putalpha(alpha.point(lambda v: round(v * color[3] / 255)))
                cast.alpha_composite(layer)
                layer = cast
            opacity = inherited_opacity * state["opacity"]
            if not isinstance(c, Group) and opacity < 1:
                layer.putalpha(layer.getchannel("A").point(lambda a: round(a * opacity)))
            return layer

        result = PILImage.new("RGBA", size, scene.canvas.bg)
        for entry in sorted((e for e in scene.entries if e.parent is None), key=lambda e: e.component.z_index):
            result.alpha_composite(visit(entry, base))
        return result

    def _sprite(self, c, state, factor, age):
        from .gradients import LinearGradient, RadialGradient
        from .paths import VectorPath
        from .surfaces import Surface

        if isinstance(c, Text) and c.text_engine == "skia":
            raise ValueError("Native typography requires backend='skia'")
        if isinstance(c, (Surface, VectorPath)) or (
            isinstance(c, Shape) and isinstance(state["fill"], (LinearGradient, RadialGradient))
        ):
            from ._portable import shape_sprite, surface_sprite

            static = state["draw"] == 1 and all(
                state.get(k) == v
                for k, v in c.state().items()
                if k in {"fill", "stroke", "width", "height", "stroke_width"}
            )
            key = (c, factor, "retained")
            if static and key in self._sprites:
                return self._sprites[key]
            sprite = surface_sprite(c, factor) if isinstance(c, Surface) else shape_sprite(c, state, factor)
            if static:
                self._sprites[key] = sprite
            return sprite
        return self._base_sprite(c, state, factor, age)

    def _base_sprite(self, c, state, factor, age):
        from .coding import CodingChamp, draw_code
        from .indicators import ProgressBar, draw_indicator

        if isinstance(c, CodingChamp):
            return draw_code(c, state, factor, self)

        if isinstance(c, ArchChamp):
            from .arch.rendering import ArchSession

            key = (c, factor)
            session = self._arch_sessions.pop(key, None)
            if session is None:
                while len(self._arch_sessions) >= self._arch_session_limit:
                    self._arch_sessions.popitem(last=False)[1].close()
                session = ArchSession(c, factor)
            self._arch_sessions[key] = session
            return session.frame(age)
        if isinstance(c, (HtmlClip, OSClip, ChessChamp, PlaygroundView, FlowChamp)):
            return c.frame_image(age, factor)
        if isinstance(c, ProgressBar):
            return draw_indicator(c, state, factor, self)
        # A temporary style view avoids mutating snapshots and retaining intermediate sprites.
        dynamic = any(
            key in state and state[key] != value
            for key, value in c.state().items()
            if key in {"fill", "stroke", "color", "width", "height", "stroke_width", "corner_radius"}
        )
        if dynamic:
            original = c
            c = copy(c)
            for key in ("fill", "stroke", "color", "width", "height", "stroke_width", "corner_radius"):
                if key in state:
                    value = state[key]
                    setattr(c, key, style_value(key, value))
            if isinstance(c, Polyline):
                c.points = tuple((x * c.width / original.width, y * c.height / original.height) for x, y in c.points)
        else:
            dynamic = False

        if isinstance(c, Map):
            return draw_map(c, state, factor)
        if isinstance(c, Chart):
            # The bounded scene-frame cache handles holds; never retain per-frame chart sprites.
            return draw_chart(c, state, factor)
        if isinstance(c, Captions):
            return self._caption_sprite(c, factor, age)
        if isinstance(c, Number):
            font = self._font(c, max(1, round(c.font_size * factor)))
            text = c.format(state["value"])
            d = ImageDraw.Draw(PILImage.new("RGBA", (1, 1)))
            box = d.textbbox((0, 0), text or " ", font=font)
            text_width = math.ceil(box[2] - box[0])
            width = text_width if c.width is None else round(c.width * factor)
            if width < text_width:
                raise ValueError("Number text exceeds its fixed width")
            sprite = PILImage.new("RGBA", (max(1, width) + 4, max(1, math.ceil(box[3] - box[1])) + 4))
            x = 0 if c.align == "left" else (width - text_width if c.align == "right" else (width - text_width) / 2)
            visible = text[: math.floor(len(text) * state["reveal"] + 1e-9)]
            ImageDraw.Draw(sprite).text((x + 2 - box[0], 2 - box[1]), visible, font=font, fill=c.color)
            return sprite
        # Dynamic reveal/draw frames are deliberately not retained in the cache.
        static = not dynamic and state["reveal"] == 1 and state["draw"] == 1
        frame_index = 0
        if isinstance(c, Image):
            frames, durations = self._image(c)
            clock = age % sum(durations)
            for frame_index, duration in enumerate(durations):
                if clock < duration:
                    break
                clock -= duration
        key = (c, factor, frame_index)
        if static and key in self._sprites:
            return self._sprites[key]
        if isinstance(c, Equation):
            sprite = self._equation(c, factor)
            if state["reveal"] < 1:
                visible = max(0, min(sprite.width, math.floor(sprite.width * state["reveal"])))
                revealed = PILImage.new("RGBA", sprite.size)
                if visible:
                    revealed.paste(sprite.crop((0, 0, visible, sprite.height)), (0, 0))
                sprite = revealed
        elif isinstance(c, Text):
            font = self._font(c, max(1, round(c.font_size * factor)))
            spacing = round(c.spacing * factor)
            draw = ImageDraw.Draw(PILImage.new("RGBA", (1, 1)))
            box = draw.multiline_textbbox((0, 0), c.text or " ", font=font, spacing=spacing, align=c.align)
            sprite = PILImage.new(
                "RGBA", (max(1, math.ceil(box[2] - box[0]) + 4), max(1, math.ceil(box[3] - box[1]) + 4))
            )
            text = c.text[: math.floor(len(c.text) * state["reveal"] + 1e-9)]
            ImageDraw.Draw(sprite).multiline_text(
                (2 - box[0], 2 - box[1]), text, font=font, fill=c.color, spacing=spacing, align=c.align
            )
        elif isinstance(c, Image):
            size = (max(1, round(c.width * factor)), max(1, round(c.height * factor)))
            source = frames[frame_index]
            if c.trim:
                # Use a union across frames to prevent animated assets from wobbling.
                boxes = [frame.getchannel("A").getbbox() for frame in frames]
                boxes = [box for box in boxes if box is not None]
                if boxes:
                    box = (
                        min(b[0] for b in boxes),
                        min(b[1] for b in boxes),
                        max(b[2] for b in boxes),
                        max(b[3] for b in boxes),
                    )
                    source = source.crop(box)
            tint = c.color if isinstance(c, Icon) else c.tint
            if tint is not None:
                alpha = source.getchannel("A")
                source = PILImage.new("RGBA", source.size, tint)
                tint_alpha = ImageColor.getcolor(tint, "RGBA")[3]
                source.putalpha(alpha.point(lambda a: round(a * tint_alpha / 255)))
            if c.fit == "cover":
                sprite = ImageOps.fit(source, size, method=PILImage.Resampling.LANCZOS)
            else:
                fit = ImageOps.contain(source, size, method=PILImage.Resampling.LANCZOS)
                sprite = PILImage.new("RGBA", size)
                sprite.alpha_composite(fit, ((size[0] - fit.width) // 2, (size[1] - fit.height) // 2))
        elif isinstance(c, Arrow):
            width = max(1, round(c.stroke_width * factor))
            length, tip = c.width * factor, c.tip_size * factor
            pad = math.ceil(tip + width)
            sprite = PILImage.new("RGBA", (math.ceil(length) + pad * 2 + 1, pad * 2 + 1))
            progress = max(0, min(1, state["draw"]))
            if c.stroke and c.stroke_width > 0 and progress > 0:
                draw = ImageDraw.Draw(sprite)
                end = pad + length * progress
                draw.line([(pad, pad), (end, pad)], fill=c.stroke, width=width)
                visible_tip = tip * min(1, max(0, (progress - 0.85) / 0.15))
                if visible_tip:
                    draw.polygon(
                        [
                            (end, pad),
                            (end - visible_tip, pad - visible_tip / 2),
                            (end - visible_tip, pad + visible_tip / 2),
                        ],
                        fill=c.stroke,
                    )
        else:
            width = max(1, round(c.stroke_width * factor))
            w, h = max(1, round(c.width * factor)), max(1, round(c.height * factor))
            sprite = PILImage.new("RGBA", (w + width * 2, h + width * 2))
            draw = ImageDraw.Draw(sprite)
            x, y = width, width
            if isinstance(c, Polyline):
                points = [(x + px * factor, y + py * factor) for px, py in c.points]
                if c.closed:
                    points.append(points[0])
            elif isinstance(c, Rectangle) and c.corner_radius:
                radius = min(c.corner_radius, c.width / 2, c.height / 2) * factor
                points = []
                for cx, cy, start in (
                    (x + w - radius, y + radius, -90),
                    (x + w - radius, y + h - radius, 0),
                    (x + radius, y + h - radius, 90),
                    (x + radius, y + radius, 180),
                ):
                    for step in range(13):
                        angle = math.radians(start + step * 90 / 12)
                        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
                points.append(points[0])
            elif isinstance(c, (Circle, Ellipse)):
                points = [
                    (
                        x + w / 2 + w / 2 * math.cos(a * math.tau / 180 - math.pi / 2),
                        y + h / 2 + h / 2 * math.sin(a * math.tau / 180 - math.pi / 2),
                    )
                    for a in range(181)
                ]
            elif isinstance(c, Triangle):
                points = [(x + w / 2, y), (x + w, y + h), (x, y + h), (x + w / 2, y)]
            elif isinstance(c, Line):
                points = [(x, y), (x + w, y)]
            else:
                points = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
            progress = max(0, min(1, state["draw"]))
            can_fill = not isinstance(c, Line) and (not isinstance(c, Polyline) or c.closed)
            if c.fill and can_fill and progress >= 1:
                draw.polygon(points, fill=c.fill)
            if c.stroke and c.stroke_width > 0 and progress > 0:
                lengths = [
                    b[0] - a[0] if isinstance(c, Polyline) and c.draw_by == "x" else math.dist(a, b)
                    for a, b in pairwise(points)
                ]
                remaining = sum(lengths) * progress
                visible = [points[0]]
                for a, b, length in zip(points, points[1:], lengths):
                    if remaining >= length:
                        visible.append(b)
                        remaining -= length
                    else:
                        ratio = remaining / length if length else 0
                        visible.append((a[0] + (b[0] - a[0]) * ratio, a[1] + (b[1] - a[1]) * ratio))
                        break
                draw.line(visible, fill=c.stroke, width=width, joint="curve")
                if isinstance(c, Polyline) and c.line_cap == "round" and not c.closed:
                    radius = width / 2
                    for px, py in (visible[0], visible[-1]):
                        draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=c.stroke)
        if static:
            self._sprites[key] = sprite
        return sprite

    def _equation(self, c: Equation, factor: float):
        key = (c.expression, c.font_size, c.fontset, c.color, c.max_width, tuple(sorted(c.color_map.items())), factor)
        if key in self._equations:
            return self._equations[key]
        try:
            import numpy as np
            from matplotlib import rc_context
            from matplotlib.font_manager import FontProperties
            from matplotlib.mathtext import MathTextParser
        except ImportError as exc:
            raise RuntimeError(
                "Equation requires the equations extra: install 'faceless-champ[equations]' "
                "or run 'uv sync --extra equations' in this checkout"
            ) from exc
        if self._math_parser is None:
            self._math_parser = MathTextParser("agg")
        with rc_context({"mathtext.default": "it"}):
            try:
                prop = FontProperties(size=max(1, c.font_size * factor), math_fontfamily=c.fontset)
                if c.color_map:
                    sprite = self._colored_equation(c, prop)
                else:
                    parsed = self._math_parser.parse(f"${c.expression}$", dpi=72, prop=prop)
            except ValueError as exc:
                raise ValueError(f"Invalid Equation {c.expression!r}: {exc}") from exc
        if not c.color_map:
            mask = PILImage.fromarray(np.asarray(parsed.image).copy())
            color = ImageColor.getcolor(c.color, "RGBA")
            sprite = PILImage.new("RGBA", mask.size, color)
            if color[3] != 255:
                mask = mask.point(lambda alpha: round(alpha * color[3] / 255))
            sprite.putalpha(mask)
        box = sprite.getbbox()
        if box:
            sprite = sprite.crop(box)
        if c.max_width is not None and sprite.width > c.max_width * factor:
            ratio = c.max_width * factor / sprite.width
            sprite = sprite.resize(
                (max(1, round(sprite.width * ratio)), max(1, round(sprite.height * ratio))), PILImage.Resampling.LANCZOS
            )
        self._equations[key] = sprite
        return sprite

    def _colored_equation(self, c, prop):
        """Color positioned math glyphs after typesetting the complete expression."""
        import numpy as np
        from matplotlib import ft2font
        from matplotlib.backends.backend_agg import RendererAgg
        from matplotlib.mathtext import MathTextParser
        from matplotlib.path import Path as MathPath
        from matplotlib.transforms import Affine2D, Bbox

        if self._math_vector_parser is None:
            self._math_vector_parser = MathTextParser("path")
        parser = self._math_vector_parser
        base = tuple(v / 255 for v in ImageColor.getcolor(c.color, "RGBA"))
        colors = {}
        for symbol, color in c.color_map.items():
            parsed_symbol = parser.parse(f"${symbol}$", dpi=72, prop=prop)
            if len(parsed_symbol.glyphs) != 1 or parsed_symbol.rects:
                raise ValueError(f"color_map key {symbol!r} must represent one math glyph")
            code = parsed_symbol.glyphs[0][2]
            rgba = tuple(v / 255 for v in ImageColor.getcolor(color, "RGBA"))
            if code in colors and colors[code] != rgba:
                raise ValueError(f"color_map contains conflicting aliases for {symbol!r}")
            colors[code] = rgba
        parsed = parser.parse(f"${c.expression}$", dpi=72, prop=prop)
        paths = []
        flags = ft2font.LoadFlags.NO_HINTING if hasattr(ft2font, "LoadFlags") else ft2font.LOAD_NO_HINTING
        for glyph in parsed.glyphs:
            font, size, code = glyph[:3]
            x, y = glyph[-2:]
            font.set_size(size, 72)
            # Matplotlib 3.11 includes the glyph index; 3.9/3.10 return five fields.
            if len(glyph) == 6:
                font.load_glyph(glyph[3], flags=flags)
            else:
                font.load_char(code, flags=flags)
            vertices, codes = font.get_path()
            if len(vertices):
                path = MathPath(vertices, codes).transformed(Affine2D().translate(x, y))
                paths.append((path, colors.get(code, base)))
        for x, y, width, height in parsed.rects:
            path = MathPath.unit_rectangle().transformed(Affine2D().scale(width, height).translate(x, y))
            paths.append((path, base))
        if not paths:
            return PILImage.new("RGBA", (1, 1))
        bounds = Bbox.union([path.get_extents() for path, _ in paths])
        left, bottom = math.floor(bounds.x0), math.floor(bounds.y0)
        renderer = RendererAgg(math.ceil(bounds.x1 - left) + 4, math.ceil(bounds.y1 - bottom) + 4, 72)
        gc = renderer.new_gc()
        gc.set_linewidth(0)
        gc.set_antialiased(True)
        transform = Affine2D().translate(2 - left, 2 - bottom)
        for path, rgba in paths:
            renderer.draw_path(gc, path, transform, rgbFace=rgba)
        gc.restore()
        return PILImage.fromarray(np.asarray(renderer.buffer_rgba()).copy())

    @staticmethod
    def _caption_state(c: Captions, age: float):
        phrase = c.phrase_at(age)
        if not phrase:
            return None
        active = c.track.active_at(age)
        finished = sum(cue.end <= age for cue in phrase)
        return (phrase[0].index, active.index if active else None, finished)

    def _caption_layout(self, c: Captions, factor: float, phrase):
        key = (c, factor, phrase[0].index)
        if key in self._caption_layouts:
            self._caption_layouts.move_to_end(key)
            return self._caption_layouts[key]
        font = self._font(c, max(1, round(c.font_size * factor)))
        width = max(1, round(c.width * factor))
        space = font.getlength(" ")
        lines, line, used = [], [], 0.0
        for cue in phrase:
            for word in cue.text.split():
                length = font.getlength(word)
                if length + 4 > width:
                    raise ValueError(f"Caption word {word!r} exceeds width; increase width or reduce font_size")
                if line and used + space + length + 4 > width:
                    lines.append((line, used))
                    line, used = [], 0.0
                if line:
                    used += space
                line.append((word, cue, length))
                used += length
        if line:
            lines.append((line, used))
        ascent, descent = font.getmetrics()
        step = ascent + descent + round(c.spacing * factor)
        layout = (font, width, lines, ascent, step)
        if self._caption_cache_limit:
            if len(self._caption_layouts) >= 128:
                self._caption_layouts.popitem(last=False)
            self._caption_layouts[key] = layout
        return layout

    def _caption_sprite(self, c: Captions, factor: float, age: float):
        state = self._caption_state(c, age)
        if state is None:
            return PILImage.new("RGBA", (1, 1))
        key = (c, factor, state)
        if key in self._caption_sprites:
            self._caption_sprites.move_to_end(key)
            return self._caption_sprites[key]
        phrase = c.phrase_at(age)
        active = c.track.active_at(age)
        font, width, lines, ascent, step = self._caption_layout(c, factor, phrase)
        space = font.getlength(" ")
        sprite = PILImage.new("RGBA", (width, step * len(lines) + 4))
        draw = ImageDraw.Draw(sprite)
        for row, (words, length) in enumerate(lines):
            x = (width - length) / 2
            for word, cue, word_length in words:
                color = c.highlight_color if active == cue else (c.color if age >= cue.end else c.future_color)
                draw.text((x, 2 + ascent + row * step), word, font=font, fill=color, anchor="ls")
                x += word_length + space
        cost = sprite.width * sprite.height * 4
        if cost <= self._caption_cache_limit:
            while self._caption_cache_bytes + cost > self._caption_cache_limit:
                _, old = self._caption_sprites.popitem(last=False)
                self._caption_cache_bytes -= old.width * old.height * 4
            self._caption_sprites[key] = sprite
            self._caption_cache_bytes += cost
        return sprite
