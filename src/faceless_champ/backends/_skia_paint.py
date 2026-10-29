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


def _append_segment(s, measure, start, stop, result):
    """skia-python's getSegment resets its destination, so collect each piece separately."""
    piece = s.Path()
    if measure.getSegment(start, stop, piece, True):
        result.addPath(piece)


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
            _append_segment(s, measure, 0, min(length, remaining), result)
        remaining -= length
        if not measure.nextContour():
            break
    return result


def _on_spans(lo, hi, pattern, phase):
    """Global-distance spans inside [lo, hi] where the dash pattern is on."""
    import math as _math

    pattern = [max(v, 1e-3) for v in pattern]
    period = sum(pattern)
    k = _math.floor((lo + phase) / period)
    spans = []
    while True:
        origin = k * period - phase
        if origin >= hi:
            break
        cursor = origin
        for index, length in enumerate(pattern):
            if index % 2 == 0:
                a, b = max(lo, cursor), min(hi, cursor + length)
                if b > a:
                    spans.append((a, b))
            cursor += length
        k += 1
        if len(spans) > 100_000:
            raise ValueError("dash pattern is too fine for this path length")
    return spans


def styled_path(s, path, state, closed, pattern=None):
    """Trim Paths + dashes over a native path: [trim_start, draw] shifted by
    trim_offset (wrapping on closed paths); dashes anchored to the path start."""
    from .._strokes import intervals

    lengths = []
    measure = s.PathMeasure(path, False)
    while True:
        lengths.append(measure.getLength())
        if not measure.nextContour():
            break
    total = sum(lengths)
    result = s.Path()
    if total <= 0:
        return result
    for a, b in intervals(state.get("trim_start", 0), state["draw"], state.get("trim_offset", 0), closed):
        spans = (
            _on_spans(a * total, b * total, pattern, state.get("dash_offset", 0))
            if pattern
            else [(a * total, b * total)]
        )
        for lo, hi in spans:
            base = 0.0
            measure = s.PathMeasure(path, False)
            for length in lengths:
                s0, s1 = max(lo, base) - base, min(hi, base + length) - base
                if length > 0 and s1 > s0:
                    _append_segment(s, measure, s0, s1, result)
                base += length
                if base >= hi or not measure.nextContour():
                    break
    return result


def path_effect(s, c):
    """Skia path effects requested by a shape: round_corners, then jitter."""
    effect = None
    radius = getattr(c, "round_corners", 0)
    if radius:
        effect = s.CornerPathEffect.Make(radius)
    jitter = getattr(c, "jitter", None)
    if jitter:
        rough = s.DiscretePathEffect.Make(jitter[0], jitter[1], int(jitter[2]) if len(jitter) > 2 else 0)
        effect = rough if effect is None else s.PathEffect.MakeCompose(rough, effect)
    return effect


def draw_shape(s, canvas, c, state, opacity):
    from .._strokes import styled
    from ..layout import Bounds

    path, closed = shape_path(s, c, state)
    w, h = state["width"], state["height"]
    progress = state["draw"]
    box = Bounds(-w / 2, -h / 2, w / 2, h / 2)
    effect = path_effect(s, c)
    if closed and progress >= 1:
        p = paint(s, state["fill"], box, opacity)
        if effect is not None:
            p.setPathEffect(effect)
        canvas.drawPath(path, p)
    if state["stroke"][3] > 0 and state["stroke_width"] > 0 and styled(c, state):
        p = paint(s, state["stroke"], box, opacity)
        if effect is not None:
            p.setPathEffect(effect)
        p.setStyle(s.Paint.kStroke_Style)
        p.setStrokeWidth(state["stroke_width"])
        p.setStrokeJoin(s.Paint.kRound_Join)
        p.setStrokeCap(
            {"round": s.Paint.kRound_Cap, "square": s.Paint.kSquare_Cap}.get(
                getattr(c, "line_cap", "butt"), s.Paint.kButt_Cap
            )
        )
        canvas.drawPath(styled_path(s, path, state, closed, getattr(c, "dash", None)), p)
        if isinstance(c, Arrow) and progress > 0:
            tip, x = c.tip_size * min(1, progress / 0.15), -w / 2 + w * min(1, progress + state.get("trim_offset", 0))
            b = s.PathBuilder().moveTo(x, 0).lineTo(x - tip, -tip / 2).lineTo(x - tip, tip / 2).close()
            canvas.drawPath(b.detach(), paint(s, state["stroke"], box, opacity))
        return
    if state["stroke"][3] > 0 and state["stroke_width"] > 0 and progress > 0:
        p = paint(s, state["stroke"], box, opacity)
        if effect is not None:
            p.setPathEffect(effect)
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
