"""Ready-made, theme-aware building blocks agents otherwise re-implement per scene.

Every primitive returns an ordinary Component (often a Group), so it can be
positioned, animated, revealed and grouped like anything else. Composite
primitives expose named parts, e.g. ``callout.label`` or ``pill.background``.
Colors default to the active Theme (``Theme.use()``) or the midnight theme, and
accept role names such as "primary" or "muted".

    with Theme.named("neon").use():
        ring = Arc((960, 540), 220, sweep=270, color="primary", width=14)
        tag = Pill("NEW", (960, 300))
        note = Callout("Peak load", target=(1210, 610))
        stat = Stat(98, "percent uptime", (960, 540), suffix="%")
"""

from __future__ import annotations

import math
from typing import Any

from .colors import readable_color, relative_luminance, with_alpha
from .components import Circle, Component, Number, Polyline, Rectangle, Text, finite
from .layout import Bounds, Group
from .theme import current_theme


def _color(value, default_role):
    theme = current_theme()
    return theme.color(value) if value is not None else theme.colors.color(default_role)


class Composite(Group):
    """A Group whose children are also reachable by name: ``composite.label``."""

    def __init__(self, parts: dict[str, Component], **kwargs: Any) -> None:
        if not parts:
            raise ValueError("Composite needs at least one part")
        super().__init__(*parts.values(), **kwargs)
        self.__dict__["parts"] = dict(parts)

    def __getattr__(self, name):
        parts = self.__dict__.get("parts")
        if parts is not None and name in parts:
            return parts[name]
        raise AttributeError(f"{type(self).__name__} has no attribute or part {name!r}")


# ---------------------------------------------------------------------------
# Simple shapes
# ---------------------------------------------------------------------------


def Dot(position=(0, 0), *, radius: float = 8, color: str | None = None, **kwargs: Any) -> Circle:
    """A filled circle marker."""
    return Circle(
        finite(radius, "radius", 0.5), fill=_color(color, "primary"), stroke=None, position=position, **kwargs
    )


def Arc(
    center,
    radius: float,
    *,
    start: float = -90,
    sweep: float = 360,
    color: str | None = None,
    width: float = 8,
    **kwargs: Any,
) -> Polyline:
    """A stroked circular arc. Angles in degrees, 0 = right, clockwise; -90 = 12 o'clock.

    Animate drawing with ``Draw(arc)`` (e.g. progress rings, gauges, orbits).
    """
    radius = finite(radius, "radius", 1)
    sweep = finite(sweep, "sweep")
    if abs(sweep) < 0.5 or abs(sweep) > 360:
        raise ValueError("sweep must be between 0.5 and 360 degrees in magnitude")
    cx, cy = (finite(v, "center") for v in center)
    steps = max(8, math.ceil(abs(sweep) / 3))
    points = [
        (
            cx + radius * math.cos(math.radians(start + sweep * i / steps)),
            cy + radius * math.sin(math.radians(start + sweep * i / steps)),
        )
        for i in range(steps + 1)
    ]
    kwargs.setdefault("line_cap", "round")
    kwargs.setdefault("fill", None)
    return Polyline(points, stroke=_color(color, "primary"), stroke_width=width, **kwargs)


def Divider(start, end=None, *, color: str | None = None, width: float = 2, **kwargs: Any) -> Polyline:
    """A hairline rule. Pass two points, or a Bounds for its horizontal center line."""
    if isinstance(start, Bounds):
        y = start.center[1]
        start, end = (start.left, y), (start.right, y)
    if end is None:
        raise ValueError("Divider needs two points or a Bounds")
    return Polyline((tuple(start), tuple(end)), stroke=_color(color, "border"), stroke_width=width, **kwargs)


# ---------------------------------------------------------------------------
# Text-bearing composites
# ---------------------------------------------------------------------------


class Pill(Composite):
    """Rounded tag with centered text. Parts: ``background``, ``text``."""

    def __init__(
        self,
        text: str,
        position=(0, 0),
        *,
        role: str = "label",
        fill: str | None = None,
        color: str | None = None,
        stroke: str | None = None,
        padding: tuple[float, float] = (24, 12),
        radius: float | None = None,
        **kwargs: Any,
    ) -> None:
        theme = current_theme()
        fill = _color(fill, "surface")
        color = (
            theme.color(color)
            if color is not None
            else readable_color(fill, theme.colors.text, theme.colors.background)
        )
        label = Text(text, role=role, type_scale=theme.type_scale, color=color, position=position, align="center")
        box = label.bounds
        px, py = (finite(v, "padding", 0) for v in padding)
        width, height = box.width + 2 * px, box.height + 2 * py
        background = Rectangle(
            width=width,
            height=height,
            fill=fill,
            stroke=theme.color(stroke) if stroke else None,
            stroke_width=2 if stroke else 0,
            corner_radius=min(height / 2, height / 2 if radius is None else radius),
            position=position,
        )
        super().__init__({"background": background, "text": label}, **kwargs)


def Badge(text: str, position=(0, 0), *, color: str = "primary", **kwargs: Any) -> Pill:
    """A filled accent pill with automatically readable text."""
    return Pill(text, position, fill=color, **kwargs)


