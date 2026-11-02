"""Immediate-mode Skia drawing for ``FunctionSource`` frame functions.

For films drawn frame by frame in code (math explainers, data stories) rather than built from
scene components::

    from faceless_champ.draw import Frame, Palette, draw_scene, env, hud, lin, mathtype, smooth

    def draw(t, size):
        fr = Frame(size)
        fr.circle(960, 540, 160 * smooth(lin(t, 0.5, 1.5)), "primary", 3.0, glow=0.6)
        mathtype.draw(fr, "e^(-x^2)", 960, 820, 72, reveal=lin(t, 1.0, 2.5))
        hud.readout(fr, 1560, 140, "area", "1.000", "secondary", env(t, 2.0, 6.0))
        fr.vignette(0.5)
        fr.grain(t, 0.04)
        return fr.finish()

    scene = draw_scene(draw, duration=6)

Modules: ``timing`` (envelopes, easing, CueClock; no Skia), ``palette`` (theme color tokens; no Skia),
``frame`` (Frame, fonts, glow, finish, motion blur), ``hud``, ``space`` (3D cameras and boxes),
``mathtype`` (Typst glyphs and morphs) and ``mesh3d`` (PyVista solids matched to ``space.Camera``).
Frame, hud, space and mathtype need skia-python (``faceless-champ[skia]``); mesh3d also needs
``faceless-champ[3d]``.
"""

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import frame, hud, mathtype, mesh3d, palette, space, timing
    from .frame import (
        DESIGN,
        LINEAR,
        Frame,
        GlowStyle,
        Pen,
        blur_samples,
        card_quad,
        col,
        draw_scene,
        font,
        image_from_array,
        mix,
        motion_blur,
        offscreen,
        quad_matrix,
        text_path,
        text_width,
        typeface,
    )
    from .palette import Palette, default_palette, set_default_palette
    from .timing import CueClock, back, chroma_kick, clamp, ease_in, ease_io, ease_out, env, lerp, lin, pulse, smooth

_EXPORTS = {
    "CueClock": "timing",
    "back": "timing",
    "chroma_kick": "timing",
    "clamp": "timing",
    "ease_in": "timing",
    "ease_io": "timing",
    "ease_out": "timing",
    "env": "timing",
    "lerp": "timing",
    "lin": "timing",
    "pulse": "timing",
    "smooth": "timing",
    "Palette": "palette",
    "default_palette": "palette",
    "set_default_palette": "palette",
    "DESIGN": "frame",
    "Frame": "frame",
    "GlowStyle": "frame",
    "LINEAR": "frame",
    "Pen": "frame",
    "blur_samples": "frame",
    "card_quad": "frame",
    "col": "frame",
    "draw_scene": "frame",
    "font": "frame",
    "image_from_array": "frame",
    "mix": "frame",
    "motion_blur": "frame",
    "offscreen": "frame",
    "quad_matrix": "frame",
    "text_path": "frame",
    "text_width": "frame",
    "typeface": "frame",
}
_MODULES = ("timing", "palette", "frame", "hud", "space", "mathtype", "mesh3d")

__all__ = [
    "DESIGN",
    "LINEAR",
    "CueClock",
    "Frame",
    "GlowStyle",
    "Palette",
    "Pen",
    "back",
    "blur_samples",
    "card_quad",
    "chroma_kick",
    "clamp",
    "col",
    "default_palette",
    "draw_scene",
    "ease_in",
    "ease_io",
    "ease_out",
    "env",
    "font",
    "frame",
    "hud",
    "image_from_array",
    "lerp",
    "lin",
    "mathtype",
    "mesh3d",
    "mix",
    "motion_blur",
    "offscreen",
    "palette",
    "pulse",
    "quad_matrix",
    "set_default_palette",
    "smooth",
    "space",
    "text_path",
    "text_width",
    "timing",
    "typeface",
]


def __getattr__(name):
    if name in _MODULES:
        return import_module(f".{name}", __name__)
    module = _EXPORTS.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(f".{module}", __name__), name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
