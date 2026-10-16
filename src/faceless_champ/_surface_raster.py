"""Bounded one-shot Pillow raster stages. No scene, timeline or global caches."""

import math
from array import array
from contextlib import ExitStack, closing
from itertools import pairwise

from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFilter, ImageMath, ImageOps

from .gradients import LinearGradient, _linear_coefficients, _parameter, _sample

_MAX_SIDE = 8192
_MAX_PIXELS = 8_388_608
_MAX_WORK_BYTES = 192 * 1024**2
_TILE_ROWS = 64
_EDGE_BLUR = 0.75  # source pixels, applied only once to geometric coverage


def _allocation(width, height):
    # Check before multiplication/rounding as even finite Bounds edges can overflow their span.
    if not all(math.isfinite(v) and 1 <= v <= _MAX_SIDE / 2 for v in (width, height)):
        raise ValueError("Gradient allocation needs finite design sides in [1, 4096]; use a smaller design canvas")
    size = (round(width * 2), round(height * 2))
    pixels = size[0] * size[1]
    estimate = 20 * pixels + 96 * size[0] * min(_TILE_ROWS, size[1]) + 8 * 1024**2
    if pixels > _MAX_PIXELS or estimate > _MAX_WORK_BYTES:
        raise ValueError("Gradient allocation exceeds the 8,388,608-pixel / 192 MiB budget; use smaller Bounds")
    return size


def _math(expression, **images):
    # Use the callable API supported by Pillow >=10.4; no string expression evaluation.
    return ImageMath.lambda_eval(expression, **images)


def _axis(values, horizontal, size):
    data = array("f", values)
    line_size = (len(data), 1) if horizontal else (1, len(data))
    with closing(Image.frombytes("F", line_size, data.tobytes())) as line:
        return line.resize(size, Image.Resampling.NEAREST)


def _field(gradient, width, height, size, top, rows):
    w, h = size
    with ExitStack() as stack:
        x = stack.enter_context(closing(_axis((i / (w - 1) if w > 1 else 0.5 for i in range(w)), True, (w, rows))))
        y = stack.enter_context(
            closing(_axis((i / (h - 1) if h > 1 else 0.5 for i in range(top, top + rows)), False, (w, rows)))
        )
        if isinstance(gradient, LinearGradient):
            a, b, c = _linear_coefficients(gradient, width if w > 1 else 0, height if h > 1 else 0)
            return _math(lambda v: v["x"] * a + v["y"] * b + c, x=x, y=y)
        cx, cy = gradient.center
        radius = gradient.radius * min(width, height)
        return _math(lambda v: (((v["x"] - cx) * width) ** 2 + ((v["y"] - cy) * height) ** 2) ** 0.5 / radius, x=x, y=y)


def _straight(channels):
    """Unpremultiply float planes once; zero-alpha RGB remains canonical."""
    with ExitStack() as stack:
        alpha = stack.enter_context(closing(_math(lambda v: v["a"] + 0.5, a=channels[3]).convert("L")))
        visible = stack.enter_context(closing(alpha.point(lambda v: 255 if v else 0)))
        output = []
        for channel in channels[:3]:
            rgb = stack.enter_context(
                closing(
                    _math(lambda v: v["p"] * 255 / v["max"](v["a"], 1e-20) + 0.5, p=channel, a=channels[3]).convert("L")
                )
            )
            output.append(stack.enter_context(closing(ImageChops.multiply(rgb, visible))))
        return Image.merge("RGBA", (*output, alpha))


def _colorize(gradient, field):
    channels = [Image.new("F", field.size, value) for value in gradient.stops[0]._premultiplied]
    try:
        for left, right in pairwise(gradient.stops):
            span = right.offset - left.offset
            with closing(
                _math(
                    lambda v, start=left.offset, span=span: v["min"](v["max"]((v["t"] - start) / span, 0), 1), t=field
                )
            ) as ramp:
                for i, (a, b) in enumerate(zip(left._premultiplied, right._premultiplied)):
                    delta = b - a
                    if delta:
                        old = channels[i]
                        channels[i] = _math(lambda v, delta=delta: v["base"] + v["ramp"] * delta, base=old, ramp=ramp)
                        old.close()
        return _straight(channels)
    finally:
        for channel in channels:
            channel.close()


