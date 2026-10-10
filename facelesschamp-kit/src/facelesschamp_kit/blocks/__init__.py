"""Composition-only blocks. All rendering belongs to faceless-champ."""

from dataclasses import dataclass
from pathlib import Path

from faceless_champ import Bounds, ImageSlot, Number, Rectangle

from ..diagnostics import KitError, number
from .base import Block, BlockBuild, build_group, centered, fit_text
from .flow import FlowDiagram
from .whiteboard import (
    WhiteboardArrow,
    WhiteboardCircle,
    WhiteboardDrawing,
    WhiteboardLine,
    WhiteboardPath,
    WhiteboardRectangle,
)


def palette(ctx, variant, color):
    if variant not in {"default", "accent", "muted"}:
        raise KitError("BLOCK_PROPS", "variant must be default, accent, or muted")
    return color or {"default": ctx.theme.foreground, "accent": ctx.theme.accent, "muted": ctx.theme.muted}[variant]


def panel(ctx, box):
    return Rectangle(
        width=max(1, box.width - 4),
        height=max(1, box.height - 4),
        fill=ctx.theme.surface,
        stroke=None,
        stroke_width=0,
        corner_radius=min(ctx.theme.radius, (box.height - 4) / 2),
        position=box.center,
    )


@dataclass(frozen=True)
class Heading:
    text: str
    variant: str = "default"
    color: str | None = None

    def compose(self, context, bounds):
        text = fit_text(
            self.text,
            context,
            bounds,
            size=context.theme.heading_size,
            color=palette(context, self.variant, self.color),
        )
        return BlockBuild(text, {"text": text})


@dataclass(frozen=True)
class TextPanel:
    text: str
    title: str = ""
    variant: str = "default"
    color: str | None = None

    def compose(self, ctx, bounds):
        box = centered(bounds, 600)
        p = min(ctx.theme.spacing, max(8, box.height / 12))
        children = {"background": panel(ctx, box)}
        top = box.top + p
        if self.title:
            title_height = min(120, (box.height - 3 * p) * 0.38)
            children["title"] = fit_text(
                self.title,
                ctx,
                Bounds(box.left + p, top, box.right - p, top + title_height),
                size=min(ctx.theme.heading_size, ctx.theme.body_size * 1.4),
                color=ctx.theme.accent,
            )
            top += title_height + p
        children["text"] = fit_text(
            self.text,
            ctx,
            Bounds(box.left + p, top, box.right - p, box.bottom - p),
            color=palette(ctx, self.variant, self.color),
        )
        return build_group(children)


@dataclass(frozen=True)
class MetricCard:
    value: float
    label: str
    variant: str = "accent"
    color: str | None = None

    def compose(self, ctx, bounds):
        value = number(self.value, "MetricCard.value", minimum=-float("inf"))
        box = centered(bounds, 460)
        p = ctx.theme.spacing
        if box.height < 180:
            raise KitError("LAYOUT", "MetricCard needs at least 180 design pixels in height")
        children = {"background": panel(ctx, box)}
        area = Bounds(box.left + p, box.top + p, box.right - p, box.top + box.height * 0.62)
        metric = Number(
            value,
            font=ctx.theme.font,
            font_size=132,
            color=palette(ctx, self.variant, self.color),
            position=area.center,
        )
        while metric.bounds.width > area.width or metric.bounds.height > area.height:
            metric.font_size -= 2
            if metric.font_size < ctx.theme.minimum_font_size:
                raise KitError("TEXT_FIT", "Metric value does not fit")
        children["value"] = metric
        children["label"] = fit_text(self.label, ctx, Bounds(box.left + p, area.bottom, box.right - p, box.bottom - p))
        return build_group(children)


@dataclass(frozen=True)
class ImageCard:
    asset: str
    label: str = ""
    mode: str = "required"

    def compose(self, ctx, bounds):
        box = centered(bounds, 760)
        p = ctx.theme.spacing
        children = {"background": panel(ctx, box)}
        image_box = Bounds(box.left + p, box.top + p, box.right - p, box.bottom - (120 if self.label else p))
        path = ctx.assets.image(self.asset, self.mode)
        entry = ctx.assets.entries.get(self.asset, {})
        label = Path(entry.get("path", self.asset)).name
        children["image"] = ImageSlot(
            path or ctx.root / label,
            mode=self.mode if path else "placeholder",
            label=label,
            width=image_box.width,
            height=image_box.height,
            position=image_box.center,
            placeholder_fill=ctx.theme.surface,
            placeholder_stroke=ctx.theme.muted,
            placeholder_color=ctx.theme.foreground,
            placeholder_font=ctx.theme.font,
            placeholder_font_size=ctx.theme.body_size,
        )
        if self.label:
            children["label"] = fit_text(
                self.label, ctx, Bounds(box.left + p, image_box.bottom, box.right - p, box.bottom - p)
            )
        return build_group(children)


@dataclass(frozen=True)
class Comparison:
    left: str
    right: str

    def compose(self, ctx, bounds):
        from ..layouts import Split

        return Split(TextPanel(self.left, title="Before"), TextPanel(self.right, title="After")).compose(ctx, bounds)


@dataclass(frozen=True)
class StepList:
    steps: tuple[str, ...]

    def __post_init__(self):
        object.__setattr__(self, "steps", tuple(self.steps))
        if not self.steps or any(not isinstance(s, str) or not s.strip() for s in self.steps):
            raise KitError("BLOCK_PROPS", "StepList needs nonempty text steps")

    def compose(self, ctx, bounds):
        from ..layouts import Stack

        return Stack(*(Heading(f"{i}. {step}", variant="accent") for i, step in enumerate(self.steps, 1))).compose(
            ctx, centered(bounds, 700)
        )


__all__ = [
    "Block",
    "BlockBuild",
    "Comparison",
    "FlowDiagram",
    "Heading",
    "ImageCard",
    "MetricCard",
    "StepList",
    "TextPanel",
    "WhiteboardArrow",
    "WhiteboardCircle",
    "WhiteboardDrawing",
    "WhiteboardLine",
    "WhiteboardPath",
    "WhiteboardRectangle",
]
