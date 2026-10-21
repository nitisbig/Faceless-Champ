"""Approved networking surfaces and motion, owned by the authoring kit."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from math import ceil
from pathlib import Path
from types import MappingProxyType

from faceless_champ.animation import Animation, linear, smooth
from faceless_champ.components import Component, Image, Rectangle, Text, finite
from faceless_champ.layout import Bounds, Group, transform_point
from faceless_champ.surfaces import ShadowStyle, card_surface
from faceless_champ.typography import CLEAN_FLOW_FONT, fit_text
from PIL import ImageColor

from facelesschamp_kit.diagrams.clip import FlowChamp
from facelesschamp_kit.diagrams.model import FlowGraph, FlowTheme
from facelesschamp_kit.diagrams.script import FlowScript

_ASSET_ROOT = Path(__file__).resolve().parent / "assets" / "networking"
_ICONS = ("laptop", "router", "internet", "cloud", "server", "dns", "lock_tls", "packet")
_PALETTE = {
    "background": "#F4F6FB",
    "surface": "#FFFFFF",
    "ink": "#172A4D",
    "muted": "#56677F",
    "blue": "#2563EB",
    "violet": "#7C3AED",
    "teal": "#08765F",
    "pale_blue": "#E9F0FF",
    "pale_violet": "#F0EAFE",
    "pale_teal": "#E1F5EF",
    "wire": "#BBC9E0",
}
_SHADOW = ShadowStyle(color="#29477619", blur=10, offset=(0, 8))
_SAMPLE_RATE = 30
_DEFAULT_BOUNDS = Bounds(0, 0, 1920, 1080)


def _point(value, name):
    try:
        result = tuple(finite(item, name) for item in value)
    except TypeError as exc:
        raise ValueError(f"{name} needs two finite coordinates") from exc
    if len(result) != 2:
        raise ValueError(f"{name} needs two finite coordinates")
    return result


def _positive(value, name):
    value = finite(value, name)
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _text(value, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be text")
    return value


def _box(center, size, padding=0):
    x, y = center
    width, height = size
    return Bounds(x - width / 2 - padding, y - height / 2 - padding, x + width / 2 + padding, y + height / 2 + padding)


def _rounded(center, size, fill, radius=18):
    return Rectangle(
        width=size[0],
        height=size[1],
        corner_radius=min(radius, min(size) / 2),
        position=center,
        fill=fill,
        stroke=None,
        stroke_width=0,
    )


def _frames(frames):
    try:
        result = tuple(
            (
                finite(progress, "frame progress", 0),
                _point(position, "frame position"),
                finite(scale, "frame scale", 0.001),
            )
            for progress, position, scale in frames
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("frames need finite (progress, position, scale) triples") from exc
    if len(result) < 2 or result[0][0] != 0 or result[-1][0] != 1:
        raise ValueError("frames must start at progress 0 and end at 1")
    if any(a[0] >= b[0] for a, b in pairwise(result)):
        raise ValueError("frame progress must increase strictly")
    return result


class FlowVisual(Group):
    """A transformable flow surface with named parts and a face-centered pivot.

    ``bounds`` includes allocated shadow clearance. ``face_bounds`` follows the
    visual's initial transforms and excludes that clearance. Parts are ordinary
    components and can be animated independently before or after grouping.
    """

    def __init__(self, parts, face_bounds, **kwargs):
        if not isinstance(face_bounds, Bounds):
            raise TypeError("face_bounds must be Bounds")
        self._parts = dict(parts)
        self._face_bounds = face_bounds
        kwargs.setdefault("position", face_bounds.center)
        super().__init__(*self._parts.values(), **kwargs)
        self._origin = face_bounds.center

    @property
    def parts(self):
        return MappingProxyType(self._parts)

    @property
    def face_bounds(self):
        box = self._face_bounds
        points = tuple(
            transform_point(point, self._origin, self.state())
            for point in ((box.left, box.top), (box.right, box.top), (box.right, box.bottom), (box.left, box.bottom))
        )
        return Bounds(
            min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points), max(p[1] for p in points)
        )


@dataclass(frozen=True)
class FlowDesign:
    """The approved rounded networking design, in reference canvas pixels.

    The preset is explicit: existing FlowChamp themes and diagrams retain their
    appearance. Supplied artwork is bundled with the library for offline use.
    """

    name: str = "networking"
    font: str = CLEAN_FLOW_FONT
    surface_mode: str = "raster"
    text_engine: str = "pillow"

    def __post_init__(self):
        if self.surface_mode not in {"raster", "vector"} or self.text_engine not in {"pillow", "skia"}:
            raise ValueError("surface_mode must be raster/vector and text_engine pillow/skia")
        if self.name != "networking":
            raise ValueError("Unknown flow design; use networking")
        if not isinstance(self.font, (str, Path)) or not str(self.font):
            raise ValueError("font must be a font name or path")
        object.__setattr__(self, "font", str(self.font))

    def __deepcopy__(self, memo):
        # Stored fields are immutable strings. Palette and shadow are read-only.
        return self

    @classmethod
    def named(cls, name, **kwargs):
        return cls(name=name, **kwargs)

    @property
    def palette(self):
        return MappingProxyType(_PALETTE)

    @property
    def shadow(self):
        return _SHADOW

    @property
    def shadow_padding(self):
        return 38

    @staticmethod
    def icon_path(name):
        """Resolve a bundled icon, accepting ``router``, ``router_icon.png``, etc."""
        if not isinstance(name, str):
            raise TypeError("icon name must be text")
        stem = name.removesuffix(".png").removesuffix("_icon")
        if stem not in _ICONS:
            raise ValueError(f"Unknown networking icon: {name!r}; choose {', '.join(_ICONS)}")
        return _ASSET_ROOT / f"{stem}_icon.png"

    @property
    def asset_paths(self):
        return tuple(self.icon_path(name) for name in _ICONS)

    def _label(self, value, center, width, height, size=28, color=None, weight=600, minimum=None):
        return fit_text(
            value,
            _box(center, (width, height)),
            font=self.font,
            font_size=size,
            min_font_size=minimum or size,
            font_weight=weight,
            color=color or self.palette["ink"],
            spacing=3,
            text_engine=self.text_engine,
        )

    def _icon(self, name, center, size):
        return Image(self.icon_path(name), width=size[0], height=size[1], position=center, trim=True)

    def node_card(self, label, *, icon, position=(0, 0), size=(240, 260), detail=None, address=None):
        """Compose an asset card; an optional address enables the client layout."""
        _text(label, "label")
        if detail is not None:
            _text(detail, "detail")
        if address is not None:
            _text(address, "address")
        center, size = _point(position, "position"), _point(size, "size")
        width, height = size
        if width <= 118 or height <= 80:
            raise ValueError("card size needs width > 118 and height > 80 design pixels")
        self.icon_path(icon)
        x, y = center
        top = y - height / 2
        allocated = _box(center, size, self.shadow_padding)
        face = card_surface(
            allocated, fill=self.palette["surface"], radius=34, shadow=self.shadow, render_mode=self.surface_mode
        )
        title_height = 70 if "\n" in label else 44
        title_y = top + (53 if "\n" in label else 37)
        title = self._label(
            label, (x, title_y), width - 32, title_height, size=32 if address is not None else 28, minimum=26
        )
        named = {"surface": face, "label": title}
        detail_label = None
        if detail:
            compact = height <= 190 and address is None
            detail_label = self._label(
                detail,
                (x + 42, y + 23) if compact else (x, y + height / 2 - 35),
                width - 118 if compact else width - 28,
                34,
                size=22 if width < 300 else 24,
                minimum=22,
                color=self.palette["muted"],
                weight=500,
            )
        if address is not None:
            named["address"] = Group(
                _rounded((x, top + 91), (width - 56, 46), self.palette["pale_blue"], radius=23),
                self._label(address, (x, top + 91), width - 82, 36, size=24, color=self.palette["blue"], weight=550),
            )
            image_top = named["address"].bounds.bottom + 8
            image_bottom = detail_label.bounds.top - 8 if detail_label is not None else top + height - 16
            if image_bottom - image_top < 1:
                raise ValueError("card height leaves no space for artwork below the address")
            artwork = self._icon(
                icon, (x, (image_top + image_bottom) / 2), (width - 10, min(260, image_bottom - image_top))
            )
        elif height <= 190 and detail:
            title.move_to(x + 50, y - 26)
            artwork = self._icon(icon, (x - 73, y + 3), (138, 124))
        else:
            image_width = min(width + 24, 290)
            image_height = min(height - 67, image_width * 0.73)
            artwork = self._icon(icon, (x, y + (2 if detail or height >= 300 else 15)), (image_width, image_height))
        named["icon"] = artwork
        if detail_label is not None:
            named["detail"] = detail_label
        return FlowVisual(named, _box(center, size))

    def popup(self, kind, value, position=(0, 0)):
        """A compact protocol pill and large value with matching icon artwork."""
        kind, value = _text(kind, "kind").upper(), _text(value, "value")
        x, y = center = _point(position, "position")
        secure = kind in {"TLS", "HTTPS"}
        color = self.palette["teal" if secure else "violet" if kind == "DNS" else "blue"]
        pale = self.palette["pale_teal" if secure else "pale_violet" if kind == "DNS" else "pale_blue"]
        icon = "lock_tls" if secure else "dns" if kind == "DNS" else "packet"
        allocated = _box(center, (540, 156), self.shadow_padding)
        pill_width = max(84, 28 + len(kind) * 13)
        pill_center = (x - 81 + pill_width / 2, y - 39)
        named = {
            "surface": card_surface(
                allocated, fill=self.palette["surface"], radius=36, shadow=self.shadow, render_mode=self.surface_mode
            ),
            "icon": self._icon(icon, (x - 200, y - 1), (132, 122)),
            "kind": Group(
                _rounded(pill_center, (pill_width, 32), pale, radius=16),
                Text(
                    kind,
                    font=self.font,
                    font_size=20,
                    font_weight=650,
                    color=color,
                    position=pill_center,
                    text_engine=self.text_engine,
                ),
            ),
            "value": self._label(value, (x + 64, y + 16), 344, 58, size=34, minimum=32, weight=600),
        }
        return FlowVisual(named, _box(center, (540, 156)))

    def packet_marker(self, position=(0, 0), color=None):
        """A 30 by 18 capsule, soft lift and glossy upper edge."""
        x, y = center = _point(position, "position")
        color = self.palette["blue"] if color is None else color
        ImageColor.getcolor(color, "RGBA")
        shadow = card_surface(
            _box(center, (30, 18), 12),
            fill=color,
            radius=9,
            shadow=ShadowStyle(color="#29477620", blur=3, offset=(0, 3)),
            render_mode=self.surface_mode,
        )
        highlight = _rounded((x, y - 4), (18, 3), "#FFFFFFA6", radius=1.5)
        return FlowVisual({"surface": shadow, "highlight": highlight}, _box(center, (30, 18)))

    def backdrop(self, bounds=_DEFAULT_BOUNDS):
        """Place the approved blue, violet and teal wash within explicit bounds."""
        if not isinstance(bounds, Bounds):
            raise TypeError("backdrop bounds must be Bounds")
        if bounds.width < 1 or bounds.height < 1:
            raise ValueError("backdrop bounds need at least one pixel per side")
        return Image(
            _ASSET_ROOT / "backdrop.png", width=bounds.width, height=bounds.height, position=bounds.center, fit="cover"
        )

    @staticmethod
    def pop_frames(position, scale=1, duration=1):
        """Sample the approved subtle overshoot, lift and settle at 30 Hz."""
        x, y = _point(position, "position")
        scale, duration = finite(scale, "scale", 0.001), _positive(duration, "duration")
        count = ceil(duration * _SAMPLE_RATE)
        frames = []
        for index in range(count + 1):
            progress = index / count
            if progress <= 0.68:
                p = smooth(progress / 0.68)
                ratio, dy = 0.90 + 0.126 * p, 22 - 25 * p
            else:
                p = smooth((progress - 0.68) / 0.32)
                ratio, dy = 1.026 - 0.026 * p, -3 + 3 * p
            frames.append((progress, (x, y + dy), scale * ratio))
        return tuple(frames)

    @staticmethod
    def move_frames(source, destination, source_scale=1, destination_scale=1, duration=1):
        """Sample a zero-acceleration, continuous layout transition at 30 Hz."""
        source, destination = _point(source, "source"), _point(destination, "destination")
        source_scale = finite(source_scale, "source_scale", 0.001)
        destination_scale = finite(destination_scale, "destination_scale", 0.001)
        count = ceil(_positive(duration, "duration") * _SAMPLE_RATE)
        frames = []
        for index in range(count + 1):
            progress = index / count
            weight = progress**3 * (10 + progress * (-15 + 6 * progress))
            frames.append(
                (
                    progress,
                    tuple(a + (b - a) * weight for a, b in zip(source, destination)),
                    source_scale + (destination_scale - source_scale) * weight,
                )
            )
        return tuple(frames)

    @staticmethod
    def apply_transform(script, target, frames, *, at=0, duration=1):
        """Apply shared motion samples to FlowScript atomically.

        Stage the node at the first frame before the window. Visible card and
        hidden graph proxy can then consume exactly the same motion samples.
        """
        if not isinstance(script, FlowScript):
            raise TypeError("script must be FlowScript")
        frames = _frames(frames)
        at, duration = finite(at, "at", 0), _positive(duration, "duration")
        trial = FlowScript.from_dict(script.to_dict())
        for (t0, _, _), (t1, position, scale) in pairwise(frames):
            trial.move(target, position, at=at + t0 * duration, duration=(t1 - t0) * duration)
            trial.scale(target, scale, at=at + t0 * duration, duration=(t1 - t0) * duration)
        script._actions = list(trial.actions)
        return script

    @staticmethod
    def transform_animation(component, frames, *, offset=(0, 0)):
        """Animate a core component from the exact samples used by its proxy."""
        if not isinstance(component, Component):
            raise TypeError("component must be a Component")
        frames, offset = _frames(frames), _point(offset, "offset")

        def world(position):
            return tuple(a + b for a, b in zip(position, offset))

        return Animation(
            component,
            {"position": world(frames[-1][1]), "scale": frames[-1][2]},
            starts={"position": world(frames[0][1]), "scale": frames[0][2]},
            keyframes={
                "position": tuple((t, world(p)) for t, p, _ in frames),
                "scale": tuple((t, scale) for t, _, scale in frames),
            },
            rate_func=linear,
        )

    def connection_theme(self, stroke_width=4.5):
        """Neutral cables with invisible node proxies and stable focus width."""
        return FlowTheme(
            background="#00000000",
            surface="#00000000",
            foreground="#00000000",
            stroke=self.palette["wire"],
            node_stroke="#00000000",
            highlight_width=0,
            accent=self.palette["blue"],
            font=self.font,
            font_size=30,
            minimum_font_size=24,
            stroke_width=stroke_width,
        )

    def signal(self, script, targets, *, at=None, duration=1, direction="forward", color=None, fade=0.2):
        """Send a native capsule with an eased cable accent, atomically.

        Configure traffic before calling ``complete_connections``. Existing
        explicit highlights retain their overlap validation and are not removed.
        """
        if not isinstance(script, FlowScript):
            raise TypeError("script must be FlowScript")
        duration = _positive(duration, "duration")
        fade = min(finite(fade, "fade", 0), duration / 2)
        at = script.duration if at is None else finite(at, "at", 0)
        color = self.palette["teal" if direction == "reverse" else "blue"] if color is None else color
        ImageColor.getcolor(color, "RGBA")
        trial = FlowScript.from_dict(script.to_dict())
        trial.signal(targets, at=at, duration=duration, direction=direction, marker="capsule", color=color)

        def mix(first, second, weight):
            a, b = ImageColor.getcolor(first, "RGBA"), ImageColor.getcolor(second, "RGBA")
            return "#" + "".join(f"{round(x + (y - x) * weight):02X}" for x, y in zip(a, b))

        if fade:
            count = 6
            for index in range(count):
                weight = smooth((index + 1) / count)
                trial.highlight(
                    targets,
                    at=at + fade * index / count,
                    duration=fade / count,
                    color=mix(self.palette["wire"], color, weight),
                )
                trial.highlight(
                    targets,
                    at=at + duration - fade + fade * index / count,
                    duration=fade / count,
                    color=mix(color, self.palette["wire"], weight),
                )
        if duration > 2 * fade:
            trial.highlight(targets, at=at + fade, duration=duration - 2 * fade, color=color)
        script._actions = list(trial.actions)
        return script

    def complete_connections(self, script, edges, duration):
        """Fill uncovered cable-color intervals without replacing authored focus.

        Both edge objects and edge IDs are accepted. The operation is atomic and
        idempotent; its horizon must include every authored script action.
        """
        if not isinstance(script, FlowScript):
            raise TypeError("script must be FlowScript")
        duration = _positive(duration, "duration")
        if script.duration > duration + 1e-9:
            raise ValueError("connection duration must include the authored script")
        ids = tuple(getattr(edge, "id", edge) for edge in edges)
        if any(not isinstance(id, str) or not id.strip() for id in ids) or len(set(ids)) != len(ids):
            raise ValueError("edges must contain unique edge IDs")
        trial = FlowScript.from_dict(script.to_dict())
        for id in ids:
            occupied = sorted(
                (
                    action.at + action.targets.index(id) * action.options.get("stagger", 0),
                    action.at + action.targets.index(id) * action.options.get("stagger", 0) + action.duration,
                )
                for action in script.actions
                if action.kind == "highlight" and id in action.targets
            )
            cursor = 0.0
            for start, end in (*occupied, (duration, duration)):
                if start - cursor > 1e-9:
                    trial.highlight(id, at=cursor, duration=start - cursor, color=self.palette["wire"])
                cursor = max(cursor, end)
        script._actions = list(trial.actions)
        return script

    def connections(self, graph, script=None, *, width=1600, height=900, source_start=0, **component_kwargs):
        """Compose bound fine cables and their subtle glow as fresh core clips.

        Edges remain neutral outside authored highlights, including static clips
        and final holds. The caller's script and duration remain unchanged.
        Signals appear only in the foreground diagram layer.
        """
        if not isinstance(graph, FlowGraph):
            raise TypeError("graph must be FlowGraph")
        if script is not None and not isinstance(script, FlowScript):
            raise TypeError("script must be FlowScript or None")
        script = FlowScript.from_dict(script.to_dict()) if script is not None else FlowScript()
        width, height = _positive(width, "width"), _positive(height, "height")
        source_start = finite(source_start, "source_start", 0)
        center = (width / 2, height / 2)
        glow_script = FlowScript.from_dict(
            {"actions": [action for action in script.to_dict()["actions"] if action["kind"] != "signal"]}
        )
        parts = {
            "glow": FlowChamp(
                graph,
                glow_script,
                width=width,
                height=height,
                theme=self.connection_theme(18),
                source_start=min(source_start, glow_script.duration),
                position=center,
                opacity=0.11,
            ),
            "diagram": FlowChamp(
                graph,
                script,
                width=width,
                height=height,
                theme=self.connection_theme(),
                source_start=source_start,
                position=center,
            ),
        }
        return FlowVisual(parts, Bounds(0, 0, width, height), **component_kwargs)
