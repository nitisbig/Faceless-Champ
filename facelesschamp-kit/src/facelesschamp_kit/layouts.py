"""Layout allocations are measured before core scene ownership begins."""

from dataclasses import dataclass

from .blocks.base import build_group
from .diagnostics import KitError, number


@dataclass(frozen=True, init=False)
class Stack:
    blocks: tuple
    gap: float
    weights: tuple

    def __init__(self, *blocks, gap=28, weights=None):
        """Cells of equal size, or sized by relative ``weights`` (one per block)."""
        if not blocks:
            raise KitError("LAYOUT", "A layout needs at least one block")
        object.__setattr__(self, "blocks", tuple(blocks))
        object.__setattr__(self, "gap", number(gap, "gap"))
        if weights is None:
            weights = (1,) * len(blocks)
        weights = tuple(number(w, "weight", positive=True) for w in weights)
        if len(weights) != len(blocks):
            raise KitError("LAYOUT", "weights need one value per block")
        object.__setattr__(self, "weights", weights)

    def compose(self, ctx, bounds):
        return self._compose(ctx, bounds, False)

    def _compose(self, ctx, bounds, horizontal):
        try:
            boxes = (
                bounds.columns(self.weights, gap=self.gap) if horizontal else bounds.rows(self.weights, gap=self.gap)
            )
        except ValueError as exc:
            raise KitError("LAYOUT", "Gaps exceed available space") from exc
        children = {}
        for i, (block, box) in enumerate(zip(self.blocks, boxes)):
            built = block.compose(ctx, box)
            b = built.root.bounds
            if b.left < box.left - 1 or b.top < box.top - 1 or b.right > box.right + 1 or b.bottom > box.bottom + 1:
                raise KitError("LAYOUT", "Child exceeds its allocated layout bounds", child=i)
            children[str(i)] = built.root
        return build_group(children)


class Split(Stack):
    def compose(self, ctx, bounds):
        return self._compose(ctx, bounds, ctx.canvas.width > ctx.canvas.height)
