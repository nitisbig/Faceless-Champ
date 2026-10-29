"""Skia helpers shared by every backend: SkSL compilation, blend and layer filters.

These run on CPU raster surfaces, so they work on the Pillow, Skia and effects
compositor paths alike (the production 4K path on CPU-only machines). Imported
lazily; only skia-python is required.
"""

import math
from functools import lru_cache

from PIL import Image as PILImage


def skia():
    from .backends._native import load_skia

    return load_skia()


@lru_cache(maxsize=128)
def compile_shader(sksl):
    """Compile SkSL once; raises ValueError with Skia's message and line marker."""
    s = skia()
    try:
        effect = s.RuntimeEffect.MakeForShader(sksl)
    except RuntimeError as exc:
        raise ValueError(f"SkSL shader does not compile:\n{exc}") from None
    if effect is None:
        raise ValueError("SkSL shader does not compile")
    return effect


def uniform_names(effect):
    return {u.name for u in effect.uniforms()}


def child_names(effect):
    return {c.name for c in effect.children()}


def uniform_value(value, time):
    """Numbers, sequences, color strings, or callables f(time) -> one of those."""
    if callable(value):
        value = value(time)
    if isinstance(value, str):
        from PIL import ImageColor

        return [v / 255 for v in ImageColor.getcolor(value, "RGBA")]
    if isinstance(value, (int, float)):
        return float(value)
    values = [float(v) for v in value]
    if not 1 <= len(values) <= 4 or not all(math.isfinite(v) for v in values):
        raise ValueError("Shader uniforms must be 1-4 finite numbers")
    return values[0] if len(values) == 1 else values


def builder(effect, uniforms, time, builtins):
    """A RuntimeShaderBuilder with built-in and user uniforms set where declared."""
    s = skia()
    b = s.RuntimeShaderBuilder(effect)
    declared = uniform_names(effect)
    for name, value in {**builtins, **dict(uniforms)}.items():
        if name in declared:
            b.setUniform(name, uniform_value(value, time))
    missing = declared - set(builtins) - {name for name, _ in uniforms}
    if missing:
        raise ValueError(f"Shader uniforms without values: {', '.join(sorted(missing))}")
    return b


def to_skia(image):
    from .backends._native import image_from_pillow

    return image_from_pillow(image, skia())


def to_pillow(image):
    from .backends._native import image_to_pillow

    return image_to_pillow(image, skia())


def surface(size):
    s = skia()
    info = s.ImageInfo.Make(
        *size, s.ColorType.kRGBA_8888_ColorType, s.AlphaType.kPremul_AlphaType, s.ColorSpace.MakeSRGB()
    )
    result = s.Surface.MakeRaster(info)
    if result is None:
        raise RuntimeError("Skia could not allocate a raster surface")
    return result


def blend_images(dst, src, mode, offset=(0, 0)):
    """Composite ``src`` onto ``dst`` (both RGBA PIL) at offset with a named blend mode."""
    from .blending import skia_blend

    s = skia()
    out = surface(dst.size)
    canvas = out.getCanvas()
    canvas.drawImage(to_skia(dst), 0, 0, s.SamplingOptions(), s.Paint(BlendMode=s.BlendMode.kSrc))
    canvas.drawImage(to_skia(src), offset[0], offset[1], s.SamplingOptions(), s.Paint(BlendMode=skia_blend(s, mode)))
    return to_pillow(out.makeImageSnapshot())


def _run(image, shader_builder, child_shaders):
    s = skia()
    for name, value in child_shaders.items():
        shader_builder.setChild(name, value)
    out = surface(image.size)
    paint = s.Paint(Shader=shader_builder.makeShader())
    paint.setBlendMode(s.BlendMode.kSrc)
    out.getCanvas().drawPaint(paint)
    return to_pillow(out.makeImageSnapshot())


def layer_shader(image, effect, uniforms, time, scale, content_box, mix=1.0):
    """Run a ShaderEffect over a layer. SkSL sees ``content`` plus built-ins."""
    s = skia()
    x, y, w, h = content_box or (0, 0, *image.size)
    builtins = {
        "iTime": time,
        "iResolution": [float(image.width), float(image.height)],
        "iScale": float(scale),
        "iBox": [float(x), float(y), float(w), float(h)],
    }
    source = to_skia(image)
    b = builder(effect, uniforms, time, builtins)
    result = _run(image, b, {"content": source.makeShader(s.TileMode.kDecal, s.TileMode.kDecal)})
    return result if mix >= 1 else PILImage.blend(image, result, max(0.0, mix))


DISPLACE_SKSL = """
uniform shader content;
uniform shader field;
uniform float amplitude;
half4 main(float2 xy) {
    half4 n = unpremul(field.eval(xy));
    float2 d = (float2(n.r, n.g) - 0.5) * 2.0 * amplitude;
    return content.eval(xy + d);
}
"""


def displace(image, effect, time, scale, content_box):
    """Turbulent (Perlin) or image-driven displacement of a layer."""
    s = skia()
    x, y, w, h = content_box or (0, 0, *image.size)
    if effect.map is not None:
        with PILImage.open(effect.map) as source:
            field_image = to_skia(source.convert("RGBA"))
        matrix = s.Matrix.Translate(x, y)
        matrix.preScale(w / field_image.width(), h / field_image.height())
        field = field_image.makeShader(s.TileMode.kClamp, s.TileMode.kClamp, s.SamplingOptions(), matrix)
    else:
        size = max(effect.size * scale, 1e-3)
        field = s.PerlinNoiseShader.MakeFractalNoise(1 / size, 1 / size, max(1, round(effect.octaves)), effect.seed)
        drift = effect.speed * scale * time
        field = field.makeWithLocalMatrix(s.Matrix.Translate(drift, drift * 0.37))
    b = s.RuntimeShaderBuilder(compile_shader(DISPLACE_SKSL))
    b.setUniform("amplitude", float(effect.amplitude * scale))
    return _run(
        image,
        b,
        {"content": to_skia(image).makeShader(s.TileMode.kDecal, s.TileMode.kDecal), "field": field},
    )


def render_shader_fill(component, size, factor, age):
    """Rasterize a ShaderFill at ``size`` pixels; xy is in design pixels."""
    s = skia()
    effect = compile_shader(component.sksl)
    builtins = {"iTime": age, "iResolution": [float(component.width), float(component.height)]}
    b = builder(effect, component.uniforms, age, builtins)
    out = surface(size)
    canvas = out.getCanvas()
    canvas.scale(size[0] / component.width, size[1] / component.height)
    paint = s.Paint(Shader=b.makeShader(), AntiAlias=True)
    canvas.drawRect(s.Rect.MakeWH(component.width, component.height), paint)
    return to_pillow(out.makeImageSnapshot())
