from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from faceless_champ import Bounds, Component, Group, Text

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
    for font_size in range(int(size), int(minimum) - 1, -2):

        def make(value, font_size=font_size):
            return Text(
                value,
                font=theme.font,
                font_size=font_size,
                color=color or theme.foreground,
                align=align,
                spacing=8,
                position=box.center,
            )

        lines = []
        for paragraph in text.split("\n"):
            line = ""
            for word in paragraph.split():
                candidate = f"{line} {word}".strip()
                if line and make(candidate).bounds.width > box.width:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
        result = make("\n".join(lines))
        measured = result.bounds
        if measured.width <= box.width and measured.height <= box.height:
            return result
    raise KitError("TEXT_FIT", "Text cannot fit at the minimum size; shorten it or allocate more space")


def centered(box, height, width=None):
    width = min(width or box.width, box.width)
    height = min(height, box.height)
    x, y = box.center
    return Bounds(x - width / 2, y - height / 2, x + width / 2, y + height / 2)


def build_group(children):
    root = Group(*children.values())
    return BlockBuild(root, children, root.bounds)
