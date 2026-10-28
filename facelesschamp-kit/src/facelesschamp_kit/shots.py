"""Shot templates: complete, polished scenes from a few fields of content.

The fast path for any model: pick a template, fill short text, get a premium
shot with theme typography, layout, budgets and entrance motion::

    from facelesschamp_kit.shots import shot_video
    video = shot_video("stat", {"value": 98, "suffix": "%", "label": "of requests served from cache"},
                       theme="neon", duration=5)
    video.export("output/stat.mp4", settings=...)

or from the command line (JSON content)::

    fc-kit shot stat content.json --theme neon --frame 2.5 -o output/stat.png

Templates and their fields (``fc-kit shot --list`` prints them):

* ``title``  eyebrow?, title, subtitle?
* ``stat``   value, label, prefix?, suffix?, context?
* ``quote``  text, attribution?
* ``steps``  steps (2-5 short lines), title?
* ``compare`` left_title, left, right_title, right
* ``end``    title, action?

Each template is also an ordinary kit Block for ``segment.add(...)``. Copy over
a role budget raises KitError TEXT_BUDGET: shorten it rather than shrinking it.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path

from faceless_champ import Bounds, Number, Text
from faceless_champ.primitives import Dot, Pill
from faceless_champ.theme import current_theme

from .blocks.base import build_group, fit_text, heading_font, text_weight, unit
from .diagnostics import KitError


def _content_box(ctx, bounds, width=1320):
    """A centered column that never exceeds ``width`` (scaled) inside bounds."""
    width = min(bounds.width, width * unit(ctx))
    x = bounds.center[0]
    return Bounds(x - width / 2, bounds.top, x + width / 2, bounds.bottom)


def _stack(ctx, box, named, gaps):
    """Vertically center components inside box. ``gaps`` maps a part name to the
    space above it (1080p pixels, scaled); unlisted parts use 24."""
    names = list(named)
    heights = [named[n].bounds.height for n in names]
    spaces = [0] + [gaps.get(n, 24) * unit(ctx) for n in names[1:]]
    total = sum(heights) + sum(spaces)
    if total > box.height + 1:
        raise KitError("LAYOUT", "Shot content is taller than its box; shorten the copy")
    y = box.center[1] - total / 2
    for name, height, space in zip(names, heights, spaces):
        y += space
        named[name].move_to(box.center[0], y + height / 2)
        y += height


def _eyebrow(ctx, text):
    theme = current_theme()
    words = len(text.split())
    if words > 4:
        raise KitError("TEXT_BUDGET", f"eyebrow has {words} words; keep it to 4 or fewer")
    return Text(text.upper(), role="label", color=theme.colors.primary, tracking=0.14, align="center")


@dataclass(frozen=True)
class TitleCard:
    title: str
    subtitle: str = ""
    eyebrow: str = ""

    def compose(self, ctx, bounds):
        box = _content_box(ctx, bounds)
        children = {}
        if self.eyebrow:
            children["eyebrow"] = _eyebrow(ctx, self.eyebrow)
        children["title"] = fit_text(
            self.title,
            ctx,
            Bounds(box.left, box.top, box.right, box.top + box.height * 0.45),
            size=current_theme().type_scale.display.font_size * unit(ctx),
            heading=True,
            role="display",
        )
        if self.subtitle:
            children["subtitle"] = fit_text(
                self.subtitle,
                ctx,
                Bounds(box.left + box.width * 0.1, box.top, box.right - box.width * 0.1, box.top + box.height * 0.3),
                color=ctx.theme.muted,
            )
        _stack(ctx, box, children, {"title": 32, "subtitle": 48})
        return build_group(children)


@dataclass(frozen=True)
class BigStat:
    value: float
    label: str
    prefix: str = ""
    suffix: str = ""
    context: str = ""
    format_spec: str = ",.0f"

    def compose(self, ctx, bounds):
        theme = current_theme()
        box = _content_box(ctx, bounds, 1200)
        number = Number(
            float(self.value),
            format_spec=self.format_spec,
            prefix=self.prefix,
            suffix=self.suffix,
            role="display",
            font=heading_font(ctx.theme, heading=True),
            font_weight=text_weight(ctx.theme, heading=True),
            font_size=200 * unit(ctx),
            color=theme.colors.primary,
            align="center",
        )
        while number.bounds.width > box.width:
            number.font_size *= 0.9
        children = {"value": number}
        children["label"] = fit_text(
            self.label,
            ctx,
            Bounds(box.left, box.top, box.right, box.top + 140 * unit(ctx)),
            role="heading",
            size=theme.type_scale.heading.font_size * unit(ctx),
            heading=True,
        )
        if self.context:
            children["context"] = fit_text(
                self.context,
                ctx,
                Bounds(box.left, box.top, box.right, box.top + 160 * unit(ctx)),
                color=ctx.theme.muted,
            )
        _stack(ctx, box, children, {"label": 28, "context": 32})
        return build_group(children)


@dataclass(frozen=True)
class QuoteCard:
    text: str
    attribution: str = ""

    def compose(self, ctx, bounds):
        theme = current_theme()
        box = _content_box(ctx, bounds, 1240)
        children = {
            "mark": Text(
                "“",
                role="display",
                font=heading_font(ctx.theme, True) or "serif",
                font_size=180 * unit(ctx),
                color=theme.colors.primary,
                align="center",
            ),
        }
        children["quote"] = fit_text(
            self.text,
            ctx,
            Bounds(box.left, box.top, box.right, box.top + box.height * 0.5),
            role="heading",
            size=theme.type_scale.heading.font_size * unit(ctx),
            heading=True,
        )
        if self.attribution:
            children["attribution"] = Text(
                "— " + self.attribution, role="caption", color=theme.colors.muted, align="center"
            )
        _stack(ctx, box, children, {"quote": 8, "attribution": 36})
        return build_group(children)


@dataclass(frozen=True)
class StepsCard:
    steps: tuple[str, ...]
    title: str = ""

    def __post_init__(self):
        object.__setattr__(self, "steps", tuple(self.steps))
        if not 2 <= len(self.steps) <= 5:
            raise KitError("TEXT_BUDGET", "steps needs 2 to 5 items; split longer processes across shots")

    def compose(self, ctx, bounds):
        theme = current_theme()
        u = unit(ctx)
        box = _content_box(ctx, bounds, 1180)
        children = {}
        if self.title:
            children["title"] = fit_text(
                self.title,
                ctx,
                Bounds(box.left, box.top, box.right, box.top + 120 * u),
                heading=True,
                size=theme.type_scale.heading.font_size * u,
                role="heading",
            )
        rows = []
        for index, step in enumerate(self.steps, 1):
            words = len(step.split())
            if words > 9:
                raise KitError("TEXT_BUDGET", f"step {index} has {words} words; keep steps to 9 words or fewer")
            marker = Dot(radius=30 * u, color="primary")
            digit = Text(
                str(index), role="label", font_size=30 * u, align="center", color=_on(theme.colors.primary, theme)
            )
            label = Text(step, role="body", font_size=theme.type_scale.body.font_size * u, color=theme.colors.text)
            rows.append((marker, digit, label))
        row_height, title_gap, marker_space = 84 * u, 48 * u, 88 * u
        title_height = children["title"].bounds.height + title_gap if "title" in children else 0
        total = title_height + row_height * len(rows)
        if total > box.height + 1:
            raise KitError("LAYOUT", "Steps do not fit; use fewer steps or a taller placement")
        top = box.center[1] - total / 2
        if "title" in children:
            children["title"].move_to(box.center[0], top + children["title"].bounds.height / 2)
        widest = max(label.bounds.width for _, _, label in rows)
        left = box.center[0] - (marker_space + widest) / 2
        for index, (marker, digit, label) in enumerate(rows):
            y = top + title_height + row_height * (index + 0.5)
            marker.move_to(left + 30 * u, y)
            digit.move_to(left + 30 * u, y)
            label.move_to(left + marker_space + label.bounds.width / 2, y)
            if label.bounds.right > box.right + 1:
                raise KitError("TEXT_BUDGET", f"step {index + 1} is too wide; shorten it")
            children[f"marker-{index}"] = marker
            children[f"number-{index}"] = digit
            children[f"step-{index}"] = label
        return build_group(children)


@dataclass(frozen=True)
class CompareCard:
    left_title: str
    left: str
    right_title: str
    right: str

    def compose(self, ctx, bounds):
        from .blocks import Comparison

        return Comparison(self.left, self.right, self.left_title, self.right_title).compose(ctx, bounds)


@dataclass(frozen=True)
class EndCard:
    title: str
    action: str = ""

    def compose(self, ctx, bounds):
        theme = current_theme()
        box = _content_box(ctx, bounds, 1200)
        children = {
            "title": fit_text(
                self.title,
                ctx,
                Bounds(box.left, box.top, box.right, box.top + box.height * 0.4),
                heading=True,
                size=theme.type_scale.title.font_size * unit(ctx),
                role="title",
            )
        }
        if self.action:
            if len(self.action.split()) > 5:
                raise KitError("TEXT_BUDGET", "action should be 5 words or fewer")
            children["action"] = Pill(self.action, fill="primary", padding=(36 * unit(ctx), 18 * unit(ctx)))
        _stack(ctx, box, children, {"action": 48})
        return build_group(children)


def _on(color, theme):
    from faceless_champ import readable_color

    return readable_color(color, theme.colors.text, theme.colors.background)


SHOTS = {
    "title": TitleCard,
    "stat": BigStat,
    "quote": QuoteCard,
    "steps": StepsCard,
    "compare": CompareCard,
    "end": EndCard,
}


def shot_fields(name):
    """Field names of a template; optional ones end with '?'."""
    from dataclasses import MISSING

    return [f.name + ("?" if f.default is not MISSING else "") for f in fields(_template(name))]


def _template(name):
    try:
        return SHOTS[name]
    except KeyError:
        raise KitError("SHOT", f"Unknown shot {name!r}; choose {', '.join(SHOTS)}") from None


def shot(name, content):
    """Build a shot Block from a template name and a content mapping."""
    cls = _template(name)
    if not isinstance(content, dict):
        raise KitError("SHOT", "shot content must be a JSON object")
    allowed = {f.name for f in fields(cls)}
    unknown = set(content) - allowed
    if unknown:
        raise KitError(
            "SHOT", f"Unknown fields for {name}: {', '.join(sorted(unknown))}; use {', '.join(shot_fields(name))}"
        )
    try:
        return cls(**content)
    except TypeError as exc:
        raise KitError("SHOT", f"{name} needs fields {', '.join(shot_fields(name))}: {exc}") from exc


def shot_video(name, content, *, theme="midnight", duration=5.0, size=(1920, 1080), root="."):
    """A compiled one-segment video showing a single shot with theme motion."""
    from faceless_champ import Canvas

    from .context import BuildContext
    from .themes import THEMES
    from .themes import Theme as KitTheme
    from .video import Video

    if isinstance(theme, str):
        if theme not in THEMES:
            raise KitError("THEME", f"Unknown theme {theme!r}; choose {', '.join(THEMES)}")
        theme = THEMES[theme]
    if not isinstance(theme, KitTheme):
        raise KitError("THEME", "theme must be a kit Theme or theme name")
    width, height = size
    ctx = BuildContext(Path(root), Canvas(width, height, theme.background), theme)
    video = Video(ctx)
    video.segment(name, duration=duration).add(shot(name, content))
    return video.compile()


__all__ = [
    "SHOTS",
    "BigStat",
    "CompareCard",
    "EndCard",
    "QuoteCard",
    "StepsCard",
    "TitleCard",
    "shot",
    "shot_fields",
    "shot_video",
]
