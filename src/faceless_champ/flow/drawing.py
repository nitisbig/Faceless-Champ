"""Pillow rasterization of shared vector paths, labels and transient overlays."""

import math
import random
from itertools import pairwise

from PIL import Image, ImageColor, ImageDraw

from ..typography import load_font
from .geometry import length, prefix, sample, transform
from .model import FlowDataError

CARD_SYMBOLS = {"rectangle", "rounded_rectangle", "circle", "diamond", "document", "service"}


def prepare_labels(clip):
    labels = {}
    for item in (*clip.graph.nodes, *clip.graph.edges):
        if not item.label:
            continue
        node = item.id in clip._nodes
        width = item.size[0] * (0.58 if item.symbol == "diamond" else 0.8) if node else 180
        height = item.size[1] * 0.7 if node and item.symbol in CARD_SYMBOLS else max(48, clip.theme.font_size * 2.5)
        for size in range(math.floor(clip.theme.font_size), math.ceil(clip.theme.minimum_font_size) - 1, -1):
            font = load_font(clip.theme.font, size)
            lines = []
            for paragraph in item.label.split("\n"):
                line = ""
                for word in paragraph.split():
                    candidate = f"{line} {word}".strip()
                    if font.getlength(candidate) > width and line:
                        lines.append(line)
                        line = word
                    else:
                        line = candidate
                lines.append(line)
            if max((font.getlength(line) for line in lines), default=0) <= width and len(lines) * size * 1.25 <= height:
                labels[item.id] = ("\n".join(lines), size)
                break
        else:
            raise FlowDataError(item.id, "label cannot fit; enlarge node or shorten label")
    return labels


def rgba(color, opacity=1):
    r, g, b, a = ImageColor.getcolor(color, "RGBA")
    return r, g, b, round(a * opacity)


def stroke(draw, points, fill, width, dashed=False):
    if len(points) < 2:
        return
    if not dashed:
        draw.line(points, fill=fill, width=width, joint="curve")
        return
    # Carry phase across bends so dashes and reveals share one length coordinate.
    phase = 0.0
    dash = max(3, width * 3)
    for a, b in pairwise(points):
        span = math.dist(a, b)
        offset = 0.0
        while offset < span - 1e-9:
            step = min(span - offset, dash - phase % dash)
            if int(phase / dash) % 2 == 0:
                p = (a[0] + (b[0] - a[0]) * offset / span, a[1] + (b[1] - a[1]) * offset / span)
                q = (a[0] + (b[0] - a[0]) * (offset + step) / span, a[1] + (b[1] - a[1]) * (offset + step) / span)
                draw.line((p, q), fill=fill, width=width)
            phase += step + 1e-10
            offset += step


def label_image(clip, id, factor, color):
    label, size = clip._labels[id]
    font_size = max(1, round(size * factor))
    spacing = max(1, round(size * 0.25 * factor))
    key = (id, font_size, spacing, color)
    cached = clip._label_cache.get(key)
    if cached is not None:
        clip._label_cache.move_to_end(key)
        return cached.copy()
    font = load_font(clip.theme.font, font_size)
    draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    box = draw.multiline_textbbox((0, 0), label, font=font, spacing=spacing, align="center")
    image = Image.new("RGBA", (max(1, math.ceil(box[2] - box[0]) + 4), max(1, math.ceil(box[3] - box[1]) + 4)))
    ImageDraw.Draw(image).multiline_text(
        (2 - box[0], 2 - box[1]), label, font=font, fill=color, spacing=spacing, align="center"
    )
    cost = image.width * image.height * 4
    if cost <= clip._label_cache_limit:
        while clip._label_cache and clip._label_cache_bytes + cost > clip._label_cache_limit:
            _, old = clip._label_cache.popitem(last=False)
            clip._label_cache_bytes -= old.width * old.height * 4
        clip._label_cache[key] = image.copy()
        clip._label_cache_bytes += cost
    return image


def composite_center(layer, sprite, position, origin=(0, 0)):
    layer.alpha_composite(
        sprite,
        (round(position[0] - sprite.width / 2) - origin[0], round(position[1] - sprite.height / 2) - origin[1]),
    )


def raster_label(clip, id, state, factor):
    """Return the actual raster and center, including fixed pixel padding and font rounding."""
    node = id in clip._nodes
    sprite = label_image(clip, id, factor * (state["scale"] if node else 1), rgba(clip.theme.foreground))
    if not node or clip._nodes[id].symbol not in CARD_SYMBOLS:
        backing = Image.new("RGBA", (sprite.width + 8, sprite.height + 4), clip.theme.background)
        backing.alpha_composite(sprite, (4, 2))
        sprite = backing
    if node:
        item = clip._nodes[id]
        local = (0, 0) if item.symbol in CARD_SYMBOLS else (0, item.size[1] / 2 + clip._labels[id][1] * 0.9 + 6)
        position = transform(local, state)
        sprite = sprite.rotate(-state["rotation"], expand=True, resample=Image.Resampling.BICUBIC)
    else:
        edge = clip._edges[id]
        anchor = sample(state["path"], edge.label_position)
        position = tuple(a + offset for a, offset in zip(anchor, edge.label_offset))
    sprite.putalpha(sprite.getchannel("A").point(lambda a: round(a * state["draw"])))
    return sprite, tuple(x * factor for x in position)


