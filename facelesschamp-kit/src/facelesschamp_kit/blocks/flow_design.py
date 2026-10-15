"""Layout adapters for the public FlowChamp visual design components."""

from dataclasses import dataclass

from faceless_champ.flow import FlowDesign

from .base import BlockBuild


def _design(value):
    if isinstance(value, FlowDesign):
        return value
    if isinstance(value, str):
        return FlowDesign.named(value)
    raise TypeError("design must be a FlowDesign or a registered design name")


def _fit(visual, bounds):
    """Fit the complete surface, including its shadow, without enlarging it."""
    box = visual.bounds
    visual.scale *= min(1, bounds.width / box.width, bounds.height / box.height)
    box = visual.bounds
    visual.shift(bounds.center[0] - box.center[0], bounds.center[1] - box.center[1])
    return visual


@dataclass(frozen=True)
class FlowCard:
    """An asset-led device card with rounded surfaces and named visual parts.

    ``size`` describes the card face. Layout fits the entire card and its shadow
    into the allocation while preserving aspect ratio and the native maximum
    size. Every composition creates fresh core components.
    """

    label: str
    icon: str
    size: tuple = (240, 260)
    detail: str | None = None
    address: str | None = None
    design: FlowDesign | str = "networking"

    def compose(self, context, bounds):
        root = _design(self.design).node_card(
            self.label,
            icon=self.icon,
            position=bounds.center,
            size=self.size,
            detail=self.detail,
            address=self.address,
        )
        _fit(root, bounds)
        return BlockBuild(root, root.parts)


@dataclass(frozen=True)
class FlowPopup:
    """A compact protocol callout, centered and uniformly fitted to its slot."""

    kind: str
    value: str
    design: FlowDesign | str = "networking"

    def compose(self, context, bounds):
        root = _design(self.design).popup(self.kind, self.value, bounds.center)
        _fit(root, bounds)
        return BlockBuild(root, root.parts)


@dataclass(frozen=True)
class FlowBackdrop:
    """The selected FlowChamp design's background at the allocated bounds."""

    design: FlowDesign | str = "networking"

    def compose(self, context, bounds):
        root = _design(self.design).backdrop(bounds)
        return BlockBuild(root, {"background": root})