def _reference_tile(gradient, width, height, size, top, rows):
    w, h = size
    data = bytearray(w * rows * 4)
    cursor = 0
    for row in range(top, top + rows):
        y = row / (h - 1) if h > 1 else 0.5
        for col in range(w):
            x = col / (w - 1) if w > 1 else 0.5
            logical_w = width if w > 1 or not isinstance(gradient, LinearGradient) else 0
            logical_h = height if h > 1 or not isinstance(gradient, LinearGradient) else 0
            value = _parameter(gradient, x, y, logical_w, logical_h)
            data[cursor : cursor + 4] = bytes(_sample(gradient, value))
            cursor += 4
    return Image.frombytes("RGBA", (w, rows), bytes(data))


def _paint(gradient, width, height, size):
    if all(stop._rgba == gradient.stops[0]._rgba for stop in gradient.stops):
        return Image.new("RGBA", size, gradient.stops[0]._rgba)
    w, h = size
    if isinstance(gradient, LinearGradient) and gradient.angle in (0, 90, 180, 270):
        horizontal = gradient.angle in (0, 180)
        count = w if horizontal else h
        data = bytearray(count * 4)
        for i in range(count):
            x, y = (i / (count - 1) if count > 1 else 0.5), 0
            if not horizontal:
                x, y = 0, x
            t = _parameter(gradient, x, y, width if w > 1 else 0, height if h > 1 else 0)
            data[i * 4 : i * 4 + 4] = bytes(_sample(gradient, t))
        with closing(Image.frombytes("RGBA", (count, 1) if horizontal else (1, count), bytes(data))) as line:
            return line.resize(size, Image.Resampling.NEAREST)
    # Native F fields cannot resolve almost coincident stops or radial fields tiny
    # relative to the longest face side, where coordinate rounding is amplified.
    reference = any(b.offset - a.offset < 1e-3 for a, b in pairwise(gradient.stops))
    if not isinstance(gradient, LinearGradient):
        physical_radius = gradient.radius * min(width, height)
        reference |= physical_radius < 1e-3 * max(width, height)
    result = Image.new("RGBA", size)
    try:
        for top in range(0, h, _TILE_ROWS):
            rows = min(_TILE_ROWS, h - top)
            if reference:
                tile = _reference_tile(gradient, width, height, size, top, rows)
            else:
                with closing(_field(gradient, width, height, size, top, rows)) as field:
                    tile = _colorize(gradient, field)
            with closing(tile):
                result.paste(tile, (0, top))
        return result
    except BaseException:
        result.close()
        raise


def _extend_edges(paint, padding=4):
    """Clamp paint colors outside the face for its antialiased geometric edge."""
    width, height = paint.size
    result = ImageOps.expand(paint, padding)
    try:
        for box, position, size in (
            ((0, 0, 1, height), (0, padding), (padding, height)),
            ((width - 1, 0, width, height), (width + padding, padding), (padding, height)),
        ):
            with closing(paint.crop(box)) as line, closing(line.resize(size, Image.Resampling.NEAREST)) as strip:
                result.paste(strip, position)
        for row, target in ((padding, 0), (padding + height - 1, padding + height)):
            with (
                closing(result.crop((0, row, result.width, row + 1))) as line,
                closing(line.resize((result.width, padding), Image.Resampling.NEAREST)) as strip,
            ):
                result.paste(strip, (0, target))
        return result
    except BaseException:
        result.close()
        raise


