from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from faceless_champ import Bounds, Component, Group
from faceless_champ import fit_text as core_fit_text

from ..diagnostics import KitError


@dataclass(frozen=True)
class BlockBuild:
    root: Component
    children: dict[str, Component] = field(default_factory=dict)
    bounds: Bounds | None = None

    def __post_init__(self):
        if not isinstance(self.root, Component):
            raise KitError("BLOCK_CONTRACT", "BlockBuild.root must be a core Component")
        object.__setattr__(self, "children", dict(self.children))
        object.__setattr__(self, "bounds", self.bounds or self.root.bounds)


@runtime_checkable
class Block(Protocol):
    def compose(self, context, bounds: Bounds) -> BlockBuild: ...


def fit_text(text, ctx, box, *, size=None, color=None, align="center"):
    if not isinstance(text, str) or not text.strip():
        raise KitError("BLOCK_PROPS", "Text must be a nonempty string")
    theme = ctx.theme
    size = size or theme.body_size
    minimum = theme.minimum_font_size
    if size < minimum:
        raise KitError("TEXT_FIT", "Requested font size is below theme minimum")
    try:
        return core_fit_text(
            text,
            box,
            font_size=size,
            min_font_size=minimum,
            font=theme.font,
            color=color or theme.foreground,
            align=align,
        )
    except ValueError as exc:
        raise KitError("TEXT_FIT", str(exc)) from exc


def centered(box, height, width=None):
    width = min(width or box.width, box.width)
    height = min(height, box.height)
    x, y = box.center
    return Bounds(x - width / 2, y - height / 2, x + width / 2, y + height / 2)


def build_group(children):
    root = Group(*children.values())
    return BlockBuild(root, children, root.bounds)
