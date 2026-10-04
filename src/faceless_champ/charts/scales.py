"""Validated axes and pure numeric chart geometry."""

import math
from bisect import bisect_right
from collections.abc import Callable
from dataclasses import dataclass

from ..components import finite


@dataclass(frozen=True)
class Axis:
    scale: str = "linear"
    limits: tuple[float, float] | None = None
    ticks: tuple[float, ...] | None = None
    label: str = ""
    unit: str = ""
    formatter: Callable[[float], str] | None = None

    def __post_init__(self):
        if self.scale not in {"linear", "log"}:
            raise ValueError("Axis scale must be linear or log")
        if self.limits is not None:
            values = tuple(finite(v, "axis limit") for v in self.limits)
            if len(values) != 2 or values[0] >= values[1]:
                raise ValueError("Axis limits must be increasing")
            object.__setattr__(self, "limits", values)
        if self.ticks is not None:
            object.__setattr__(self, "ticks", tuple(finite(v, "tick") for v in self.ticks))
        if self.scale == "log" and any(v <= 0 for v in (*(self.limits or ()), *(self.ticks or ()))):
            raise ValueError("Log axes require positive values")
        if self.formatter is not None and not callable(self.formatter):
            raise TypeError("formatter must be callable")

    def format(self, value):
        return str(self.formatter(value)) if self.formatter else f"{value:g}{self.unit}"


def domain(values, axis, *, zero=False):
    values = tuple(values)
    if axis.scale == "log" and any(v <= 0 for v in values):
        raise ValueError("Log axes require positive data")
    if axis.limits:
        return axis.limits
    lo, hi = min(values), max(values)
    if zero and axis.scale == "linear":
        lo, hi = min(0, lo), max(0, hi)
    if lo == hi:
        if axis.scale == "log":
            return lo / 10, hi * 10
        delta = abs(lo) * 0.1 or 1
        return lo - delta, hi + delta
    return lo, hi


def project(value, bounds, scale="linear"):
    lo, hi = bounds
    if scale == "log":
        value, lo, hi = math.log10(value), math.log10(lo), math.log10(hi)
    return (value - lo) / (hi - lo)


def ticks(bounds, axis):
    lo, hi = bounds
    if axis.ticks is not None:
        return tuple(v for v in axis.ticks if lo <= v <= hi)
    if axis.scale == "log":
        result = tuple(10.0**i for i in range(math.ceil(math.log10(lo)), math.floor(math.log10(hi)) + 1))
        return result or (lo, hi)
    raw = (hi - lo) / 5
    power = 10 ** math.floor(math.log10(raw))
    step = next(n for n in (1, 2, 2.5, 5, 10) if n * power >= raw) * power
    return tuple(
        0.0 if abs(i * step) < step * 1e-10 else i * step
        for i in range(math.ceil(lo / step), math.floor(hi / step) + 1)
    )


def histogram(samples, edges):
    counts = [0.0] * (len(edges) - 1)
    for value in samples:
        if edges[0] <= value <= edges[-1]:
            index = min(len(counts) - 1, bisect_right(edges, value) - 1)
            counts[index] += 1
    return tuple(counts)


def graph_positions(nodes, edges, *, flow=False):
    if not flow:
        return tuple(
            (0.5 + 0.38 * math.cos(i * math.tau / len(nodes)), 0.5 + 0.38 * math.sin(i * math.tau / len(nodes)))
            for i in range(len(nodes))
        )
    levels = dict.fromkeys(nodes, 0)
    pending = set(nodes)
    while pending:
        ready = [n for n in nodes if n in pending and not any(b == n and a in pending for a, b in edges)]
        if not ready:
            raise ValueError("Sankey links must be acyclic")
        for n in ready:
            levels[n] = max((levels[a] + 1 for a, b in edges if b == n), default=0)
            pending.remove(n)
    maximum = max(levels.values()) or 1
    groups = {level: [n for n in nodes if levels[n] == level] for level in set(levels.values())}
    return tuple(
        (0.06 + 0.88 * levels[n] / maximum, (groups[levels[n]].index(n) + 1) / (len(groups[levels[n]]) + 1))
        for n in nodes
    )


def sankey_geometry(nodes, edges, weights, positions, height):
    """Return node heights and ribbon top offsets using one global weight scale."""
    incoming, outgoing = dict.fromkeys(nodes, 0.0), dict.fromkeys(nodes, 0.0)
    for (a, b), value in zip(edges, weights):
        outgoing[a] += value
        incoming[b] += value
    totals = {n: max(incoming[n], outgoing[n]) for n in nodes}
    scale = height * 0.65 / (sum(totals.values()) or 1)
    heights = {n: totals[n] * scale for n in nodes}
    starts = {n: positions[n][1] - heights[n] / 2 for n in nodes}
    ins, outs = starts.copy(), starts.copy()
    ribbons = []
    for (a, b), value in zip(edges, weights):
        thickness = value * scale
        ribbons.append((outs[a], ins[b], thickness))
        outs[a] += thickness
        ins[b] += thickness
    return heights, tuple(ribbons)


def palette_color(value, bounds, palette):
    """Clamp and interpolate RGBA palette stops using a fixed numeric domain."""
    p = min(1, max(0, project(value, bounds))) * (len(palette) - 1)
    index = min(len(palette) - 2, int(p))
    return tuple(round(a + (b - a) * (p - index)) for a, b in zip(palette[index], palette[index + 1]))