def _coverage_replace(source, paint, position, coverage):
    """C*face + (1-C)*shadow in premultiplied float; bounded row scratch only."""
    x, y = position
    left, top = max(0, x), max(0, y)
    right, bottom = min(source.width, x + paint.width), min(source.height, y + paint.height)
    for row in range(top, bottom, _TILE_ROWS):
        box = (left, row, right, min(row + _TILE_ROWS, bottom))
        with ExitStack() as stack:

            def own(image):
                return stack.enter_context(closing(image))

            face = own(paint.crop((box[0] - x, box[1] - y, box[2] - x, box[3] - y)))
            shadow = own(source.crop(box))
            c = own(own(coverage.crop(box)).convert("F"))
            af = own(own(face.getchannel("A")).convert("F"))
            ab = own(own(shadow.getchannel("A")).convert("F"))
            wf = own(_math(lambda v: v["c"] * v["a"] / 255, c=c, a=af))
            wb = own(_math(lambda v: (1 - v["c"] / 255) * v["a"], c=c, a=ab))
            channels = []
            for channel in "RGB":
                f = own(own(face.getchannel(channel)).convert("F"))
                b = own(own(shadow.getchannel(channel)).convert("F"))
                channels.append(
                    own(_math(lambda v: (v["f"] * v["wf"] + v["b"] * v["wb"]) / 255, f=f, b=b, wf=wf, wb=wb))
                )
            channels.append(own(_math(lambda v: v["wf"] + v["wb"], wf=wf, wb=wb)))
            with closing(_straight(channels)) as composed:
                source.paste(composed, (left, row))


def gradient_card(bounds, gradient, radius, shadow, inset):
    """Return straight RGBA; caller owns it. Coverage replaces shadow under the face."""
    size = _allocation(bounds.width, bounds.height)
    raster_inset = inset * 2
    # Coverage and paint share the allocation's rounded dimensions, including its last sample.
    box = (raster_inset, raster_inset, size[0] - raster_inset - 1, size[1] - raster_inset - 1)
    width, height = bounds.width - 2 * inset, bounds.height - 2 * inset
    face_size = tuple(side - 2 * raster_inset for side in size)
    if min(face_size) < 1:
        raise ValueError("Gradient card face needs at least one raster sample per side")
    corner = min(radius, width / 2, height / 2) * 2
    source = Image.new("RGBA", size)
    try:
        with ExitStack() as stack:
            coverage = stack.enter_context(closing(Image.new("L", size)))
            ImageDraw.Draw(coverage).rounded_rectangle(box, radius=corner, fill=255)
            opaque_coverage = coverage.getextrema() == (255, 255)
            soft = (
                coverage
                if opaque_coverage
                else stack.enter_context(closing(coverage.filter(ImageFilter.GaussianBlur(_EDGE_BLUR))))
            )
            if shadow is not None:
                silhouette = stack.enter_context(closing(Image.new("L", size)))
                dx, dy = (v * 2 for v in shadow.offset)
                shifted = (box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy)
                ImageDraw.Draw(silhouette).rounded_rectangle(shifted, radius=corner, fill=255)
                with closing(silhouette.filter(ImageFilter.GaussianBlur(shadow.blur * 2))) as blurred:
                    color = ImageColor.getcolor(shadow.color, "RGBA")
                    alpha = stack.enter_context(closing(blurred.point(lambda v: round(v * color[3] / 255))))
                source.paste((*color[:3], 255), (0, 0, *size))
                source.putalpha(alpha)
            with closing(_paint(gradient, width, height, face_size)) as paint:
                if opaque_coverage:
                    source.paste(paint, (box[0], box[1]))
                else:
                    # Fractional coverage must mix premultiplied color, never straight RGBA.
                    with closing(_extend_edges(paint)) as extended:
                        _coverage_replace(source, extended, (box[0] - 4, box[1] - 4), soft)
            # Canonical zero RGB without changing partially transparent shadow color.
            with (
                closing(source.getchannel("A")) as alpha,
                closing(alpha.point(lambda v: 255 if v == 0 else 0)) as empty,
            ):
                source.paste((0, 0, 0, 0), (0, 0, *size), empty)
        return source
    except BaseException:
        source.close()
        raise
