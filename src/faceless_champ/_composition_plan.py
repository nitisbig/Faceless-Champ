"""Pure composition timing and integer viewport allocation, shared by all engines."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Placement:
    node: object
    time: float
    viewport: tuple
    background: str


def fit(canvas, size):
    ratio = min(size[0] / canvas.width, size[1] / canvas.height)
    fitted = max(1, round(canvas.width * ratio)), max(1, round(canvas.height * ratio))
    return fitted, ((size[0] - fitted[0]) // 2, (size[1] - fitted[1]) // 2)


def composition_plan(node, time, size):
    from .timeline import Grid, Layer, Sequence

    full = (0, 0, *size)
    if isinstance(node, Sequence):
        starts = node.starts
        active = [i for i, (s, c) in enumerate(zip(starts, node.children)) if s <= time < s + c.duration]
        if not active and time >= node.duration:
            active = [len(node.children) - 1]
        parts = tuple(Placement(node.children[i], time - starts[i], full, node.canvas.bg) for i in active)
        progress = min(1, (time - starts[active[1]]) / node.crossfade) if len(active) == 2 else None
        return parts, progress
    if isinstance(node, Grid):
        sx, sy = size[0] / node.canvas.width, size[1] / node.canvas.height
        top, right_pad, bottom_pad, left = node.padding
        cw = (node.canvas.width - left - right_pad - node.gap * (node.columns - 1)) / node.columns
        ch = (node.canvas.height - top - bottom_pad - node.gap * (node.rows - 1)) / node.rows
        parts = []
        for i, (start, child) in enumerate(zip(node.start_times, node.children)):
            if time < start:
                continue
            col, row = i % node.columns, i // node.columns
            x, y = round((left + col * (cw + node.gap)) * sx), round((top + row * (ch + node.gap)) * sy)
            r, b = round((left + col * (cw + node.gap) + cw) * sx), round((top + row * (ch + node.gap) + ch) * sy)
            parts.append(
                Placement(
                    child, min(time - start, child.duration), (x, y, max(1, r - x), max(1, b - y)), node.canvas.bg
                )
            )
        return tuple(parts), None
    if isinstance(node, Layer):
        return tuple(Placement(c, min(time, c.duration), full, "#00000000") for c in node.children), None
    raise TypeError(f"Unsupported renderable: {type(node).__name__}")
