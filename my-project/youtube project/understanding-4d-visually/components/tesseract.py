"""The Tesseract Rig: the one 4D model every scene uses.

Vertices are the 16 points of {0, 1}^4 (``V``), or centred in {-1, 1}^4 (``C``).
Edges join corners that differ in exactly one coordinate, and that coordinate is the
edge's axis, so edges are always colored x/y/z/w. Every count on screen comes from here.

Pipeline per frame:  4D points -> rotate4(...) -> project_persp(d) or project_ortho() -> 3D world
-> space.Camera -> draw(...).
"""

from __future__ import annotations

import itertools
import math
from functools import lru_cache

import numpy as np
import skia
from fx import mix
from scipy.spatial import ConvexHull
from theme import TOKENS

AXES = "xyzw"
PLANES = ("xy", "xz", "xw", "yz", "yw", "zw")

V = np.array(list(itertools.product((0, 1), repeat=4)), float)  # row i: bits (x, y, z, w)
C = V * 2 - 1
EDGES = [
    (i, j, int(np.flatnonzero(V[i] != V[j])[0]))
    for i, j in itertools.combinations(range(16), 2)
    if np.count_nonzero(V[i] != V[j]) == 1
]


def _squares():
    out = []
    for a, b in itertools.combinations(range(4), 2):
        rest = [k for k in range(4) if k not in (a, b)]
        for fixed in itertools.product((0, 1), repeat=2):
            loop = []
            for ua, ub in ((0, 0), (1, 0), (1, 1), (0, 1)):  # cyclic order
                bits = [0] * 4
                bits[a], bits[b] = ua, ub
                bits[rest[0]], bits[rest[1]] = fixed
                loop.append(int(np.flatnonzero((V == bits).all(1))[0]))
            out.append((tuple(loop), (a, b)))
    return out


SQUARES = _squares()  # ((4 vertex indices in cyclic order), (axis a, axis b))
CELLS = [(axis, value, tuple(np.flatnonzero(V[:, axis] == value))) for axis in range(4) for value in (0, 1)]
assert len(V) == 16 and len(EDGES) == 32 and len(SQUARES) == 24 and len(CELLS) == 8


def label(i: int) -> str:
    """Binary coordinate label, digits in x y z w order: e.g. '0110'."""
    return "".join(str(int(b)) for b in V[i])


def index_of(bits: str) -> int:
    return int(np.flatnonzero((V == [int(c) for c in bits]).all(1))[0])


def axis_color(axis: int) -> str:
    return TOKENS[AXES[axis]]


def plane_colors(plane: str) -> tuple[str, str]:
    """The two-axis gradient of a rotation plane, e.g. 'zw' -> (yellow, blue)."""
    return TOKENS[plane[0]], TOKENS[plane[1]]


# ------------------------------------------------------------------ linear algebra


def rot4(plane: str, angle: float) -> np.ndarray:
    """4x4 rotation in a coordinate plane ('xy', 'zw', ...). Same cos/sin layout as the 2x2 matrix."""
    a, b = AXES.index(plane[0]), AXES.index(plane[1])
    R = np.eye(4)
    c, s = math.cos(angle), math.sin(angle)
    R[a, a], R[a, b], R[b, a], R[b, b] = c, -s, s, c
    return R


def rotation(*pairs) -> np.ndarray:
    """Product of plane rotations: rotation(('zw', 0.4), ('xy', 0.2))."""
    R = np.eye(4)
    for plane, angle in pairs:
        R = rot4(plane, angle) @ R
    return R


def project_persp(p4: np.ndarray, d: float = 3.0):
    """Perspective along w with the camera at w = d:  x' = d / (d - w) * x.  Returns (Nx3, scale)."""
    p4 = np.atleast_2d(p4)
    f = d / (d - p4[:, 3])
    return p4[:, :3] * f[:, None], f


