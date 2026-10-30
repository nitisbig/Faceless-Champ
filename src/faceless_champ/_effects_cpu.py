"""Float32 CPU reference for the built-in shader contracts. Imported lazily."""

import math
from functools import lru_cache

from PIL import Image, ImageColor

from .effects import _phase


def numpy():
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("CPU effects need faceless-champ[effects] (or faceless-champ[gpu])") from exc
    return np


def linear(value):
    np = numpy()
    return np.where(value <= 0.04045, value / 12.92, ((value + 0.055) / 1.055) ** 2.4)


def encoded(value):
    np = numpy()
    value = np.maximum(value, 0)
    return np.where(value <= 0.0031308, value * 12.92, 1.055 * value ** (1 / 2.4) - 0.055)


def pixels(image):
    np = numpy()
    a = np.asarray(image.convert("RGBA"), dtype="f4") / 255
    a[..., :3] = linear(a[..., :3]) * a[..., 3:4]
    return a


def image(a):
    np = numpy()
    alpha = np.clip(a[..., 3:4], 0, 1)
    rgb = encoded(a[..., :3] / np.maximum(alpha, 1e-8))
    out = np.concatenate((np.where(alpha > 0, rgb, 0), alpha), axis=2)
    quantized = np.floor(np.clip(out, 0, 1) * 255 + 0.5).astype("uint8")
    quantized[quantized[..., 3] == 0] = 0
    return Image.fromarray(quantized)


def sample(a, x, y):
    np = numpy()
    h, w = a.shape[:2]
    # Clamp-to-edge agrees with the GPU sampler. Effect padding supplies zero borders.
    x, y = np.clip(x, 0, w - 1), np.clip(y, 0, h - 1)
    ix, iy = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = (x - ix)[..., None], (y - iy)[..., None]
    return (
        (a[iy, ix] * (1 - fx) + a[iy, np.minimum(ix + 1, w - 1)] * fx) * (1 - fy)
        + (a[np.minimum(iy + 1, h - 1), ix] * (1 - fx) + a[np.minimum(iy + 1, h - 1), np.minimum(ix + 1, w - 1)] * fx)
        * fy
    ).astype("f4")


def resize(a, size):
    np = numpy()
    w, h = size
    x = (np.arange(w, dtype="f4") + 0.5) * a.shape[1] / w - 0.5
    y = (np.arange(h, dtype="f4") + 0.5) * a.shape[0] / h - 0.5
    return sample(a, x[None, :], y[:, None])


@lru_cache(maxsize=256)
def kernel(radius):
    np = numpy()
    count = min(64, math.ceil(3 * radius))
    offsets = np.arange(-count, count + 1, dtype="f4")
    weights = np.exp(-0.5 * (offsets / max(radius, 1e-6)) ** 2)
    weights /= weights.sum()
    return weights


def blur(a, radius):
    np = numpy()
    if radius <= 0:
        return a.copy()
    size = a.shape[1], a.shape[0]
    reduction = max(1, math.ceil(3 * radius / 64))
    if reduction > 1:
        a = resize(a, (max(1, math.ceil(size[0] / reduction)), max(1, math.ceil(size[1] / reduction))))
    weights = kernel(radius / reduction)
    n = len(weights) // 2
    for axis in (1, 0):
        padding = [(0, 0)] * 3
        padding[axis] = (n, n)
        padded = np.pad(a, padding, mode="edge")
        out = np.zeros_like(a)
        for i, weight in enumerate(weights):
            sl = [slice(None)] * 3
            sl[axis] = slice(i, i + a.shape[axis])
            out += padded[tuple(sl)] * weight
        a = out
    return resize(a, size) if reduction > 1 else a


def content(source, stack, scale, time, content_box=None):
    if stack is not None and stack.uses_skia:
        # Skia-backed layer filters run first, on encoded pixels, then the float pipeline.
        from . import _skia_fx

        if stack.morphology is not None and stack.morphology.radius > 0:
            source = _skia_fx.morphology(source, stack.morphology, scale)
        if stack.displacement is not None and stack.displacement.amplitude:
            source = _skia_fx.displace(source, stack.displacement, time, scale, content_box)
        if stack.lighting is not None and stack.lighting.mix > 0:
            source = _skia_fx.lighting(source, stack.lighting, scale, content_box)
        if stack.shader is not None and stack.shader.mix > 0:
            e = stack.shader
            source = _skia_fx.layer_shader(
                source, _skia_fx.compile_shader(e.sksl), e.uniforms, time, scale, content_box, e.mix
            )
    if stack is None or not any((stack.blur, stack.distortion, stack.chromatic, stack.light_sweep)):
        return source.copy()
    np = numpy()
    a = pixels(source)
    h, w = a.shape[:2]
    ox, oy, logical_w, logical_h = content_box or (0, 0, w, h)
    x, y = np.meshgrid(np.arange(w, dtype="f4"), np.arange(h, dtype="f4"))
    if (e := stack.light_sweep) is not None:
        center = _phase(time, e.speed, 1) % 1
        band = np.exp(-0.5 * (((x + 0.5 - ox) / max(logical_w, 1e-6) - center) / max(e.width, 1e-6)) ** 2)
        a[..., :3] *= (1 + e.intensity * band)[..., None]
    if (e := stack.distortion) is not None:
        a = sample(
            a,
            x
            + e.amplitude
            * scale
            * np.sin((y + 0.5 - oy) / max(logical_h, 1e-6) * math.tau * e.frequency + _phase(time, e.speed)),
            y,
        )
    if (e := stack.chromatic) is not None:
        r, b = sample(a, x + e.offset * scale, y), sample(a, x - e.offset * scale, y)
        a[..., 0], a[..., 2] = r[..., 0], b[..., 2]
        a[..., 3] = np.maximum(a[..., 3], np.maximum(r[..., 3], b[..., 3]))
    if (e := stack.blur) is not None:
        a = blur(a, e.radius * scale)
    return image(a)


