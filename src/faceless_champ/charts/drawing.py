"""Pillow chart sprites. Marks are clipped independently of labels and axes."""

import math
from functools import lru_cache
from itertools import pairwise

from PIL import Image, ImageDraw

from ..typography import load_font
from . import BarChart, Heatmap, Histogram, LineChart, NetworkGraph, PieChart, RankedBarChart, ScatterPlot, VectorField
from .scales import palette_color, project, sankey_geometry, separate_positions, ticks


@lru_cache(maxsize=64)
def _font(size, path=None, weight=None):
    return load_font(path, size, weight)


def _style_fonts(style, factor):
    return (
        _font(max(1, round(style.font_size * factor)), style.font, style.font_weight),
        _font(
            max(1, round(style.title_size * factor)),
            style.title_font or style.font,
            style.title_font_weight if style.title_font_weight is not None else style.font_weight,
        ),
    )


def draw_ranked_bars(c, state, factor):
    s = c.style
    width, height = max(1, round(c.width * factor)), max(1, round(c.height * factor))
    image = Image.new("RGBA", (width, height), s.scheme.surface)
    d = ImageDraw.Draw(image)
    font, title_font = _style_fonts(s, factor)
    fs = s.font_size * factor
    n = len(c.categories)
    values, ranks, availability = state["data"][:n], state["data"][n : 2 * n], state["data"][2 * n :]
    left = (24 + c.label_width) * factor
    right = width - (24 + c.value_width) * factor
    top = (64 if c.title else 24) * factor
    lower = height - (fs * 2.5 + (fs * 1.6 if c.x_axis.label else 0))
    row_height = (lower - top) / c.top_n
    if right <= left + 10 or row_height < fs * 1.5:
        raise ValueError("Ranked chart is too small for its labels; increase width/height or reduce font size")
    if c.title:
        d.text((24 * factor, 16 * factor), c.title, font=title_font, fill=s.scheme.text, anchor="lt")
    maximum = max((v for v, a in zip(values, availability) if a >= 1 - 1e-9), default=0)
    bounds = c.x_axis.limits or (0.0, max(maximum * 1.08, 1.0))
    for value in ticks(bounds, c.x_axis):
        x = left + project(value, bounds) * (right - left)
        if s.grid:
            d.line((x, top, x, lower), fill=s.scheme.grid, width=max(1, round(factor)))
        label = c.x_axis.format(value)
        d.text((x, lower + fs * 0.6), label, font=font, fill=s.scheme.muted, anchor="mt")
    progress = min(1, max(0, state["reveal"]))
    visible = [i for i in range(n) if ranks[i] < c.top_n]
    centers = [top + (ranks[i] + 0.5) * row_height for i in visible]
    label_positions = dict(zip(visible, separate_positions(centers, fs * 1.3, (top + fs / 2, lower - fs / 2))))
    # Draw in rank order for deterministic overlap during crossings. Category
    # colors stay tied to input identity, never to the current rank.
    for i in sorted(range(n), key=lambda i: (ranks[i], i), reverse=True):
        if ranks[i] >= c.top_n:
            continue
        y = top + (ranks[i] + 0.5) * row_height
        label_y = label_positions[i]
        name = c.categories[i]
        if d.textlength(name, font=font) > c.label_width * factor - fs * 1.2:
            raise ValueError("Ranked category label exceeds label_width")
        color = s.color(i)
        known = availability[i] >= 1 - 1e-9
        if c.show_markers:
            d.ellipse((24 * factor, label_y - fs / 6, 24 * factor + fs / 3, label_y + fs / 6), fill=color)
        d.text((left - 12 * factor, label_y), name, font=font, fill=s.scheme.text, anchor="rm")
        if abs(label_y - y) > factor:
            d.line((left - 8 * factor, label_y, left, min(lower, max(top, y))), fill=color, width=max(1, round(factor)))
        end = left + min(1, max(0, project(values[i], bounds))) * (right - left) * progress
        if known and end > left:
            bar_height = (
                min(row_height * 0.62, fs * 1.55) if c.bar_height is None else min(row_height, c.bar_height * factor)
            )
            y0, y1 = max(top, y - bar_height / 2), min(lower, y + bar_height / 2)
            if y1 > y0:
                d.rounded_rectangle(
                    (left, y0, end, y1),
                    radius=min(c.corner_radius * factor, (end - left) / 2, (y1 - y0) / 2),
                    fill=color,
                )
        label = str(c.value_formatter(values[i])) if known else c.missing_label
        if d.textlength(label, font=font) > c.value_width * factor:
            raise ValueError("Ranked value label exceeds value_width")
        d.text(
            (right + 12 * factor, label_y),
            label,
            font=font,
            fill=s.scheme.text if known else s.scheme.muted,
            anchor="lm",
        )
    if c.x_axis.label:
        d.text(((left + right) / 2, height - fs * 0.5), c.x_axis.label, font=font, fill=s.scheme.muted, anchor="mb")
    return image


