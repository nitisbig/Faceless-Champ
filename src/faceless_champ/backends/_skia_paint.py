"""Native paint/geometry translation of public, renderer-neutral descriptions."""

import math

from ..components import Arrow, Circle, Ellipse, Line, Polyline, Rectangle, Triangle
from ..gradients import LinearGradient, RadialGradient
from ..motion import rgba
from ..paths import VectorPath


def color(s, value, opacity=1):
    r, g, b, a = rgba(value)
    return s.ColorSetARGB(round(a * opacity), round(r), round(g), round(b))


def paint(s, fill, box, opacity=1):
    p = s.Paint(AntiAlias=True)
    if not isinstance(fill, (LinearGradient, RadialGradient)):
        p.setColor(color(s, fill, opacity))
        return p
    colors, stops = [color(s, stop._rgba) for stop in fill.stops], [stop.offset for stop in fill.stops]
    if stops[0] > 0:
        colors.insert(0, colors[0])
        stops.insert(0, 0)
    if stops[-1] < 1:
        colors.append(colors[-1])
        stops.append(1)
    flags = s.GradientShader.kInterpolateColorsInPremul_Flag
    if isinstance(fill, LinearGradient):
        angle = math.radians(fill.angle)
        dx, dy = math.cos(angle), math.sin(angle)
        span = abs(dx * box.width) + abs(dy * box.height)
        cx, cy = box.center
        shader = s.GradientShader.MakeLinear(
            [(cx - dx * span / 2, cy - dy * span / 2), (cx + dx * span / 2, cy + dy * span / 2)],
            colors,
            stops,
            flags=flags,
        )
    else:
        shader = s.GradientShader.MakeRadial(
            (box.left + box.width * fill.center[0], box.top + box.height * fill.center[1]),
            fill.radius * min(box.width, box.height),
            colors,
            stops,
            flags=flags,
        )
    if shader is None:
        raise ValueError("Cannot construct native gradient")
    p.setShader(shader)
    p.setAlphaf(opacity)
    return p


def path_data(s, data):
    b = s.PathBuilder()
    for c in data.commands:
        {"M": b.moveTo, "L": b.lineTo, "Q": b.quadTo, "C": b.cubicTo, "Z": b.close}[c[0]](*c[1:])
    return b.detach()


def shape_path(s, c, state):
    w, h = state["width"], state["height"]
    b = s.PathBuilder()
    if isinstance(c, VectorPath):
        path = c.path.transformed(sx=w / c.width, sy=h / c.height, dx=-w / 2, dy=-h / 2)
        b = s.PathBuilder(path_data(s, path))
        b.setFillType(s.PathFillType.kEvenOdd if c.fill_rule == "even_odd" else s.PathFillType.kWinding)
        closed = c.path.commands[-1][0] == "Z"
    elif isinstance(c, Polyline):
        points = [(x * w / c.width - w / 2, y * h / c.height - h / 2) for x, y in c.points]
        b.moveTo(*points[0])
        for p in points[1:]:
            b.lineTo(*p)
        if c.closed:
            b.close()
        closed = c.closed
    elif isinstance(c, (Circle, Ellipse)):
        b.addOval(s.Rect.MakeXYWH(-w / 2, -h / 2, w, h), s.PathDirection.kCW, 3)
        closed = True
    elif isinstance(c, Triangle):
        b.moveTo(0, -h / 2).lineTo(w / 2, h / 2).lineTo(-w / 2, h / 2).close()
        closed = True
    elif isinstance(c, Line):
        b.moveTo(-w / 2, 0).lineTo(w / 2, 0)
        closed = False
    else:
        radius = min(state.get("corner_radius", 0), w / 2, h / 2) if isinstance(c, Rectangle) else 0
        b.addRRect(s.RRect.MakeRectXY(s.Rect.MakeXYWH(-w / 2, -h / 2, w, h), radius, radius))
        closed = True
    return b.detach(), closed


