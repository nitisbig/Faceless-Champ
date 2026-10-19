"""Source-clock transitions; Sequence.crossfade retains overlap/audio timing."""

from dataclasses import dataclass

from .components import finite


@dataclass(frozen=True)
class DirectionalWipe:
    softness: float = 0.08

    def __post_init__(self):
        value = finite(self.softness, "softness")
        if not 0 <= value <= 1:
            raise ValueError("softness must be in [0,1]")
        object.__setattr__(self, "softness", value)


@dataclass(frozen=True)
class LuminanceWipe(DirectionalWipe):
    pass


@dataclass(frozen=True)
class ZoomBlurTransition:
    strength: float = 0.12

    def __post_init__(self):
        value = finite(self.strength, "strength")
        if not 0 <= value <= 1:
            raise ValueError("strength must be in [0,1]")
        object.__setattr__(self, "strength", value)


def transition(value):
    if value is not None and not isinstance(value, (DirectionalWipe, ZoomBlurTransition)):
        raise TypeError("transition must be a built-in transition or None")
    return value


__all__ = ["DirectionalWipe", "LuminanceWipe", "ZoomBlurTransition"]