def draw_chart(chart, state, factor):
    if isinstance(chart, RankedBarChart):
        return draw_ranked_bars(chart, state, factor)
    c, s = chart, chart.style
    width, height = max(1, round(c.width * factor)), max(1, round(c.height * factor))
    image = Image.new("RGBA", (width, height), s.scheme.surface)
    d = ImageDraw.Draw(image)
    font, title_font = _style_fonts(s, factor)
    fs = s.font_size * factor

    def text(x, y, value, *, anchor="mm", color=None, title=False):
        d.text((x, y), str(value), font=title_font if title else font, anchor=anchor, fill=color or s.scheme.text)

    if c.title:
        text(width / 2, 12 * factor, c.title, anchor="mt", title=True)
    names = getattr(c, "names", ())
    if isinstance(c, PieChart):
        names = c.categories
    legend_rows = []
    if names and s.legend:
        row, used = [], 0
        for i, name in enumerate(names):
            size = d.textlength(name, font=font) + 34 * factor
            if row and used + size > width - 24 * factor:
                legend_rows.append(row)
                row, used = [], 0
            row.append((i, name, size))
            used += size
        legend_rows.append(row)
    bottom = 30 * factor + len(legend_rows) * fs * 1.6
    for ri, row in enumerate(legend_rows):
        x = (width - sum(item[2] for item in row)) / 2
        y = height - (len(legend_rows) - ri) * fs * 1.6
        for i, name, size in row:
            d.rectangle((x, y - fs / 4, x + fs / 2, y + fs / 4), fill=s.color(i))
            text(x + fs, y, name, anchor="lm")
            x += size
    left, top, right = 24 * factor, (58 if c.title else 24) * factor, width - 24 * factor
    end_labels = isinstance(c, LineChart) and not isinstance(c, ScatterPlot) and c.end_labels
    if end_labels:
        right -= max(d.textlength(name, font=font) for name in c.names) + 20 * factor
    if c.cartesian:
        yt = ticks(c.y_bounds, c.y_axis)
        left += max((d.textlength(c.y_axis.format(v), font=font) for v in yt), default=0) + 12 * factor
        bottom += fs * 1.8
        if c.y_axis.label:
            top += fs * 1.7
        if c.x_axis.label:
            bottom += fs * 1.6
    elif isinstance(c, Heatmap):
        left += max(d.textlength(v, font=font) for v in c.row_labels) + 8 * factor
        bottom += fs * 1.7
        if c.colorbar:
            right -= 40 * factor + max(d.textlength(f"{v:g}", font=font) for v in c.color_bounds)
    lower = height - bottom
    if right <= left + 10 or lower <= top + 10:
        raise ValueError("Chart is too small for its labels; increase width/height or reduce font size")
    if isinstance(c, VectorField) and c.equal_units:
        ratio = min((right - left) / (c.x_bounds[1] - c.x_bounds[0]), (lower - top) / (c.y_bounds[1] - c.y_bounds[0]))
        w, h = ratio * (c.x_bounds[1] - c.x_bounds[0]), ratio * (c.y_bounds[1] - c.y_bounds[0])
        left, right = (left + right - w) / 2, (left + right + w) / 2
        top, lower = (top + lower - h) / 2, (top + lower + h) / 2
    pw, ph = right - left, lower - top

    def xp(v):
        return left + project(v, c.x_bounds, c.x_axis.scale) * pw

    def yp(v):
        return lower - project(v, c.y_bounds, c.y_axis.scale) * ph

    if c.cartesian:
        for v in ticks(c.y_bounds, c.y_axis):
            y = yp(v)
            if s.grid:
                d.line((left, y, right, y), fill=s.scheme.grid, width=max(1, round(factor)))
            text(left - 8 * factor, y, c.y_axis.format(v), anchor="rm")
        xt = (
            enumerate(c.categories)
            if isinstance(c, BarChart)
            else ((v, c.x_axis.format(v)) for v in ticks(c.x_bounds, c.x_axis))
        )
        last_end = -math.inf
        for v, label in xt:
            # Category axes are always linear; numeric x_axis settings apply to other charts.
            x = left + (v + 0.5) / len(c.categories) * pw if isinstance(c, BarChart) else xp(v)
            tw = d.textlength(label, font=font)
            if x - tw / 2 >= last_end + 6 * factor:
                text(x, lower + 10 * factor, label, anchor="mt")
                last_end = x + tw / 2
        d.line((left, top, left, lower, right, lower), fill=s.scheme.axis, width=max(1, round(factor)))
        if c.x_axis.label:
            text((left + right) / 2, lower + fs * 2.3, c.x_axis.label, anchor="mt")
        if c.y_axis.label:
            text(left, top - fs, c.y_axis.label, anchor="lb")

    marks = Image.new("RGBA", image.size)
    md = ImageDraw.Draw(marks)
    progress = min(1, max(0, state["reveal"]))
    values = state["data"]
    lw = max(1, round(s.line_width * factor))

    def arrow(a, b, color, line_width=lw):
        if a == b:
            return
        md.line((*a, *b), fill=color, width=line_width)
        angle = math.atan2(b[1] - a[1], b[0] - a[0])
        length = min(10 * factor, math.dist(a, b) * 0.4)
        md.polygon(
            [
                b,
                (b[0] - length * math.cos(angle - 0.45), b[1] - length * math.sin(angle - 0.45)),
                (b[0] - length * math.cos(angle + 0.45), b[1] - length * math.sin(angle + 0.45)),
            ],
            fill=color,
        )

    if isinstance(c, BarChart):
        n, groups = len(c.categories), len(c.names)
        positive, negative = [0.0] * n, [0.0] * n
        for j in range(groups):
            for i in range(n):
                v = values[j * n + i]
                base = c.y_bounds[0] if c.y_axis.scale == "log" else 0
                if c.stacked:
                    stack = positive if v >= 0 else negative
                    base = stack[i]
                    stack[i] += v
                target = base + v if c.stacked else v
                y0, y1 = yp(base), yp(target)
                y1 = y0 + (y1 - y0) * progress
                slots = 1 if c.stacked else groups
                bw = pw / n * 0.8 / slots
                x = left + (i + 0.1) * pw / n + (0 if c.stacked else j * bw)
                if progress:
                    md.rectangle((x, min(y0, y1), x + bw * 0.94, max(y0, y1)), fill=s.color(j))
    elif isinstance(c, Histogram):
        for i, v in enumerate(values):
            x0, x1 = xp(c.edges[i]), xp(c.edges[i + 1])
            if progress:
                md.rectangle((x0, yp(v * progress), max(x0, x1 - factor), yp(0)), fill=s.color(0))
    elif isinstance(c, LineChart):
        offset, point_index = 0, 0
        for j, count in enumerate(c.lengths):
            points = [(xp(values[k]), yp(values[k + 1])) for k in range(offset, offset + count * 2, 2)]
            offset += count * 2
            if isinstance(c, ScatterPlot):
                for x, y in points:
                    radius = c.sizes[point_index] * factor * progress
                    point_index += 1
                    if radius:
                        md.ellipse((x - radius, y - radius, x + radius, y + radius), fill=s.color(j))
            else:
                lengths = [math.dist(a, b) for a, b in pairwise(points)]
                remaining = sum(lengths) * progress
                for a, b, length in zip(points, points[1:], lengths):
                    fraction = min(1, remaining / length) if length else 1
                    if remaining <= 0:
                        break
                    end = tuple(x + (y - x) * fraction for x, y in zip(a, b))
                    md.line((*a, *end), fill=s.color(j), width=lw)
                    remaining -= length
                if len(points) == 1 and progress:
                    x, y = points[0]
                    md.ellipse((x - lw, y - lw, x + lw, y + lw), fill=s.color(j))
    elif isinstance(c, Heatmap):

        def color(v):
            return palette_color(v, c.color_bounds, c.palette)

        for row in range(c.rows):
            for col in range(c.columns):
                rgba = color(values[row * c.columns + col])
                md.rectangle(
                    (
                        left + col * pw / c.columns,
                        top + row * ph / c.rows,
                        left + (col + 1) * pw / c.columns,
                        top + (row + 1) * ph / c.rows,
                    ),
                    fill=(*rgba[:3], round(rgba[3] * progress)),
                )
        for i, label in enumerate(c.row_labels):
            text(left - 8 * factor, top + (i + 0.5) * ph / c.rows, label, anchor="rm")
        last_end = -math.inf
        for i, label in enumerate(c.column_labels):
            x = left + (i + 0.5) * pw / c.columns
            tw = d.textlength(label, font=font)
            if x - tw / 2 > last_end:
                text(x, lower + 10 * factor, label, anchor="mt")
                last_end = x + tw / 2 + 6 * factor
        if c.colorbar:
            for y in range(round(top), round(lower)):
                v = c.color_bounds[1] - (y - top) / ph * (c.color_bounds[1] - c.color_bounds[0])
                d.line((right + 15 * factor, y, right + 28 * factor, y), fill=color(v))
            for v in c.color_bounds:
                y = lower - project(v, c.color_bounds) * ph
                text(right + 34 * factor, y, f"{v:g}", anchor="lm")
    elif isinstance(c, VectorField):
        for i in range(0, len(values), 4):
            x, y, dx, dy = values[i : i + 4]
            arrow(
                (xp(x), yp(y)),
                (xp(x + dx * c.vector_scale * progress), yp(y + dy * c.vector_scale * progress)),
                s.color(0),
            )
    elif isinstance(c, NetworkGraph):
        positions = {n: (left + x * pw, top + y * ph) for n, (x, y) in zip(c.nodes, c.positions)}
        if c.flow:
            heights, ribbons = sankey_geometry(c.nodes, c.edges, values, positions, ph)
            for (a, b), (y0, y1, thickness) in zip(c.edges, ribbons):
                x0, x1 = positions[a][0] + 5 * factor, positions[b][0] - 5 * factor
                if thickness and progress:
                    upper, lower_edge = [], []
                    for step in range(31):
                        t = progress * step / 30
                        u = t * t * (3 - 2 * t)
                        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * u
                        upper.append((x, y))
                        lower_edge.append((x, y + thickness))
                    md.polygon(upper + lower_edge[::-1], fill=s.color(c.nodes.index(a)))
            for i, n in enumerate(c.nodes):
                x, y = positions[n]
                h = max(2 * factor, heights[n])
                md.rectangle((x - 5 * factor, y - h / 2, x + 5 * factor, y + h / 2), fill=s.color(i))
                text(x, y + h / 2 + fs * 0.6, n, anchor="mt")
        else:
            for (a, b), v in zip(c.edges, values):
                start, target = positions[a], positions[b]
                distance = math.dist(start, target)
                fraction = max(0, 1 - 9 * factor / distance) if distance else 0
                end = tuple(x + (y - x) * fraction * progress for x, y in zip(start, target))
                if v and progress:
                    line_width = max(1, round(min(v, 12) * factor))
                    if c.directed:
                        arrow(start, end, s.scheme.muted, line_width)
                    else:
                        md.line((*start, *end), fill=s.scheme.muted, width=line_width)
            for i, n in enumerate(c.nodes):
                x, y = positions[n]
                r = 8 * factor
                md.ellipse((x - r, y - r, x + r, y + r), fill=s.color(i))
                text(x, y + r + 5 * factor, n, anchor="mt")
    elif isinstance(c, PieChart):
        radius = min(pw, ph) / 2
        cx, cy = (left + right) / 2, (top + lower) / 2
        box = (cx - radius, cy - radius, cx + radius, cy + radius)
        start = -90
        for i, v in enumerate(values):
            end = start + v / sum(values) * 360
            shown = min(end, -90 + progress * 360)
            if shown > start:
                md.pieslice(box, start, shown, fill=s.color(i))
            start = end
        if c.hole:
            r = radius * c.hole
            md.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(0, 0, 0, 0))
    # Clip marks only; tick labels, legends, titles and node labels stay outside the plot.
    crop = (math.ceil(left), math.ceil(top), math.floor(right) + 1, math.floor(lower) + 1)
    image.alpha_composite(marks.crop(crop), crop[:2])
    if end_labels and progress >= 1 - 1e-9:
        endpoints, offset = [], 0
        for count in c.lengths:
            offset += count * 2
            endpoints.append((xp(values[offset - 2]), yp(values[offset - 1])))
        positions = separate_positions([y for _, y in endpoints], fs * 1.3, (top + fs / 2, lower - fs / 2))
        for i, (y, (end_x, end_y)) in enumerate(zip(positions, endpoints)):
            end_x, end_y = min(right, max(left, end_x)), min(lower, max(top, end_y))
            if abs(y - end_y) > factor or end_x < right - factor:
                d.line((end_x, end_y, right + 6 * factor, y), fill=s.color(i), width=max(1, round(factor)))
            text(right + 10 * factor, y, c.names[i], anchor="lm", color=s.color(i))
    return image