def project_ortho(p4: np.ndarray) -> np.ndarray:
    """The 3x4 matrix that keeps x, y, z and drops w."""
    P = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]], float)
    return np.atleast_2d(p4) @ P.T


def edge_lengths(points: np.ndarray) -> np.ndarray:
    """Length of every edge for the given vertex positions (works in 4D or 3D)."""
    return np.array([np.linalg.norm(points[i] - points[j]) for i, j, _ in EDGES])


def place(p3: np.ndarray, R3=None, center=(0.0, 0.0, 0.0), scale: float = 1.0) -> np.ndarray:
    """Projected 3D points (math axes x, y, z) -> view/world points for space.Camera (y up)."""
    p = np.asarray(p3, float) * scale
    if R3 is not None:
        p = p @ np.asarray(R3).T
    return p[:, [0, 2, 1]] + np.asarray(center, float)


# ------------------------------------------------------------------ corner-first slices (S16)

# Orthonormal basis of the hyperplane x + y + z + w = s (rows of a Hadamard matrix, all orthogonal to (1, 1, 1, 1)).
SLICE_BASIS = np.array([[1, 1, -1, -1], [1, -1, 1, -1], [1, -1, -1, 1]], float) / 2


@lru_cache(maxsize=512)
def _corner_slice(s_key: int):
    s = s_key / 10000
    pts = []
    for i, j, _ in EDGES:
        a, b = V[i].sum(), V[j].sum()
        if (a - s) * (b - s) <= 0 and a != b:
            u = (s - a) / (b - a)
            pts.append(V[i] + (V[j] - V[i]) * u)
    pts = np.unique(np.round(np.array(pts), 9), axis=0) if pts else np.zeros((0, 4))
    if len(pts) < 4:
        return np.zeros((0, 3)), []
    local = (pts - s / 4) @ SLICE_BASIS.T  # 3D coordinates inside the hyperplane
    hull = ConvexHull(local)
    faces = {}
    for simplex, eq in zip(hull.simplices, hull.equations):
        key = tuple(np.round(eq, 6))
        faces.setdefault(key, set()).update(simplex.tolist())
    loops = []
    for key, idx in faces.items():
        idx = list(idx)
        n = np.array(key[:3])
        c = local[idx].mean(0)
        u = local[idx[0]] - c
        u /= np.linalg.norm(u)
        v = np.cross(n, u)
        ang = [math.atan2((local[k] - c) @ v, (local[k] - c) @ u) for k in idx]
        loops.append([idx[k] for k in np.argsort(ang)])
    return local, loops


def corner_slice(s: float):
    """The real 3D cross-section of the unit tesseract by x + y + z + w = s (0 < s < 4).

    Returns (points Nx3 in the hyperplane, faces as vertex loops). s <= 1: tetrahedron,
    1 < s < 2: truncated tetrahedron, s = 2: regular octahedron (symmetric about 2).
    """
    return _corner_slice(int(round(s * 10000)))


def loop_edges(loops) -> list[tuple[int, int]]:
    seen = set()
    for loop in loops:
        for a, b in zip(loop, loop[1:] + loop[:1]):
            seen.add((min(a, b), max(a, b)))
    return sorted(seen)


# ------------------------------------------------------------------ drawing


def depth_alpha(cam, world: np.ndarray, near=1.0, far=0.45) -> np.ndarray:
    """Per-vertex brightness from camera depth: nearest vertex -> near, farthest -> far."""
    _, _, z = cam.project(world)
    span = max(1e-6, float(z.max() - z.min()))
    return near + (far - near) * (z - z.min()) / span


