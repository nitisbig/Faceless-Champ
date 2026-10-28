"""Design audit: machine-checkable quality rules with actionable fixes.

``design_audit(scene)`` samples the timeline and reports problems a viewer
would notice, so an agent can repair a scene without a human critique:

* ``TEXT_TOO_SMALL``   rendered text below the readable size (scaled to 1080p)
* ``LOW_CONTRAST``     text/background contrast below WCAG targets
* ``TEXT_CLUTTER``     too many words on screen at once
* ``TOO_MANY_SIZES``   too many distinct text sizes in one frame
* ``TOO_MANY_FONTS``   more than two font families in one frame
* ``OUTSIDE_SAFE_AREA`` / ``OUTSIDE_FRAME``  text leaves the title-safe area / frame

Each finding carries a ``fix`` hint. Thresholds are keyword arguments.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    time: float
    message: str
    fix: str
    text: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class DesignReport:
    times: tuple[float, ...]
    findings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(f.severity == "error" for f in self.findings)

    def to_dict(self):
        return {"ok": self.ok, "times": list(self.times), "findings": [f.to_dict() for f in self.findings]}

    def __str__(self):
        if not self.findings:
            return "design audit: no findings"
        return "\n".join(f"[{f.severity}] {f.code} t={f.time:.2f}s {f.message} -> {f.fix}" for f in self.findings)


def _paint_color(value):
    """A solid RGBA tuple for a fill, averaging gradient stops; None if unknown/transparent."""
    from .gradients import LinearGradient, RadialGradient
    from .motion import rgba

    if value is None:
        return None
    if isinstance(value, (LinearGradient, RadialGradient)):
        colors = [rgba(stop.color) for stop in value.stops]
        return tuple(sum(c[i] for c in colors) / len(colors) for i in range(4))
    try:
        return tuple(rgba(value))
    except (ValueError, TypeError):
        return None


def _hex(color):
    return "#{:02x}{:02x}{:02x}".format(*(round(c) for c in color[:3]))


def _blend(top, bottom):
    alpha = top[3] / 255
    return tuple(top[i] * alpha + bottom[i] * (1 - alpha) for i in range(3)) + (255,)


def _visible_opacity(entry, time):
    opacity = 1.0
    for current in (entry, *entry.ancestors()):
        if time < current.start or (current.end is not None and time >= current.end):
            return 0.0
        opacity *= current.state_at(time).get("opacity", 1.0)
    return opacity


def _scale(entry, time):
    factor = 1.0
    for current in (entry, *entry.ancestors()):
        state = current.state_at(time)
        factor *= state.get("scale", 1.0) * state.get("scale_y", 1.0)
    return factor


def _scenes_at(node, time):
    """(scene, local_time) pairs visible at a composition time."""
    from .timeline import Grid, Layer, Scene, Sequence

    if isinstance(node, Scene):
        yield node, time
    elif isinstance(node, Sequence):
        for child, start in zip(node.children, node.starts):
            if start <= time < start + child.duration + 1e-9:
                yield from _scenes_at(child, time - start)
    elif isinstance(node, (Layer, Grid)):
        for child in node.children:
            yield from _scenes_at(child, time)


def design_audit(
    node,
    times=None,
    *,
    samples: int = 8,
    min_font: float = 28,
    error_font: float = 22,
    max_words: int = 30,
    max_sizes: int = 4,
    max_families: int = 2,
    min_contrast: float = 4.5,
    large_contrast: float = 3.0,
) -> DesignReport:
    """Sample ``node`` and return a DesignReport. Font limits are 1080p pixels."""
    from ._rendering.evaluate import scene_entries
    from ._rendering.measure import measurement_session
    from .colors import contrast_ratio
    from .components import Shape, Text
    from .surfaces import Surface
    from .typography import FALLBACK_FONT

    duration = node.duration
    if times is None:
        count = max(1, int(samples))
        times = tuple(duration * (i + 0.5) / count for i in range(count))
    times = tuple(float(t) for t in times)
    report = DesignReport(times)
    seen = set()

    def add(code, severity, time, message, fix, text=""):
        key = (code, text)
        if key not in seen:
            seen.add(key)
            report.findings.append(Finding(code, severity, round(time, 3), message, fix, text))

    measure = measurement_session()
    for time in times:
        for scene, local in _scenes_at(node, time):
            scene.build()
            canvas = scene.canvas
            unit = min(canvas.width, canvas.height) / 1080
            safe = canvas.safe_area()
            frame = canvas.bounds
            evaluated = scene_entries(scene, local)
            order = sorted(range(len(scene.entries)), key=lambda i: (scene.entries[i].component.z_index, i))
            canvas_color = _paint_color(canvas.bg)
            texts, words, sizes, families = [], 0, set(), set()
            for rank, index in enumerate(order):
                entry = scene.entries[index]
                component = entry.component
                if not isinstance(component, Text) or _visible_opacity(entry, local) < 0.05:
                    continue
                content = component.text.strip()
                if not content:
                    continue
                label = content.replace("\n", " ")[:40]
                px = component.font_size * _scale(entry, local) / unit
                texts.append(component)
                words += len(content.split())
                sizes.add(round(px / 4) * 4)
                if component.font and Path(component.font).name != Path(FALLBACK_FONT).name:
                    families.add(Path(component.font).name)
                if px < error_font:
                    add(
                        "TEXT_TOO_SMALL",
                        "error",
                        time,
                        f"text at {px:.0f}px is unreadable: {label!r}",
                        "use role='label' or larger; shorten copy instead of shrinking",
                        label,
                    )
                elif px < min_font:
                    add(
                        "TEXT_TOO_SMALL",
                        "warning",
                        time,
                        f"text at {px:.0f}px is hard to read: {label!r}",
                        f"keep text >= {min_font:g}px at 1080p (role='label' or 'caption')",
                        label,
                    )
                box = measure.entry_bounds(evaluated[index], local, ancestors=True)
                if not frame.contains(box, tolerance=1):
                    add(
                        "OUTSIDE_FRAME",
                        "error",
                        time,
                        f"text is cut off by the frame: {label!r}",
                        "place it inside canvas.safe_area()",
                        label,
                    )
                elif not safe.contains(box, tolerance=1):
                    add(
                        "OUTSIDE_SAFE_AREA",
                        "warning",
                        time,
                        f"text sits outside the title-safe area: {label!r}",
                        "lay out inside canvas.safe_area()",
                        label,
                    )
                # Background: the nearest painted solid surface under the text center.
                color = _paint_color(getattr(component, "color", None))
                background = canvas_color
                center = box.center
                for below in reversed(order[:rank]):
                    other_entry = scene.entries[below]
                    other = other_entry.component
                    if isinstance(other, Text) or _visible_opacity(other_entry, local) < 0.05:
                        continue
                    if hasattr(other, "children"):
                        continue
                    other_box = measure.entry_bounds(evaluated[below], local, ancestors=True)
                    if not other_box.contains(center, tolerance=0):
                        continue
                    if not isinstance(other, (Shape, Surface)):
                        background = None  # image/viewport/custom pixels: unknown, skip the check
                        break
                    fill = _paint_color(other.fill)
                    if fill is not None and fill[3] >= 128:
                        background = fill
                        break
                if color is not None and background is not None and background[3] > 0:
                    ratio = contrast_ratio(_hex(_blend(color, background)), _hex(background))
                    needed = large_contrast if px >= 40 else min_contrast
                    if ratio < large_contrast:
                        add(
                            "LOW_CONTRAST",
                            "error",
                            time,
                            f"contrast {ratio:.1f}:1 is too low: {label!r}",
                            "use the theme 'text' color on 'background'/'surface'",
                            label,
                        )
                    elif ratio < needed:
                        add(
                            "LOW_CONTRAST",
                            "warning",
                            time,
                            f"contrast {ratio:.1f}:1 below {needed:g}:1 for {px:.0f}px text: {label!r}",
                            "use a stronger color role ('text' instead of 'muted') or larger text",
                            label,
                        )
            if words > max_words:
                add(
                    "TEXT_CLUTTER",
                    "warning",
                    time,
                    f"{words} words on screen at once",
                    f"keep under {max_words}: split the beat or let narration carry the detail",
                )
            if len(sizes) > max_sizes:
                add(
                    "TOO_MANY_SIZES",
                    "warning",
                    time,
                    f"{len(sizes)} different text sizes in one frame",
                    "use type roles (title/body/label) instead of custom sizes",
                )
            if len(families) > max_families:
                add(
                    "TOO_MANY_FONTS",
                    "warning",
                    time,
                    f"{len(families)} font families in one frame",
                    "use one heading and one body font (TypeScale.named pairing)",
                )
    return report
