"""Procedural 1D -> 4D hypercube renderer used through ``FunctionSource``.

One function, ``draw(t, size)``, returns a transparent RGBA frame for source time ``t``.
Geometry lives in R^4 the whole time; a dimension that has not been "extruded" yet is
simply squashed to zero, so the point, segment, square, cube and tesseract are the same
16 vertices and 32 edges at different stages.
"""

from __future__ import annotations

import itertools
import math

import numpy as np
import skia
from sample_frames import FRAME_SIZE, load_frames

# Source-clock beats shared with render.py.
EXTRUDE = ((0.6, 2.6), (3.4, 5.4), (6.4, 8.6), (9.6, 11.8))  # x, y, z, w
SPIN_3D_START = 6.4
SPIN_4D_START = 11.0
SLICES_START = 11.6
PULSE = (24.0, 32.0)
CLIP_FPS = 12
SLICE_COUNT = 7

AXIS_COLORS = ("#FF5A4E", "#FF9F3D", "#FFD17E", "#5FB6FF")  # x, y, z, w
VERTEX = "#FFF3DE"
D4, D3 = 4.2, 6.5  # 4D->3D and 3D->2D camera distances

VERTICES = np.array(list(itertools.product((-1, 1), repeat=4)), dtype=float)
EDGES = [
    (i, j, int(np.flatnonzero(VERTICES[i] != VERTICES[j])[0]))
    for i, j in itertools.combinations(range(16), 2)
    if np.count_nonzero(VERTICES[i] != VERTICES[j]) == 1
]


def smooth(a: float, b: float, t: float) -> float:
    k = min(1.0, max(0.0, (t - a) / (b - a)))
    return k * k * (3 - 2 * k)


def theta_zw(t: float) -> float:
    """ZW-plane rotation angle (radians); the scene's live theta readout uses this too.

    Rotating z into w (not x) keeps the x-y video slices facing the camera while the
    inner and outer cubes swap places, the classic tesseract "inside-out" flow.
    """
    if t <= SPIN_4D_START:
        return 0.0
    ramp = smooth(SPIN_4D_START, SPIN_4D_START + 2.5, t)
    return 0.42 * (t - SPIN_4D_START) * ramp


def _extents(t: float) -> np.ndarray:
    return np.array([smooth(a, b, t) for a, b in EXTRUDE])


def _rot(n: int, i: int, j: int, a: float) -> np.ndarray:
    m = np.eye(n)
    c, s = math.cos(a), math.sin(a)
    m[i, i], m[i, j], m[j, i], m[j, j] = c, -s, s, c
    return m


def project(points4: np.ndarray, t: float, unit: float, center: tuple[float, float]):
    """R^4 points -> (screen xy, depth, 4D perspective factor)."""
    p = points4 @ _rot(4, 2, 3, theta_zw(t)).T
    f4 = D4 / (D4 - p[:, 3])
    p3 = p[:, :3] * f4[:, None]
    ease = smooth(SPIN_3D_START, SPIN_3D_START + 2, t)
    yaw = ease * (0.5 + 0.45 * math.sin(0.55 * max(0.0, t - SPIN_3D_START)))  # sway, never edge-on
    tilt = 0.38 * ease
    p3 = p3 @ _rot(3, 0, 2, yaw).T
    p3 = p3 @ _rot(3, 1, 2, -tilt).T
    f3 = D3 / (D3 - p3[:, 2])
    xy = np.stack([center[0] + unit * p3[:, 0] * f3, center[1] - unit * p3[:, 1] * f3], axis=1)
    return xy, p3[:, 2], f4


def _color(hex_color: str, alpha: float) -> int:
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return skia.ColorSetARGB(int(255 * max(0.0, min(1.0, alpha))), r, g, b)


_FRAME_IMAGES: list[skia.Image] = []


def _frames() -> list[skia.Image]:
    if not _FRAME_IMAGES:
        _FRAME_IMAGES.extend(skia.Image.fromarray(np.asarray(f)) for f in load_frames())
    return _FRAME_IMAGES


