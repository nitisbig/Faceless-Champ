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


def _filtered(image, image_filter):
    """Draw a Skia image through an ImageFilter onto a same-size raster surface."""
    s = skia()
    out = surface((image.width(), image.height()))
    out.getCanvas().drawImage(image, 0, 0, s.SamplingOptions(), s.Paint(ImageFilter=image_filter))
    return out.makeImageSnapshot()


def morphology(image, effect, scale):
    """Dilate or erode a layer by ``effect.radius`` design pixels."""
    s = skia()
    r = round(effect.radius * scale)
    if r <= 0:
        return image
    make = s.ImageFilters.Dilate if effect.mode == "dilate" else s.ImageFilters.Erode
    return to_pillow(_filtered(to_skia(image), make(r, r)))


LIGHTING_SKSL = """
uniform shader content;
uniform shader diffuse;
uniform shader specular;
uniform float amount;
half4 main(float2 xy) {
    half4 c = content.eval(xy);
    // Diffuse is normalized so flat areas read 0.5; x2 keeps their color.
    half3 lit = c.rgb * diffuse.eval(xy).rgb * 2.0 + specular.eval(xy).rgb * c.a;
    return mix(c, half4(min(lit, half3(c.a)), c.a), amount);
}
"""


def lighting(image, effect, scale, content_box):
    """Bevel/emboss shading from Skia's diffuse and specular lighting filters."""
    from PIL import ImageColor

    s = skia()
    x, y, w, h = content_box or (0, 0, *image.size)
    r, g, b, _ = ImageColor.getcolor(effect.color, "RGBA")
    color = s.ColorSetARGB(255, r, g, b)
    depth = effect.depth * scale
    bevel = max(effect.bevel * scale, 0.0)
    height_map = s.ImageFilters.Blur(bevel / 2, bevel / 2) if bevel > 0 else None
    shininess = min(max(effect.shininess, 1.0), 128.0)
    center = (x + w / 2, y + h / 2)
    if effect.light == "distant":
        az, el = math.radians(effect.azimuth), math.radians(effect.elevation)
        direction = s.Point3(math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))
        flat = math.sin(el)
        specular = s.ImageFilters.DistantLitSpecular(direction, color, depth, effect.specular, shininess, height_map)
        diffuse_args = (direction, color, depth)
        make_diffuse = s.ImageFilters.DistantLitDiffuse
    else:
        location = s.Point3(x + effect.x * w, y + effect.y * h, max(effect.height * scale, 1e-3))
        flat = location.fZ / math.dist((location.fX, location.fY, location.fZ), (*center, 0))
        if effect.light == "point":
            diffuse_args = (location, color, depth)
            make_diffuse = s.ImageFilters.PointLitDiffuse
            specular = s.ImageFilters.PointLitSpecular(location, color, depth, effect.specular, shininess, height_map)
        else:
            cone = min(max(effect.cone, 0.1), 90.0)
            target = s.Point3(*center, 0)
            diffuse_args = (location, target, 1.0, cone, color, depth)
            make_diffuse = s.ImageFilters.SpotLitDiffuse
            specular = s.ImageFilters.SpotLitSpecular(
                location, target, 1.0, cone, color, depth, effect.specular, shininess, height_map
            )
    kd = 0.5 * effect.diffuse / max(flat, 0.05)
    diffuse = make_diffuse(*diffuse_args, kd, height_map)
    source = to_skia(image)
    lit = {name: _filtered(source, f) for name, f in (("diffuse", diffuse), ("specular", specular))}
    b = s.RuntimeShaderBuilder(compile_shader(LIGHTING_SKSL))
    b.setUniform("amount", float(min(max(effect.mix, 0.0), 1.0)))
    children = {"content": source.makeShader(s.TileMode.kDecal, s.TileMode.kDecal)}
    children.update({name: img.makeShader(s.TileMode.kClamp, s.TileMode.kClamp) for name, img in lit.items()})
    return _run(image, b, children)


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
