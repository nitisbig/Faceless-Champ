"""Portable trim-path and dash geometry over flattened polylines (Pillow paths).

The Skia backend implements the same contract natively with PathMeasure and
DashPathEffect: lengths are measured along the whole path, the visible span is
[trim_start, draw] shifted by trim_offset (wrapping on closed paths, clamped on
open ones), and dashes are anchored to the path start, so trimming never makes
the dash pattern swim.
"""

import math
from itertools import pairwise


def styled(c, state):
    """True when trim start/offset or dashes change the plain draw-progress stroke."""
    return bool(state.get("trim_start", 0) or state.get("trim_offset", 0) or getattr(c, "dash", None))


def intervals(start, end, offset, closed):
    """Visible spans as fractions of total length."""
    span = end - start
    if span <= 0:
        return []
    if closed:
        if span >= 1:
            return [(0.0, 1.0)]
        a = (start + offset) % 1.0
        b = a + span
        return [(a, b)] if b <= 1 else [(a, 1.0), (0.0, b - 1.0)]
    a, b = max(0.0, start + offset), min(1.0, end + offset)
    return [(a, b)] if b > a else []


def _lengths(contours):
    return [[math.dist(a, b) for a, b in pairwise(points)] for points in contours]


def trim(contours, start, end, offset, closed):
    """Return [(polyline, distance_of_its_first_point_from_path_start)]."""
    lengths = _lengths(contours)
    total = sum(sum(ls) for ls in lengths)
    if total <= 0:
        return []
    result = []
    for a, b in intervals(start, end, offset, closed):
        lo, hi = a * total, b * total
        base = 0.0
        for points, ls in zip(contours, lengths):
            length = sum(ls)
            if base + length <= lo or base >= hi:
                base += length
                continue
            line, cursor, first = [], base, None
            for (p, q), seg in zip(pairwise(points), ls):
                s0, s1 = max(lo, cursor), min(hi, cursor + seg)
                if seg > 0 and s1 > s0:
                    u0, u1 = (s0 - cursor) / seg, (s1 - cursor) / seg
                    start_point = (p[0] + (q[0] - p[0]) * u0, p[1] + (q[1] - p[1]) * u0)
                    if not line:
                        line.append(start_point)
                        first = s0
                    line.append((p[0] + (q[0] - p[0]) * u1, p[1] + (q[1] - p[1]) * u1))
                cursor += seg
            if len(line) > 1:
                result.append((line, first))
            base += length
    return result


def dash(pieces, pattern, phase):
    """Split polylines into dashes; phase and distances are in the same units as points."""
    pattern = [max(v, 1e-3) for v in pattern]  # zero-length "on" dashes become dots with round caps
    period = sum(pattern)
    out = []
    for points, origin in pieces:
        cursor = origin
        current = [points[0]]
        position = (origin + phase) % period
        index, remaining = 0, pattern[0]
        while position >= remaining:
            position -= remaining
            index = (index + 1) % len(pattern)
            remaining = pattern[index]
        remaining -= position
        on = index % 2 == 0
        for p, q in pairwise(points):
            seg = math.dist(p, q)
            done = 0.0
            while seg - done > remaining:
                done += remaining
                u = done / seg
                point = (p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u)
                if on:
                    current.append(point)
                    if len(current) > 1:
                        out.append(current)
                current = [point]
                index = (index + 1) % len(pattern)
                remaining, on = pattern[index], index % 2 == 0
            remaining -= seg - done
            if on:
                current.append(q)
            else:
                current = [q]
            cursor += seg
        if on and len(current) > 1:
            out.append(current)
    return [line for line in out if len(line) > 1]


def stroke_lines(contours, state, closed, dash_pattern=None, scale=1.0):
    """Visible stroke polylines for the full trim + dash contract."""
    pieces = trim(contours, state.get("trim_start", 0), state["draw"], state.get("trim_offset", 0), closed)
    if dash_pattern:
        return dash(pieces, [v * scale for v in dash_pattern], state.get("dash_offset", 0) * scale)
    return [line for line, _ in pieces]