class Callout(Composite):
    """A dot on a target point, an elbow leader line and a label.

    ``offset`` is where the elbow sits relative to the target; the label
    continues horizontally away from the target. Parts: ``dot``, ``line``,
    ``label``. Reveal the parts in order for a classic annotation build.
    """

    def __init__(
        self,
        text: str,
        target,
        *,
        offset: tuple[float, float] = (140, -90),
        role: str = "label",
        color: str | None = None,
        line_color: str | None = None,
        dot_radius: float = 7,
        tail: float = 48,
        gap: float = 14,
        **kwargs: Any,
    ) -> None:
        theme = current_theme()
        tx, ty = (finite(v, "target") for v in target)
        dx, dy = (finite(v, "offset") for v in offset)
        direction = 1 if dx >= 0 else -1
        elbow = (tx + dx, ty + dy)
        end = (elbow[0] + direction * finite(tail, "tail", 0), elbow[1])
        stroke = _color(line_color, "muted")
        dot = Dot((tx, ty), radius=dot_radius, color=color or "primary")
        line = Polyline((target, elbow, end), stroke=stroke, stroke_width=2, line_cap="round", fill=None)
        label = Text(
            text,
            role=role,
            type_scale=theme.type_scale,
            color=theme.color(color) if color is not None else theme.colors.text,
        )
        width = label.bounds.width
        label.move_to(end[0] + direction * (gap + width / 2), end[1])
        super().__init__({"dot": dot, "line": line, "label": label}, **kwargs)


class IconText(Composite):
    """An icon component followed by text, vertically centered. Parts: ``icon``, ``text``."""

    def __init__(
        self,
        icon: Component,
        text: str,
        position=(0, 0),
        *,
        role: str = "body",
        color: str | None = None,
        gap: float = 16,
        **kwargs: Any,
    ) -> None:
        theme = current_theme()
        label = Text(
            text,
            role=role,
            type_scale=theme.type_scale,
            color=theme.color(color) if color is not None else theme.role_color(role),
        )
        group = Group(icon, label).arrange(direction="right", gap=finite(gap, "gap", 0))
        dx = position[0] - group.bounds.center[0]
        dy = position[1] - group.bounds.center[1]
        icon.shift(dx, dy)
        label.shift(dx, dy)
        super().__init__({"icon": icon, "text": label}, **kwargs)


class Stat(Composite):
    """A big animated number over a short label. Parts: ``value`` (Number), ``label``.

    Count up with ``scene.play(stat.value.animate.value_to(98))``.
    """

    def __init__(
        self,
        value: float,
        label: str,
        position=(0, 0),
        *,
        value_role: str = "display",
        label_role: str = "caption",
        color: str | None = None,
        label_color: str | None = None,
        gap: float = 20,
        format_spec: str = ",.0f",
        prefix: str = "",
        suffix: str = "",
        **kwargs: Any,
    ) -> None:
        theme = current_theme()
        number = Number(
            value,
            role=value_role,
            type_scale=theme.type_scale,
            color=theme.color(color) if color is not None else theme.readable("primary", large=True),
            format_spec=format_spec,
            prefix=prefix,
            suffix=suffix,
            align="center",
        )
        caption = Text(
            label,
            role=label_role,
            type_scale=theme.type_scale,
            color=theme.color(label_color) if label_color is not None else theme.role_color(label_role),
            align="center",
        )
        x, y = position
        nb, cb = number.bounds, caption.bounds
        total = nb.height + gap + cb.height
        number.move_to(x, y - total / 2 + nb.height / 2)
        caption.move_to(x, y + total / 2 - cb.height / 2)
        super().__init__({"value": number, "label": caption}, **kwargs)


# ---------------------------------------------------------------------------
# Surfaces
# ---------------------------------------------------------------------------


class GlassCard(Composite):
    """A translucent gradient card with a hairline border and top sheen.

    Parts: ``body`` (Rectangle), ``sheen`` (Polyline). Place content inside
    ``bounds.inset(theme.space(5))``.
    """

    def __init__(
        self,
        bounds: Bounds,
        *,
        tint: str | None = None,
        radius: float | None = None,
        border: str | None = None,
        opacity: float = 0.72,
        shadow=True,
        **kwargs: Any,
    ) -> None:
        from .gradients import GradientStop, LinearGradient

        theme = current_theme()
        if not isinstance(bounds, Bounds) or bounds.width < 4 or bounds.height < 4:
            raise ValueError("GlassCard needs Bounds at least 4 px in each direction")
        base = _color(tint, "surface")
        opacity = finite(opacity, "opacity", 0)
        fill = LinearGradient(
            (
                GradientStop(0, with_alpha(base, min(1.0, opacity * 1.15))),
                GradientStop(1, with_alpha(base, opacity * 0.7)),
            ),
            angle=115,
        )
        radius = theme.radius if radius is None else finite(radius, "radius", 0)
        radius = min(radius, bounds.width / 2, bounds.height / 2)
        if shadow is True:
            shadow = theme.shadow
        body = Rectangle(
            width=bounds.width,
            height=bounds.height,
            fill=fill,
            stroke=with_alpha(_color(border, "text"), 0.14),
            stroke_width=1.5,
            corner_radius=radius,
            position=bounds.center,
            shadow=shadow or None,
        )
        inset = radius + 4
        light = relative_luminance(base) > 0.5
        sheen = Polyline(
            ((bounds.left + inset, bounds.top + 1.5), (bounds.right - inset, bounds.top + 1.5)),
            stroke=with_alpha("#FFFFFF", 0.9) if light else with_alpha(_color(border, "text"), 0.28),
            stroke_width=1.5,
            fill=None,
        )
        super().__init__({"body": body, "sheen": sheen}, **kwargs)
