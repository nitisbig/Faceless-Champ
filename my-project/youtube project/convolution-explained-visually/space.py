"""Tiny 3D toolkit: look-at cameras, painter-sorted shaded boxes, projected text.

Geometry is real 3D (numpy), projected with a pinhole camera and drawn with
skia through fx.Frame, so 3D shots share the exact line quality of the 2D ones.
"""

from __future__ import annotations

import math

import numpy as np
import skia

from fx import mix
from theme import TOKENS


class Camera:
    def __init__(self, eye, target, focal=1000.0, center=(960.0, 540.0), up=(0.0, 1.0, 0.0)):
        self.eye = np.asarray(eye, float)
        self.target = np.asarray(target, float)
        f = self.target - self.eye
        self.f = f / np.linalg.norm(f)
        r = np.cross(np.asarray(up, float), self.f)
        self.r = r / np.linalg.norm(r)
        self.u = np.cross(self.f, self.r)
        self.focal, self.cx, self.cy = focal, center[0], center[1]

    def project(self, points):
        p = np.atleast_2d(np.asarray(points, float)) - self.eye
        z = np.maximum(p @ self.f, 1e-3)
        return self.cx + self.focal * (p @ self.r) / z, self.cy - self.focal * (p @ self.u) / z, z

    def depth(self, point):
        return float((np.asarray(point, float) - self.eye) @ self.f)


def orbit(target, dist, elev, azim, focal=1000.0, center=(960.0, 540.0)):
    """Camera on a sphere around ``target``; azim 0 looks along +z, elev lifts it."""
    t = np.asarray(target, float)
    eye = t + dist * np.array([math.cos(elev) * math.sin(azim), math.sin(elev), -math.cos(elev) * math.cos(azim)])
    return Camera(eye, t, focal, center)


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


CORNERS = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], float)
# (outward normal, corner indices in winding order)
FACES = [
    ((1, 0, 0), (4, 5, 7, 6)), ((-1, 0, 0), (0, 2, 3, 1)),
    ((0, 1, 0), (2, 6, 7, 3)), ((0, -1, 0), (0, 1, 5, 4)),
    ((0, 0, 1), (1, 3, 7, 5)), ((0, 0, -1), (0, 4, 6, 2)),
]
LIGHT = np.array([-0.35, 0.85, -0.45]) / np.linalg.norm([-0.35, 0.85, -0.45])


def box_faces(center, half, R=None):
    """Yield (normal, corner points 4x3, face centre) for each face of a box."""
    R = np.eye(3) if R is None else R
    verts = np.asarray(center, float) + (CORNERS * np.asarray(half, float)) @ R.T
    for n, idx in FACES:
        normal = R @ np.asarray(n, float)
        pts = verts[list(idx)]
        yield normal, pts, pts.mean(0)


def _poly_path(xs, ys):
    p = skia.Path()
    p.moveTo(float(xs[0]), float(ys[0]))
    for x, y in zip(xs[1:], ys[1:]):
        p.lineTo(float(x), float(y))
    p.close()
    return p


def draw_box(fr, cam, center, half, fill, stroke, alpha=1.0, R=None, fill_strength=0.22, stroke_width=1.6,
             glow=0.0, on_face=None):
    """Opaque flat-shaded box with emissive edges. ``on_face(normal, pts, path)`` decorates visible faces."""
    if alpha <= 0.003:
        return
    for normal, pts, fc in box_faces(center, half, R):
        if float(normal @ (cam.eye - fc)) <= 0:
            continue
        xs, ys, _ = cam.project(pts)
        path = _poly_path(xs, ys)
        shade = 0.45 + 0.55 * max(0.0, float(normal @ LIGHT))
        face = mix(TOKENS["bg"], TOKENS.get(fill, fill), fill_strength * shade)
        fr.path_fill(path, face, alpha)
        fr.path_stroke(path, stroke, stroke_width, alpha, glow=glow)
        if on_face is not None:
            on_face(normal, pts, path)


def draw_boxes(fr, cam, boxes):
    """Painter-sort a list of dicts (center, half, ...draw_box kwargs) far-to-near and draw them."""
    for b in sorted(boxes, key=lambda b: -cam.depth(b["center"])):
        b = dict(b)
        draw_box(fr, cam, b.pop("center"), b.pop("half"), **b)


def text3d(fr, cam, s, point, size, color, alpha=1.0, weight=600, family="display", glow=0.0):
    """Text whose size follows perspective, centred on a 3D point."""
    x, y, z = cam.project(point)
    px = size * cam.focal / float(z[0])
    if px < 4:
        return
    fr.text(s, float(x[0]), float(y[0]) + px * 0.36, family, px, weight, color, alpha, glow=glow)
