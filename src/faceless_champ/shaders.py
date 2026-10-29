"""Custom SkSL shaders as layers (ShaderFill). For shaders over existing content use
``effects=EffectStack(shader=ShaderEffect(...))``.

SkSL is Skia's GLSL-like shading language. A ShaderFill program defines
``half4 main(float2 xy)``, where ``xy`` is in design pixels inside the layer
(0..width, 0..height), so it looks the same at 720p and 4K. Declare any of
these built-in uniforms and they are filled in automatically:

* ``uniform float iTime;``        seconds since the layer appeared
* ``uniform float2 iResolution;`` layer size in design pixels

Other uniforms come from ``uniforms={"name": value}``. A value is a number,
a 2-4 number sequence, a color string ("#4FD1C5" becomes a float4 in 0..1),
or a function ``f(t)`` of the layer time returning one of those.

Example::

    WAVES = '''
    uniform float iTime; uniform float2 iResolution; uniform half4 tint;
    half4 main(float2 xy) {
        float2 uv = xy / iResolution;
        float v = 0.5 + 0.5 * sin(uv.x * 12.0 + iTime * 2.0 + sin(uv.y * 8.0));
        return half4(tint.rgb * v, 1.0);
    }'''
    ShaderFill(WAVES, width=1920, height=1080, uniforms={"tint": "#4FD1C5"})

SkSL runs per pixel on the CPU: a full-frame 720p shader costs roughly 0.3 s per
frame. For smooth fields pass ``resolution=0.5`` (or 0.25) to shade fewer pixels
and upscale.

Requires skia-python (faceless-champ[skia]); works with every backend.
"""

from typing import Any

from .components import Component, finite


def _uniform_items(uniforms):
    if uniforms is None:
        return ()
    if not isinstance(uniforms, dict):
        raise TypeError("uniforms must be a dict of name -> value")
    items = []
    for name, value in uniforms.items():
        if not isinstance(name, str) or not name.isidentifier():
            raise ValueError(f"Invalid uniform name {name!r}")
        if not callable(value) and not isinstance(value, str):
            from ._skia_fx import uniform_value

            value = uniform_value(value, 0)
            value = tuple(value) if isinstance(value, list) else value
        items.append((name, value))
    return tuple(sorted(items, key=lambda item: item[0]))


class ShaderFill(Component):
    """A rectangle painted by a custom SkSL program (procedural backgrounds,
    gradients, noise, plasma, light rays, fractals...)."""

    def __init__(
        self,
        sksl: str,
        *,
        width: float = 1920,
        height: float = 1080,
        uniforms=None,
        resolution: float = 1.0,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        # SkSL runs per pixel on the CPU; smooth fields (gradients, auroras, noise)
        # look identical at resolution=0.5 or 0.25 and render 4-16x faster.
        self.resolution = finite(resolution, "resolution", 0.05)
        if self.resolution > 1:
            raise ValueError("resolution must be in (0, 1]")
        if not isinstance(sksl, str) or "main" not in sksl:
            raise ValueError("ShaderFill needs SkSL source defining half4 main(float2 xy)")
        self.sksl = sksl
        self.width, self.height = finite(width, "width", 1), finite(height, "height", 1)
        self.uniforms = _uniform_items(uniforms)
        self._animated = "iTime" in sksl or any(callable(v) for _, v in self.uniforms)
        from ._skia_fx import compile_shader

        try:
            compile_shader(sksl)  # compile errors raise ValueError right here, with Skia's message
        except RuntimeError:  # skia unavailable: validated again at render time
            pass

    def frame_key(self, age):
        return age if self._animated else 0

    def validate_render(self, backend, painter):
        from ._skia_fx import builder, compile_shader

        builder(compile_shader(self.sksl), self.uniforms, 0, {"iTime": 0, "iResolution": [1.0, 1.0]})
        return True

    def render_raster(self, state, factor, age, painter):
        from ._portable import guard_size
        from ._skia_fx import render_shader_fill

        size = max(1, round(self.width * factor)), max(1, round(self.height * factor))
        guard_size(size)
        if self.resolution >= 1:
            return render_shader_fill(self, size, factor, age)
        from PIL import Image as PILImage

        low = max(1, round(size[0] * self.resolution)), max(1, round(size[1] * self.resolution))
        with render_shader_fill(self, low, factor * self.resolution, age) as image:
            return image.resize(size, PILImage.Resampling.BICUBIC)


__all__ = ["ShaderFill"]
