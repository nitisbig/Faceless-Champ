"""Immutable local effects. Parameters use design pixels and source time."""

import math
from dataclasses import dataclass, fields, replace

from PIL import ImageColor

from .components import finite


class _Effect:
    # Fields that are configuration, not animatable numbers.
    _static = ("color",)

    def __post_init__(self):
        for item in fields(self):
            value = getattr(self, item.name)
            if item.name == "color":
                ImageColor.getcolor(value, "RGBA")
            elif item.name in self._static:
                continue
            else:
                value = validate_effect_value(f"effect.{self.__class__.__name__}.{item.name}", value)
                object.__setattr__(self, item.name, value)

    @classmethod
    def animatable(cls):
        return tuple(f.name for f in fields(cls) if f.name not in cls._static)


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


@dataclass(frozen=True)
class DisplacementMap(_Effect):
    """Push pixels around by a turbulent noise field or an image map (CPU/Skia).

    ``amplitude`` is the maximum shift in design pixels, ``size`` the noise
    feature size in design pixels, ``octaves`` the detail (1-8), ``speed`` how
    fast the field drifts (design px/s; 0 = still). ``map`` is an optional
    image path whose red/green channels displace x/y instead of noise
    (mid-grey = no shift). Animate e.g. ``animate.effect_to("displacement", amplitude=0)``.
    """

    _static = ("map",)
    amplitude: float = 12
    size: float = 120
    octaves: float = 2
    seed: float = 0
    speed: float = 0
    map: str | None = None

    def __post_init__(self):
        super().__post_init__()
        if not 1 <= self.octaves <= 8:
            raise ValueError("DisplacementMap octaves must be in [1, 8]")
        if self.size <= 0:
            raise ValueError("DisplacementMap size must be positive")
        if self.map is not None:
            from pathlib import Path

            if not Path(self.map).is_file():
                raise FileNotFoundError(f"Displacement map not found: {self.map}")
            object.__setattr__(self, "map", str(self.map))


@dataclass(frozen=True)
class ShaderEffect(_Effect):
    """Run custom SkSL over a component's pixels (CPU/Skia).

    The program receives ``uniform shader content;`` (sample it with
    ``content.eval(xy)``; colors are premultiplied) and returns the new color
    from ``half4 main(float2 xy)``; ``xy`` is in layer pixels. Optional built-in
    uniforms: ``float iTime`` (seconds), ``float2 iResolution`` (layer px),
    ``float iScale`` (pixels per design pixel), ``float4 iBox`` (component box
    x, y, w, h in layer px). ``uniforms`` work as in ShaderFill. ``mix`` (0-1,
    animatable) fades between the original and the shaded result.
    """

    _static = ("sksl", "uniforms")
    sksl: str = ""
    uniforms: tuple = ()
    mix: float = 1

    def __post_init__(self):
        from .shaders import _uniform_items

        if not isinstance(self.sksl, str) or "content" not in self.sksl or "main" not in self.sksl:
            raise ValueError("ShaderEffect SkSL must declare 'uniform shader content;' and half4 main(float2 xy)")
        uniforms = self.uniforms
        object.__setattr__(self, "uniforms", _uniform_items(dict(uniforms) if uniforms else None))
        super().__post_init__()
        from ._skia_fx import compile_shader

        try:
            compile_shader(self.sksl)
        except RuntimeError:  # skia unavailable; validated at render time
            pass


_TYPES = {
    "blur": GaussianBlur,
    "glow": OuterGlow,
    "bloom": Bloom,
    "distortion": Distortion,
    "chromatic": ChromaticAberration,
    "light_sweep": LightSweep,
    "displacement": DisplacementMap,
    "shader": ShaderEffect,
}

# Effects implemented with Skia on the CPU compositor only (not the ModernGL shaders).
SKIA_EFFECTS = frozenset({"displacement", "shader"})


def _phase(time, speed, period=math.tau):
    """Reduce the source clock before multiplication to keep shader phases finite."""
    return math.remainder(time, period / abs(speed)) * speed if speed else 0.0


def validate_effect_value(key, value):
    parameter = key.rsplit(".", 1)[-1]
    signed = parameter in {"offset", "amplitude", "speed"}
    value = finite(value, key, None if signed else 0)
    limit = (
        1
        if parameter in {"threshold", "width", "mix"}
        else 4096
        if parameter in {"radius", "offset", "amplitude", "size", "seed"}
        else 64
    )
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
    displacement: DisplacementMap | None = None
    shader: ShaderEffect | None = None

    def __post_init__(self):
        for name, cls in _TYPES.items():
            if getattr(self, name) is not None and not isinstance(getattr(self, name), cls):
                raise TypeError(f"{name} must be {cls.__name__}")

    def state(self):
        return {
            f"effect.{name}.{field}": getattr(effect, field)
            for name in _TYPES
            if (effect := getattr(self, name)) is not None
            for field in effect.animatable()
            if field != "color"
        }

    def evaluated(self, state):
        return replace(
            self,
            **{
                name: replace(
                    effect,
                    **{
                        field: state.get(f"effect.{name}.{field}", getattr(effect, field))
                        for field in effect.animatable()
                        if field != "color"
                    },
                )
                for name in _TYPES
                if (effect := getattr(self, name)) is not None
            },
        )

    @property
    def time_dependent(self):
        """Pixels change with time even when no property is animated."""
        return bool(
            self.distortion
            or self.light_sweep
            or self.shader
            or (self.displacement is not None and self.displacement.speed and self.displacement.map is None)
        )

    @property
    def uses_skia(self):
        return any(getattr(self, name) is not None for name in SKIA_EFFECTS)

    @property
    def padding(self):
        return math.ceil(
            (abs(self.distortion.amplitude) if self.distortion else 0)
            + (abs(self.displacement.amplitude) if self.displacement else 0)
            + (abs(self.chromatic.offset) if self.chromatic else 0)
            + (3 * self.blur.radius if self.blur else 0)
            + max(3 * self.glow.radius if self.glow else 0, 3 * self.bloom.radius if self.bloom else 0)
        )


def effect_stack(value):
    if value is not None and not isinstance(value, EffectStack):
        raise TypeError("effects must be an EffectStack or None")
    return value


def needs_compositor(node, *, native_blend=False):
    """Whether a frame must use the local-isolation compositor.

    Blend modes need it on Pillow; the Skia renderer composites them natively
    (``native_blend=True``) unless effects already require the compositor.
    """
    from .blending import blends
    from .timeline import Scene

    if isinstance(node, Scene):
        node.build()
        return any(
            e.component.effects is not None
            or getattr(e.component, "_procedural", False)
            or (not native_blend and (blends(e.component) or getattr(e.component, "perspective", None) is not None))
            for e in node.entries
        )
    return (
        getattr(node, "effects", None) is not None
        or getattr(node, "transition", None) is not None
        or any(needs_compositor(c, native_blend=native_blend) for c in node.children)
    )


__all__ = [
    "Bloom",
    "ChromaticAberration",
    "DisplacementMap",
    "Distortion",
    "EffectStack",
    "GaussianBlur",
    "LightSweep",
    "OuterGlow",
    "ShaderEffect",
]
