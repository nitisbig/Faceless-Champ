"""Immutable local effects. Parameters use design pixels and source time."""

import math
from dataclasses import dataclass, fields, replace

from PIL import ImageColor

from .components import finite


class _Effect:
    def __post_init__(self):
        for item in fields(self):
            value = getattr(self, item.name)
            if item.name == "color":
                ImageColor.getcolor(value, "RGBA")
            else:
                value = validate_effect_value(f"effect.{self.__class__.__name__}.{item.name}", value)
                object.__setattr__(self, item.name, value)


@dataclass(frozen=True)
class GaussianBlur(_Effect):
    radius: float = 8


@dataclass(frozen=True)
class OuterGlow(_Effect):
    color: str = "#69CAFF"
    radius: float = 12
    intensity: float = 1


@dataclass(frozen=True)
class Bloom(_Effect):
    radius: float = 16
    threshold: float = 0.65
    intensity: float = 0.6


@dataclass(frozen=True)
class Distortion(_Effect):
    amplitude: float = 8
    frequency: float = 2
    speed: float = 1


@dataclass(frozen=True)
class ChromaticAberration(_Effect):
    offset: float = 2


@dataclass(frozen=True)
class LightSweep(_Effect):
    intensity: float = 0.35
    width: float = 0.15
    speed: float = 0.3


_TYPES = {
    "blur": GaussianBlur,
    "glow": OuterGlow,
    "bloom": Bloom,
    "distortion": Distortion,
    "chromatic": ChromaticAberration,
    "light_sweep": LightSweep,
}


def _phase(time, speed, period=math.tau):
    """Reduce the source clock before multiplication to keep shader phases finite."""
    return math.remainder(time, period / abs(speed)) * speed if speed else 0.0


def validate_effect_value(key, value):
    parameter = key.rsplit(".", 1)[-1]
    signed = parameter in {"offset", "amplitude", "speed"}
    value = finite(value, key, None if signed else 0)
    limit = 1 if parameter in {"threshold", "width"} else 4096 if parameter in {"radius", "offset", "amplitude"} else 64
    if abs(value) > limit:
        raise ValueError(f"{key} exceeds {limit}")
    return value


@dataclass(frozen=True)
class EffectStack:
    blur: GaussianBlur | None = None
    glow: OuterGlow | None = None
    bloom: Bloom | None = None
    distortion: Distortion | None = None
    chromatic: ChromaticAberration | None = None
    light_sweep: LightSweep | None = None

    def __post_init__(self):
        for name, cls in _TYPES.items():
            if getattr(self, name) is not None and not isinstance(getattr(self, name), cls):
                raise TypeError(f"{name} must be {cls.__name__}")

    def state(self):
        return {
            f"effect.{name}.{f.name}": getattr(effect, f.name)
            for name in _TYPES
            if (effect := getattr(self, name)) is not None
            for f in fields(effect)
            if f.name != "color"
        }

    def evaluated(self, state):
        return replace(
            self,
            **{
                name: replace(
                    effect,
                    **{
                        f.name: state.get(f"effect.{name}.{f.name}", getattr(effect, f.name))
                        for f in fields(effect)
                        if f.name != "color"
                    },
                )
                for name in _TYPES
                if (effect := getattr(self, name)) is not None
            },
        )

    @property
    def padding(self):
        return math.ceil(
            (abs(self.distortion.amplitude) if self.distortion else 0)
            + (abs(self.chromatic.offset) if self.chromatic else 0)
            + (3 * self.blur.radius if self.blur else 0)
            + max(3 * self.glow.radius if self.glow else 0, 3 * self.bloom.radius if self.bloom else 0)
        )


def effect_stack(value):
    if value is not None and not isinstance(value, EffectStack):
        raise TypeError("effects must be an EffectStack or None")
    return value


def needs_compositor(node):
    from .timeline import Scene

    if isinstance(node, Scene):
        node.build()
        return any(e.component.effects is not None or getattr(e.component, "_procedural", False) for e in node.entries)
    return (
        getattr(node, "effects", None) is not None
        or getattr(node, "transition", None) is not None
        or any(needs_compositor(c) for c in node.children)
    )


__all__ = ["Bloom", "ChromaticAberration", "Distortion", "EffectStack", "GaussianBlur", "LightSweep", "OuterGlow"]