def draw(fr, cam, world: np.ndarray, alpha=1.0, width=2.0, glow=0.6, edge_alpha=None, colors=None,
         vertices=0.0, vertex_r=4.0, depth_cue=True):
    """Edges colored by axis, depth-cued; optional vertex dots.

    edge_alpha: optional length-32 multipliers; colors: optional {axis or edge index: color} overrides.
    """
    if alpha <= 0.003:
        return
    xs, ys, z = cam.project(world)
    if np.any(z <= 0.05):
        return
    da = depth_alpha(cam, world) if depth_cue else np.ones(16)
    order = sorted(range(len(EDGES)), key=lambda k: -(z[EDGES[k][0]] + z[EDGES[k][1]]))  # far to near
    colors = colors or {}
    for k in order:
        i, j, axis = EDGES[k]
        a = alpha * (1.0 if edge_alpha is None else float(edge_alpha[k])) * 0.5 * (da[i] + da[j])
        if a <= 0.003:
            continue
        color = colors.get(("edge", k), colors.get(axis, axis_color(axis)))
        fr.line(xs[i], ys[i], xs[j], ys[j], color, width, a, glow=glow)
    if vertices > 0:
        for i in range(16):
            fr.glow_dot(xs[i], ys[i], vertex_r, "ink", alpha * vertices * da[i], strength=0.6)


def hull_path(xs, ys) -> skia.Path:
    pts = np.stack([xs, ys], 1)
    hull = ConvexHull(pts)
    p = skia.Path()
    p.addPoly([skia.Point(float(pts[k, 0]), float(pts[k, 1])) for k in hull.vertices], True)
    return p


def fill_cell(fr, cam, world, cell: int, color="ink", alpha=0.12, stroke=0.0, sweep=None):
    """Glass tint over one of the 8 cubic cells (its projected convex hull)."""
    if alpha <= 0.003:
        return
    idx = list(CELLS[cell][2])
    xs, ys, _ = cam.project(world[idx])
    path = hull_path(xs, ys)
    fr.path_fill(path, color, alpha)
    if stroke > 0:
        fr.path_stroke(path, color, 1.2, stroke)
    if sweep is not None:
        fr.light_sweep(path, sweep)


def fill_square(fr, cam, world, square: int, color="ink", alpha=0.10):
    loop, _ = SQUARES[square]
    xs, ys, _ = cam.project(world[list(loop)])
    p = skia.Path()
    p.addPoly([skia.Point(float(x), float(y)) for x, y in zip(xs, ys)], True)
    fr.path_fill(p, color, alpha)


def draw_trails(fr, cam, world_at, t, span=1.0, steps=20, alpha=0.6, width=1.4, color="ink", which=None):
    """Fading trails of vertex positions over the last ``span`` seconds. ``world_at(t) -> 16x3``."""
    if alpha <= 0.003 or span <= 0:
        return
    hist = np.stack([world_at(t - span * k / steps) for k in range(steps + 1)])  # (steps+1, 16, 3)
    which = range(16) if which is None else which
    for v in which:
        xs, ys, z = cam.project(hist[:, v])
        if np.any(z <= 0.05):
            continue
        for k in range(steps):
            a = alpha * (1 - k / steps) ** 1.6
            fr.line(xs[k], ys[k], xs[k + 1], ys[k + 1], color, width * (1 - 0.6 * k / steps), a)


def draw_solid(fr, cam, world, loops, color="w", alpha=1.0, fill=0.10, width=2.2, glow=0.8, sweep=None):
    """A convex slice solid: tinted faces (back to front) and razor edges in ``color``."""
    if alpha <= 0.003 or len(world) == 0:
        return
    xs, ys, z = cam.project(world)
    order = sorted(loops, key=lambda lp: -float(np.mean(z[lp])))
    for lp in order:
        p = skia.Path()
        p.addPoly([skia.Point(float(xs[k]), float(ys[k])) for k in lp], True)
        fr.path_fill(p, mix(TOKENS["bg"], TOKENS.get(color, color), 0.9), alpha * fill)
    if sweep is not None:
        fr.light_sweep(hull_path(xs, ys), sweep)
    da = depth_alpha(cam, world, 1.0, 0.5)
    for a, b in loop_edges(loops):
        fr.line(xs[a], ys[a], xs[b], ys[b], color, width, alpha * 0.5 * (da[a] + da[b]), glow=glow)