def halos(source, stack, scale):
    if stack is None or not any((stack.glow, stack.bloom)):
        return source.copy()
    np = numpy()
    a = pixels(source)
    base = a.copy()
    if (e := stack.glow) is not None and e.intensity:
        color = np.array(ImageColor.getcolor(e.color, "RGBA"), dtype="f4") / 255
        alpha = np.clip(blur(base, e.radius * scale)[..., 3:4] * e.intensity * color[3], 0, 1)
        glow = np.concatenate((linear(color[:3]) * alpha, alpha), axis=2)
        a = a + glow * (1 - a[..., 3:4])
    if (e := stack.bloom) is not None and e.intensity:
        lum = (base[..., :3] @ np.array([0.2126, 0.7152, 0.0722], dtype="f4")) / np.maximum(base[..., 3], 1e-8)
        bright = base * (np.maximum(lum - e.threshold, 0) / np.maximum(lum, 1e-8))[..., None]
        # A fixed three-scale pyramid supplies broad light without a canvas-size kernel.
        light = np.zeros_like(base)
        for level in (1, 2, 4):
            low = resize(bright, (max(1, math.ceil(source.width / level)), max(1, math.ceil(source.height / level))))
            light += resize(blur(low, e.radius * scale / level), source.size) / 3
        light *= e.intensity
        a[..., :3] += light[..., :3]
        a[..., 3] = np.maximum(a[..., 3], np.clip(light[..., 3], 0, 1))
    return image(a)


def background(component, age, size, *, bounds):
    np = numpy()
    from .procedural import ParticleField, particle_data

    w, h = size
    color = np.array(ImageColor.getcolor(component.color, "RGBA"), dtype="f4") / 255
    if isinstance(component, ParticleField):
        from PIL import ImageDraw

        out = Image.new("RGBA", size)
        qx, qy = w / bounds.width, h / bounds.height
        r = component.radius * min(qx, qy)
        for x, y, opacity in particle_data(component, age):
            tile = Image.new("RGBA", (max(1, math.ceil(2 * r + 2)),) * 2)
            ImageDraw.Draw(tile).ellipse(
                (1, 1, 2 * r + 1, 2 * r + 1),
                fill=(*tuple(round(v * 255) for v in color[:3]), round(color[3] * opacity * 255)),
            )
            out.alpha_composite(
                tile,
                (
                    round((x - component.width / 2 - bounds.left) * qx - r - 1),
                    round((y - component.height / 2 - bounds.top) * qy - r - 1),
                ),
            )
        return out
    x = (np.arange(w, dtype="f4")[None, :] + 0.5) / w
    y = (np.arange(h, dtype="f4")[:, None] + 0.5) / h
    t = component.frame_key(age) + (component.seed % 65536) / 65536
    field = np.sin(x * 8 + t) * np.sin(y * 6 - t * 0.7)
    if component.kind == "aurora":
        field = np.exp(-(((y - 0.45 - 0.15 * np.sin(x * 7 + t)) / 0.18) ** 2)) * (0.7 + 0.3 * field)
    else:
        field = 0.5 + 0.5 * field
    rgb = np.clip(color[:3] * (0.15 + field[..., None]) + (1 - color[:3]) * field[..., None] * 0.18, 0, 1)
    out = np.concatenate((rgb, np.full((h, w, 1), color[3], dtype="f4")), axis=2)
    return Image.fromarray(np.floor(out * 255 + 0.5).astype("uint8"))


def crossfade(first, second, progress, transition=None):
    from .transitions import LuminanceWipe, ZoomBlurTransition

    if progress <= 0:
        return first.copy()
    if progress >= 1:
        return second.copy()
    if transition is None:
        return Image.blend(first, second, progress)
    np = numpy()
    a, b = np.asarray(first, dtype="f4") / 255, np.asarray(second, dtype="f4") / 255
    h, w = a.shape[:2]
    x, y = np.meshgrid(np.arange(w, dtype="f4"), np.arange(h, dtype="f4"))
    if isinstance(transition, ZoomBlurTransition):
        amount = transition.strength * math.sin(math.pi * progress)
        aa, bb = np.zeros_like(a), np.zeros_like(b)
        for i in range(8):
            zoom = 1 + amount * i / 7
            xx, yy = (x + 0.5 - w / 2) / zoom + w / 2 - 0.5, (y + 0.5 - h / 2) / zoom + h / 2 - 0.5
            aa += sample(a, xx, yy) / 8
            bb += sample(b, xx, yy) / 8
        out = aa * (1 - progress) + bb * progress
    else:
        field = (
            a[..., :3] @ np.array([0.2126, 0.7152, 0.0722], dtype="f4")
            if isinstance(transition, LuminanceWipe)
            else (x + 0.5) / w
        )
        soft = max(transition.softness, 1e-6)
        u = np.clip((progress * (1 + soft) - field) / soft, 0, 1)
        u = u * u * (3 - 2 * u)
        out = a * (1 - u[..., None]) + b * u[..., None]
    return Image.fromarray(np.floor(np.clip(out, 0, 1) * 255).astype("uint8"))
