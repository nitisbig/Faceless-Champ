"""Layout allocations are measured before core scene ownership begins."""

from dataclasses import dataclass

from faceless_champ import Bounds

from .blocks.base import build_group
from .diagnostics import KitError, number


@dataclass(frozen=True, init=False)
class Stack:
    blocks: tuple
    gap: float

    def __init__(self, *blocks, gap=28):
        if not blocks:
            raise KitError("LAYOUT", "A layout needs at least one block")
        object.__setattr__(self, "blocks", tuple(blocks))
        object.__setattr__(self, "gap", number(gap, "gap"))

    def compose(self, ctx, bounds):
        return self._compose(ctx, bounds, False)

    def _compose(self, ctx, bounds, horizontal):
        extent = bounds.width if horizontal else bounds.height
        unit = (extent - self.gap * (len(self.blocks) - 1)) / len(self.blocks)
        if unit <= 0:
            raise KitError("LAYOUT", "Gaps exceed available space")
        children = {}
        for i, block in enumerate(self.blocks):
            offset = i * (unit + self.gap)
            box = (
                Bounds(bounds.left + offset, bounds.top, bounds.left + offset + unit, bounds.bottom)
                if horizontal
                else Bounds(bounds.left, bounds.top + offset, bounds.right, bounds.top + offset + unit)
            )
            built = block.compose(ctx, box)
            b = built.root.bounds
            if b.left < box.left - 1 or b.top < box.top - 1 or b.right > box.right + 1 or b.bottom > box.bottom + 1:
                raise KitError("LAYOUT", "Child exceeds its allocated layout bounds", child=i)
            children[str(i)] = built.root
        return build_group(children)


class Split(Stack):
    def compose(self, ctx, bounds):
        return self._compose(ctx, bounds, ctx.canvas.width > ctx.canvas.height)
