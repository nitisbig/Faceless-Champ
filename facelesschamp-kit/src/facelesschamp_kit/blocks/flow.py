"""Measured workflow diagrams with independently animatable children."""

from dataclasses import dataclass
from itertools import pairwise

from faceless_champ import Arrow, Bounds, Group, Rectangle

from ..diagnostics import KitError
from .base import BlockBuild, fit_text


@dataclass(frozen=True)
class FlowDiagram:
    steps: tuple[str, ...]
    direction: str = "horizontal"

    def __post_init__(self):
        object.__setattr__(self, "steps", tuple(self.steps))
        if not self.steps or any(not isinstance(s, str) or not s.strip() for s in self.steps):
            raise KitError("BLOCK_PROPS", "FlowDiagram needs nonempty text steps")
        if self.direction not in {"horizontal", "vertical"}:
            raise KitError("BLOCK_PROPS", "direction must be horizontal or vertical")

    def compose(self, ctx, bounds):
        horizontal = self.direction == "horizontal"
        extent = bounds.width if horizontal else bounds.height
        gap = max(32, ctx.theme.spacing * 2)
        unit = (extent - 8 - gap * (len(self.steps) - 1)) / len(self.steps)
        if unit < 64:
            raise KitError("LAYOUT", "FlowDiagram needs more space for its steps")
        children, roots, boxes = {}, [], []
        for i, text in enumerate(self.steps):
            if horizontal:
                left = bounds.left + 4 + i * (unit + gap)
                height = min(bounds.height - 8, 220)
                box = Bounds(left, bounds.center[1] - height / 2, left + unit, bounds.center[1] + height / 2)
            else:
                top = bounds.top + 4 + i * (unit + gap)
                width = min(bounds.width - 8, 600)
                box = Bounds(bounds.center[0] - width / 2, top, bounds.center[0] + width / 2, top + unit)
            if min(box.width, box.height) <= 32:
                raise KitError("LAYOUT", "FlowDiagram nodes need more space")
            card = Rectangle(
                width=box.width,
                height=box.height,
                fill=ctx.theme.surface,
                stroke=ctx.theme.accent,
                stroke_width=2,
                corner_radius=min(ctx.theme.radius, min(box.width, box.height) / 2),
                position=box.center,
            )
            label = fit_text(text, ctx, Bounds(box.left + 16, box.top + 16, box.right - 16, box.bottom - 16))
            node = Group(card, label)
            roots.append(node)
            children[f"node-{i}"] = node
            children[f"label-{i}"] = label
            boxes.append(box)
        for i, (a, b) in enumerate(pairwise(boxes)):
            start, end = (
                ((a.right + 10, a.center[1]), (b.left - 10, b.center[1]))
                if horizontal
                else ((a.center[0], a.bottom + 10), (b.center[0], b.top - 10))
            )
            arrow = Arrow(start, end, stroke=ctx.theme.accent, stroke_width=3, tip_size=12)
            roots.append(arrow)
            children[f"edge-{i}"] = arrow
        return BlockBuild(Group(*roots), children)
