from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from faceless_champ import Bounds, Component, Group
from faceless_champ import fit_text as core_fit_text
from faceless_champ.typography import TYPE_SCALE, TextBudgetError

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


def text_weight(theme, heading=False):
    """Theme weight, or the role weight when the theme uses the bundled default font."""
    weight = theme.heading_weight if heading else theme.font_weight
    if weight is None and theme.font is None:
        weight = (TYPE_SCALE.title if heading else TYPE_SCALE.body).font_weight
    return weight


def fit_text(text, ctx, box, *, size=None, color=None, align="center", heading=False, role=None):
    """Theme-styled core fit_text with role line height, tracking and text budgets.

    Text may shrink to 80% of its size (never below the theme minimum). Copy that
    exceeds the role's word/line budget raises KitError TEXT_BUDGET: shorten it,
    split the beat, or let narration carry it. Themes can set text_budgets=False.
    """
    if not isinstance(text, str) or not text.strip():
        raise KitError("BLOCK_PROPS", "Text must be a nonempty string")
    theme = ctx.theme
    size = size or theme.body_size
    if size < theme.minimum_font_size:
        raise KitError("TEXT_FIT", "Requested font size is below theme minimum")
    minimum = min(size, max(theme.minimum_font_size, size * 0.8))
    role = role or ("title" if heading else "body")
    try:
        return core_fit_text(
            text,
            box,
            role=role,
            budget=theme.text_budgets,
            font_size=size,
            min_font_size=minimum,
            font=theme.font,
            font_weight=text_weight(theme, heading),
            color=color or theme.foreground,
            align=align,
            text_engine=theme.text_engine,
        )
    except TextBudgetError as exc:
        raise KitError("TEXT_FIT" if exc.kind == "fit" else "TEXT_BUDGET", str(exc)) from exc
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