def draw_frame(clip, snapshot, factor):
    size = (max(1, round(clip.width * factor)), max(1, round(clip.height * factor)))
    canvas = Image.new("RGBA", size, clip.theme.background)
    states = snapshot["elements"]
    width = max(1, round(clip.theme.stroke_width * factor))
    for item in (*clip.graph.edges, *clip.graph.nodes):
        id, s = item.id, states[item.id]
        opacity = s["opacity"]
        for h in snapshot["highlights"]:
            if id not in h["targets"]:
                opacity *= h["dim"]
        if opacity <= 0:
            continue
        node = id in clip._nodes
        paths = clip.paths_for(id, states)
        # Integer origins preserve rasterization while avoiding viewport-sized element layers.
        bounds = clip._bounds_for(id, states, labels=False)
        pad = math.ceil((clip.theme.stroke_width + 4) * factor) + 4
        left = max(0, math.floor(bounds.left * factor) - pad)
        top = max(0, math.floor(bounds.top * factor) - pad)
        right = min(size[0], math.ceil(bounds.right * factor) + pad)
        bottom = min(size[1], math.ceil(bounds.bottom * factor) + pad)
        label = raster_label(clip, id, s, factor) if id in clip._labels else None
        if label is not None:
            sprite, position = label
            x, y = round(position[0] - sprite.width / 2), round(position[1] - sprite.height / 2)
            left, top = max(0, min(left, x)), max(0, min(top, y))
            right, bottom = min(size[0], max(right, x + sprite.width)), min(size[1], max(bottom, y + sprite.height))
        if right <= left or bottom <= top:
            continue
        layer = Image.new("RGBA", (right - left, bottom - top))
        draw = ImageDraw.Draw(layer)

        def raster_point(point, left=left, top=top):
            return point[0] * factor - left, point[1] * factor - top

        total = sum(length(path) for path in paths)
        remaining = total * s["draw"]
        highlighted = [h for h in snapshot["highlights"] if id in h["targets"]]
        outline = highlighted[-1]["color"] if highlighted else (clip.theme.stroke or clip.theme.accent)
        sw = width + (max(1, round(2 * factor)) if highlighted else 0)
        rng = random.Random(f"{clip.theme.seed}:{id}")
        if node and (item.symbol in CARD_SYMBOLS or item.symbol == "junction") and s["draw"] >= 1:
            fill = outline if item.symbol == "junction" else clip.theme.surface
            if highlighted and highlighted[-1]["mode"] == "tint":
                fill = highlighted[-1]["color"]
            draw.polygon([raster_point(p) for p in paths[0]], fill=rgba(fill, 0.35 if highlighted else 1))
        for path in paths:
            if remaining <= 0:
                break
            span = length(path)
            progress = max(0, min(1, remaining / span)) if span else 0
            remaining -= span
            visible = prefix(path, progress)
            scaled = [raster_point(p) for p in visible]
            stroke(draw, scaled, rgba(outline), sw, False if node else item.dashed)
            if clip.theme.sketch:
                # Secondary texture cannot move the authoritative path or pencil tip.
                jittered = [(x + rng.uniform(-1, 1) * factor, y + rng.uniform(-1, 1) * factor) for x, y in scaled]
                stroke(draw, jittered, rgba(outline, 0.3), max(1, width // 2), False if node else item.dashed)
        if not node and s["draw"] > 0:
            path = paths[0]
            for end, enabled in ((False, item.arrows in {"start", "both"}), (True, item.arrows in {"end", "both"})):
                if not enabled or (end and s["draw"] < 1):
                    continue
                tip, previous = (path[-1], sample(path, 0.98)) if end else (path[0], sample(path, 0.02))
                angle = math.atan2(tip[1] - previous[1], tip[0] - previous[0])
                corners = [
                    tip,
                    *[(tip[0] - 12 * math.cos(angle + a), tip[1] - 12 * math.sin(angle + a)) for a in (-0.45, 0.45)],
                ]
                draw.polygon([raster_point(p) for p in corners], fill=rgba(outline))
        if node and id in clip._images:
            sprite = clip._images[id].copy()
            ratio = min(item.size[0] / sprite.width, item.size[1] / sprite.height) * s["scale"] * factor
            sprite = sprite.resize(
                (max(1, round(sprite.width * ratio)), max(1, round(sprite.height * ratio))), Image.Resampling.LANCZOS
            )
            sprite = sprite.rotate(-s["rotation"], expand=True, resample=Image.Resampling.BICUBIC)
            sprite.putalpha(sprite.getchannel("A").point(lambda a, progress=s["draw"]: round(a * progress)))
            composite_center(layer, sprite, tuple(x * factor for x in s["position"]), (left, top))
        if label is not None:
            sprite, position = label
            composite_center(layer, sprite, position, (left, top))
        layer.putalpha(layer.getchannel("A").point(lambda a, alpha=opacity: round(a * alpha)))
        canvas.alpha_composite(layer, (left, top))
    draw = ImageDraw.Draw(canvas)
    for signal in snapshot["signals"]:
        x, y = (v * factor for v in signal["position"])
        r = 6 * factor
        fill = rgba(signal["color"], signal["opacity"])
        if signal["marker"] == "packet":
            draw.rounded_rectangle((x - r * 1.4, y - r, x + r * 1.4, y + r), radius=2 * factor, fill=fill)
        else:
            draw.ellipse((x - r, y - r, x + r, y + r), fill=fill)
    for tool in snapshot["tools"]:
        x, y = (v * factor for v in tool["position"])
        fill = "#F8CA54" if tool["tool"] == "pencil" else clip.theme.foreground
        draw.polygon([(x, y), (x + 7 * factor, y - 20 * factor), (x + 13 * factor, y - 14 * factor)], fill=fill)
        draw.line(
            [(x, y), (x + 3 * factor, y - 7 * factor)], fill=clip.theme.foreground, width=max(1, round(2 * factor))
        )
    return canvas
