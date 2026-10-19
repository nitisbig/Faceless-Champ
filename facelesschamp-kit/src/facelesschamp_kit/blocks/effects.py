"""Thin authoring wrappers over public Core effects and procedural components."""

from dataclasses import dataclass

from faceless_champ import EffectStack, Group, ParticleField, ProceduralBackground

from .base import BlockBuild


@dataclass(frozen=True)
class EffectBlock:
    block: object
    effects: EffectStack

    def compose(self, context, bounds):
        built = self.block.compose(context, bounds)
        return BlockBuild(Group(built.root, effects=self.effects), built.children)


@dataclass(frozen=True)
class ProceduralBackdrop:
    kind: str = "aurora"
    seed: int | None = None
    color: str | None = None
    speed: float = 0.2

    def compose(self, context, bounds):
        root = ProceduralBackground(
            self.kind,
            width=bounds.width,
            height=bounds.height,
            position=bounds.center,
            seed=context.seed if self.seed is None else self.seed,
            color=self.color or context.theme.accent,
            speed=self.speed,
        )
        return BlockBuild(root, {"background": root})


@dataclass(frozen=True)
class ParticleBackdrop:
    count: int = 1000
    radius: float = 2
    seed: int | None = None
    color: str | None = None

    def compose(self, context, bounds):
        root = ParticleField(
            width=bounds.width,
            height=bounds.height,
            position=bounds.center,
            count=self.count,
            radius=self.radius,
            seed=context.seed if self.seed is None else self.seed,
            color=self.color or context.theme.accent,
        )
        return BlockBuild(root, {"particles": root})
