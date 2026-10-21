"""Pillow rasterization of the portable retained-vector subset."""

import math
from itertools import pairwise

from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFilter

from .gradients import LinearGradient, RadialGradient


def guard_size(size):
    if any(not isinstance(v, int) or v < 1 or v > 16384 for v in size) or size[0] * size[1] > 33_554_432:
        raise ValueError("Raster allocation exceeds 16384 sides / 33,554,432 pixels")


def paint_image(fill, width, height, size):
    guard_size(size)
    if isinstance(fill, (LinearGradient, RadialGradient)):
        from ._surface_raster import _paint

        return _paint(fill, width, height, size)
    return Image.new("RGBA", size, tuple(round(v) for v in fill) if isinstance(fill, tuple) else fill)


def surface_sprite(c, factor):
    from ._surface_raster import _coverage_replace, _extend_edges
    from .surfaces import _shadow_padding

    size = max(1, round(c.width * factor)), max(1, round(c.height * factor))
    guard_size(size)
    source = Image.new("RGBA", size)
    if c.pattern == "dots":
        draw = ImageDraw.Draw(source)
        r = c.dot_radius * factor
        for row in range(math.ceil(c.height / c.spacing)):
            for col in range(math.ceil(c.width / c.spacing)):
                x, y = (col + 0.5) * c.spacing * factor, (row + 0.5) * c.spacing * factor
                draw.ellipse((x - r, y - r, x + r, y + r), fill=c.fill)
        return source
    inset = round(_shadow_padding(c.surface_shadow) * factor)
    face_size = size[0] - 2 * inset, size[1] - 2 * inset
    if min(face_size) < 1:
        raise ValueError("Surface face needs at least one raster sample")
    box = inset, inset, size[0] - inset - 1, size[1] - inset - 1
    radius = min(c.radius * factor, min(face_size) / 2)
    coverage = Image.new("L", size)
    ImageDraw.Draw(coverage).rounded_rectangle(box, radius=radius, fill=255)
    if c.surface_shadow:
        s = c.surface_shadow
        dx, dy = (v * factor for v in s.offset)
        silhouette = Image.new("L", size)
        ImageDraw.Draw(silhouette).rounded_rectangle(
            (box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy), radius=radius, fill=255
        )
        color = ImageColor.getcolor(s.color, "RGBA")
        alpha = silhouette.filter(ImageFilter.GaussianBlur(s.blur * factor)).point(lambda a: round(a * color[3] / 255))
        source.paste((*color[:3], 255), (0, 0, *size))
        source.putalpha(alpha)
    logical_w = c.width - 2 * _shadow_padding(c.surface_shadow)
    logical_h = c.height - 2 * _shadow_padding(c.surface_shadow)
    with paint_image(c.fill, logical_w, logical_h, face_size) as fill, _extend_edges(fill) as extended:
        _coverage_replace(source, extended, (inset - 4, inset - 4), coverage)
    empty = source.getchannel("A").point(lambda a: 255 if a == 0 else 0)
    source.paste((0, 0, 0, 0), (0, 0, *size), empty)
    return source


def shape_sprite(c, state, factor):
    from .components import Circle, Ellipse, Line, Polyline, Triangle
    from .paths import VectorPath

    w, h = max(1, round(state["width"] * factor)), max(1, round(state["height"] * factor))
    sw = max(1, round(state["stroke_width"] * factor))
    size = w + 2 * sw, h + 2 * sw
    guard_size(size)
    coverage, stroke = Image.new("L", size), Image.new("L", size)
    d = ImageDraw.Draw(coverage)
    box = sw, sw, sw + w - 1, sw + h - 1
    contours = None
    if isinstance(c, VectorPath):
        if not c.portable:
            raise ValueError("Compound paths and even_odd fill require backend='skia'")
        path = c.path.transformed(
            sx=state["width"] / c.width * factor, sy=state["height"] / c.height * factor, dx=sw, dy=sw
        )
        contours = path.flatten(0.25)
        closed = c.path.commands[-1][0] == "Z"
    elif isinstance(c, Polyline):
        pts = tuple(
            (sw + x * state["width"] / c.width * factor, sw + y * state["height"] / c.height * factor)
            for x, y in c.points
        )
        contours = (pts + (pts[:1] if c.closed else ()),)
        closed = c.closed
    else:
        closed = not isinstance(c, Line)
    progress = state["draw"]
    if progress >= 1 and closed:
        if contours:
            d.polygon(contours[0], fill=255)
        elif isinstance(c, (Circle, Ellipse)):
            d.ellipse(box, fill=255)
        elif isinstance(c, Triangle):
            d.polygon(((sw + w / 2, sw), (sw + w, sw + h), (sw, sw + h)), fill=255)
        else:
            d.rounded_rectangle(box, radius=min(state.get("corner_radius", 0) * factor, min(w, h) / 2), fill=255)
    if contours is None:
        # Reuse the legacy outline producer, with a white stroke and no fill.
        from copy import copy

        from ._rendering.raster import RasterPainter

        view = copy(c)
        view.fill, view.stroke = None, "white"
        view_state = {**state, "fill": (0, 0, 0, 0), "stroke": (255, 255, 255, 255)}
        with RasterPainter(source_cache_mb=0) as renderer:
            stroke = renderer.primitive(view, view_state, factor, 0).getchannel("A")
    else:
        draw = ImageDraw.Draw(stroke)
        lengths = [math.dist(a, b) for pts in contours for a, b in pairwise(pts)]
        remaining = sum(lengths) * progress
        for pts in contours:
            visible = [pts[0]]
            for a, b in pairwise(pts):
                length = math.dist(a, b)
                u = min(1, remaining / length) if length else 1
                visible.append(tuple(x + (y - x) * u for x, y in zip(a, b)))
                remaining -= length * u
                if u < 1:
                    break
            if progress > 0:
                draw.line(visible, fill=255, width=sw, joint="curve")
                if getattr(c, "line_cap", "butt") == "round" and not closed:
                    for x, y in (visible[0], visible[-1]):
                        draw.ellipse((x - sw / 2, y - sw / 2, x + sw / 2, y + sw / 2), fill=255)
    result = Image.new("RGBA", size)
    fill = state["fill"]
    if fill is not None:
        with paint_image(fill, state["width"], state["height"], (w, h)) as field:
            expanded = Image.new("RGBA", size)
            expanded.paste(field, (sw, sw))
            expanded.putalpha(ImageChops.multiply(expanded.getchannel("A"), coverage))
            result.alpha_composite(expanded)
    if state["stroke"][3] > 0 and state["stroke_width"] > 0:
        color = tuple(round(v) for v in state["stroke"])
        outline = Image.new("RGBA", size, color)
        outline.putalpha(stroke.point(lambda a: round(a * color[3] / 255)))
        result.alpha_composite(outline)
    return result