def partial_path(s, path, progress):
    if progress >= 1:
        return path
    lengths = []
    measure = s.PathMeasure(path, False)
    while True:
        lengths.append(measure.getLength())
        if not measure.nextContour():
            break
    remaining = sum(lengths) * progress
    measure = s.PathMeasure(path, False)
    result = s.Path()
    for length in lengths:
        if remaining > 0 and length > 0:
            measure.getSegment(0, min(length, remaining), result, True)
        remaining -= length
        if not measure.nextContour():
            break
    return result


def draw_shape(s, canvas, c, state, opacity):
    from ..layout import Bounds

    path, closed = shape_path(s, c, state)
    w, h = state["width"], state["height"]
    progress = state["draw"]
    box = Bounds(-w / 2, -h / 2, w / 2, h / 2)
    if closed and progress >= 1:
        canvas.drawPath(path, paint(s, state["fill"], box, opacity))
    if state["stroke"][3] > 0 and state["stroke_width"] > 0 and progress > 0:
        p = paint(s, state["stroke"], box, opacity)
        p.setStyle(s.Paint.kStroke_Style)
        p.setStrokeWidth(state["stroke_width"])
        p.setStrokeJoin(s.Paint.kRound_Join)
        p.setStrokeCap(
            {"round": s.Paint.kRound_Cap, "square": s.Paint.kSquare_Cap}.get(
                getattr(c, "line_cap", "butt"), s.Paint.kButt_Cap
            )
        )
        if isinstance(c, Polyline) and c.draw_by == "x" and progress < 1:
            # Match the public x-based reveal, rather than clipping arc length.
            end = c.width * progress
            b = s.PathBuilder().moveTo(-w / 2, -h / 2 + c.points[0][1] * h / c.height)
            for a, d in zip(c.points, c.points[1:]):
                u = min(1, max(0, (end - a[0]) / (d[0] - a[0])))
                b.lineTo(
                    (a[0] + (d[0] - a[0]) * u) * w / c.width - w / 2, (a[1] + (d[1] - a[1]) * u) * h / c.height - h / 2
                )
                if u < 1:
                    break
            visible = b.detach()
        else:
            visible = partial_path(s, path, progress)
        canvas.drawPath(visible, p)
        if isinstance(c, Arrow):
            tip = c.tip_size * min(1, max(0, (progress - 0.85) / 0.15))
            x = -w / 2 + w * progress
            if tip:
                b = s.PathBuilder().moveTo(x, 0).lineTo(x - tip, -tip / 2).lineTo(x - tip, tip / 2).close()
                canvas.drawPath(b.detach(), paint(s, state["stroke"], box, opacity))


def draw_surface(s, canvas, c, opacity=1):
    from ..layout import Bounds
    from ..surfaces import _shadow_padding

    if c.pattern == "dots":
        p = paint(s, c.fill, Bounds(0, 0, c.width, c.height), opacity)
        for row in range(math.ceil(c.height / c.spacing)):
            for col in range(math.ceil(c.width / c.spacing)):
                canvas.drawCircle(
                    (col + 0.5) * c.spacing - c.width / 2, (row + 0.5) * c.spacing - c.height / 2, c.dot_radius, p
                )
        return
    inset = _shadow_padding(c.surface_shadow)
    box = Bounds(-c.width / 2 + inset, -c.height / 2 + inset, c.width / 2 - inset, c.height / 2 - inset)
    radius = min(c.radius, box.width / 2, box.height / 2)
    rect = s.Rect.MakeLTRB(box.left, box.top, box.right, box.bottom)
    if c.surface_shadow:
        shadow = c.surface_shadow
        p = paint(s, shadow.color, box, opacity)
        if shadow.blur:
            p.setMaskFilter(s.MaskFilter.MakeBlur(s.BlurStyle.kNormal_BlurStyle, shadow.blur))
        canvas.save()
        canvas.translate(*shadow.offset)
        canvas.drawRoundRect(rect, radius, radius, p)
        canvas.restore()
    p = paint(s, c.fill, box, opacity)
    if c.surface_shadow:
        # Face coverage replaces the padded shadow, even for transparent fills.
        p.setBlendMode(s.BlendMode.kSrc)
    canvas.drawRoundRect(rect, radius, radius, p)