def _draw_slices(canvas: skia.Canvas, t: float, ext: np.ndarray, unit: float, center) -> None:
    """Video frames stacked along w: the newest frame sits on the outer cube, older ones trail inward."""
    show = smooth(SLICES_START, SLICES_START + 0.8, t)
    if show <= 0:
        return
    frames = _frames()
    tick = int((t - SLICES_START) * CLIP_FPS)
    sx, sy = 1.0, FRAME_SIZE[1] / FRAME_SIZE[0]
    quads = []
    for k in range(SLICE_COUNT):
        # Slices appear one by one while the clip starts, then all play.
        born = SLICES_START + 0.18 * k
        a = smooth(born, born + 0.35, t) * show
        if a <= 0:
            continue
        w = (-1 + 2 * k / (SLICE_COUNT - 1)) * ext[3]
        corners = np.array([[-sx, sy, 0, w], [sx, sy, 0, w], [sx, -sy, 0, w], [-sx, -sy, 0, w]]) * [
            ext[0],
            ext[1],
            1,
            1,
        ]
        xy, depth, _ = project(corners, t, unit, center)
        age = SLICE_COUNT - 1 - k
        frame = frames[max(0, tick - age * 2) % len(frames)]
        quads.append((depth.mean(), xy, frame, a * (1.0 if age == 0 else 0.42 - 0.05 * age), age == 0))
    for _, xy, frame, alpha, newest in sorted(quads, key=lambda q: (q[4], q[0])):
        matrix = skia.Matrix()
        fw, fh = frame.width(), frame.height()
        src = [skia.Point(0, 0), skia.Point(fw, 0), skia.Point(fw, fh), skia.Point(0, fh)]
        dst = [skia.Point(float(x), float(y)) for x, y in xy]
        if not matrix.setPolyToPoly(src, dst):
            continue
        canvas.save()
        canvas.concat(matrix)
        paint = skia.Paint(AntiAlias=True, Alpha=int(255 * alpha))
        canvas.drawImageRect(frame, skia.Rect(0, 0, fw, fh), skia.SamplingOptions(skia.FilterMode.kLinear), paint)
        canvas.restore()
        border = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3 if newest else 1.5)
        border.setColor(_color(AXIS_COLORS[3], alpha * (1.0 if newest else 0.7)))
        path = skia.Path()
        path.addPoly(dst, True)
        canvas.drawPath(path, border)


def draw(t: float, size: tuple[int, int]) -> np.ndarray:
    w, h = size
    unit = h * 0.185
    center = (w / 2, h * 0.5)
    surface = skia.Surface(w, h)
    canvas = surface.getCanvas()
    canvas.clear(skia.ColorTRANSPARENT)
    ext = _extents(t)
    # A point exists from the start; it "pops" in.
    pop = smooth(0.0, 0.5, t)
    xy, depth, f4 = project(VERTICES * ext, t, unit, center)
    scale = h / 1080
    _draw_slices(canvas, t, ext, unit, center)

    glow = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeCap=skia.Paint.kRound_Cap)
    glow.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10 * scale))
    line = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeCap=skia.Paint.kRound_Cap)
    dmin, dmax = depth.min(), depth.max()
    span = max(1e-6, dmax - dmin)
    for i, j, axis in sorted(EDGES, key=lambda e: depth[e[0]] + depth[e[1]]):
        if ext[axis] <= 1e-4:
            continue
        near = ((depth[i] + depth[j]) / 2 - dmin) / span
        alpha = (0.45 + 0.55 * near) * min(1.0, ext[axis] * 4)
        width = (2.2 + 2.6 * near) * scale * (0.75 + 0.25 * (f4[i] + f4[j]) / 2)
        p, q = skia.Point(*xy[i]), skia.Point(*xy[j])
        glow.setStrokeWidth(width * 4)
        glow.setColor(_color(AXIS_COLORS[axis], alpha * 0.45))
        canvas.drawLine(p, q, glow)
        line.setStrokeWidth(width)
        line.setColor(_color(AXIS_COLORS[axis], alpha))
        canvas.drawLine(p, q, line)

    # Vertex dots; during the counting beat they pulse in turn, in the order they were created.
    dot = skia.Paint(AntiAlias=True)
    halo = skia.Paint(AntiAlias=True)
    halo.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14 * scale))
    count_phase = (t - PULSE[0]) / (PULSE[1] - PULSE[0]) if PULSE[0] <= t <= PULSE[1] else None
    for index in np.argsort(depth):
        near = (depth[index] - dmin) / span
        r = (5 + 4 * near) * scale * pop
        boost = 0.0
        if count_phase is not None:
            # 4 beats (1D..4D): highlight the vertices that exist in that dimension.
            beat = min(3, int(count_phase * 4))
            in_dim = all(VERTICES[index][d] < 0 for d in range(beat + 1, 4))
            local = (count_phase * 4) % 1
            boost = in_dim * math.sin(math.pi * min(1.0, local * 1.6)) ** 2
        if boost > 0:
            halo.setColor(_color(AXIS_COLORS[min(3, int(count_phase * 4))], 0.8 * boost))
            canvas.drawCircle(*xy[index], r * 4, halo)
        dot.setColor(_color(VERTEX, 0.6 + 0.4 * near))
        canvas.drawCircle(*xy[index], r * (1 + 0.9 * boost), dot)
    image = surface.makeImageSnapshot()
    return image.toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
