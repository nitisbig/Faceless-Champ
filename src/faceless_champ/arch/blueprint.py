"""Prepared CAD hidden-line views made from existing portable drawing primitives."""

import hashlib
import json
import math
from dataclasses import asdict
from itertools import pairwise

from .cad import _detached, _engine, _unit_scale, parts_from_cad
from .camera import ArchCamera, part_matrix
from .dependencies import _versions
from .model import ArchDataError, ArchDimension, _format_dimension, number

__all__ = ["blueprint_from_cad"]


def blueprint_from_cad(
    shape,
    *,
    camera=None,
    width=1600,
    height=900,
    margin=70,
    dimensions=(),
    source_units="mm",
    target_units="mm",
    color="#63d3ff",
    hidden_color="#567080",
    font=None,
    font_size=24,
    linear_deflection=0.05,
    max_segments=20000,
):
    """Prepare one orthographic CAD projection without a renderer or GL context.

    Curves are sampled adaptively in source units; hidden edges use portable dash
    segments. Dimension values come from original 3D anchors, not projected lengths.
    Part-bound anchors use the same stable leaf IDs as parts_from_cad.
    """
    import numpy as np

    from ..components import Arrow, Polyline, Rectangle, Text
    from ..layout import Group

    bd = _engine()
    dimensions = tuple(dimensions)
    if any(not isinstance(d, ArchDimension) for d in dimensions):
        raise ArchDataError("dimensions", "expected ArchDimension values")
    if not isinstance(shape, bd.Shape) or shape.wrapped is None:
        raise ArchDataError("cad.shape", "expected a nonempty build123d Shape")
    width, height = number(width, "width", 1), number(height, "height", 1)
    margin = number(margin, "margin", 0)
    tolerance = number(linear_deflection, "linear_deflection", 1e-9)
    if 2 * margin >= min(width, height):
        raise ArchDataError("margin", "must leave drawable viewport space")
    if isinstance(max_segments, bool) or not isinstance(max_segments, int) or max_segments < 1:
        raise ArchDataError("max_segments", "expected positive integer")
    factor = _unit_scale(source_units, target_units)
    camera = camera or ArchCamera()
    if not isinstance(camera, ArchCamera) or camera.projection != "orthographic":
        raise ArchDataError("camera", "CAD blueprints require an orthographic ArchCamera")
    forward = np.asarray(camera.focal_point) - camera.position
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, camera.up)
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    center = np.asarray(camera.focal_point)

    def project(p):
        delta = np.asarray(p) - center
        return np.array((delta @ right, -(delta @ up)))

    # Native HLR works on a detached copy so caller state and cached triangulations
    # remain outside this prepared drawing's lifecycle.
    visible, hidden = _detached(shape).project_to_viewport(camera.position, camera.up, camera.focal_point)
    contours, count = [], 0

    def sample(edge, t0, a, t1, b, depth=0):
        nonlocal count
        mid = (t0 + t1) / 2
        p = np.asarray(tuple(edge.position_at(mid)), dtype=float)
        # Quarter samples catch inflections/closed curves with coincident endpoints.
        error = max(
            np.linalg.norm(np.asarray(tuple(edge.position_at(t))) - (a + (b - a) * u))
            for u, t in ((0.25, t0 + (t1 - t0) / 4), (0.5, mid), (0.75, t0 + (t1 - t0) * 3 / 4))
        )
        if error > tolerance:
            if depth >= 24:
                raise ArchDataError("blueprint.budget", "curve subdivision exceeded depth budget")
            return sample(edge, t0, a, mid, p, depth + 1)[:-1] + sample(edge, mid, p, t1, b, depth + 1)
        count += 1
        if count > max_segments:
            raise ArchDataError("blueprint.budget", "edge segment budget exceeded")
        return [a, b]

    # Draw visible edges last so coincident hidden contours cannot dim them.
    for is_hidden, edges in ((True, hidden), (False, visible)):
        for edge in edges:
            points = sample(edge, 0, np.asarray(tuple(edge.position_at(0))), 1, np.asarray(tuple(edge.position_at(1))))
            # build123d HLR returns edges already transformed into the view's XY plane.
            contours.append((is_hidden, [np.array((p[0], -p[1])) for p in points]))
    if not contours:
        raise ArchDataError("blueprint", "projection produced no edges")
    all_points = np.asarray([p for _, points in contours for p in points])
    low, high = all_points.min(axis=0), all_points.max(axis=0)
    extent = np.maximum(high - low, 1e-12)
    scale = min((width - 2 * margin) / extent[0], (height - 2 * margin) / extent[1])
    offset = np.array((width, height)) / 2 - (low + high) / 2 * scale

    def screen(p):
        return tuple(p * scale + offset)

    elements = [Rectangle(width=width, height=height, fill=None, stroke=None, position=(width / 2, height / 2))]
    for is_hidden, points in contours:
        if not is_hidden:
            elements.append(Polyline([screen(p) for p in points], stroke=color, stroke_width=1.5))
        else:
            distance = 0.0
            for a, b in pairwise(points):
                a, b = np.asarray(screen(a)), np.asarray(screen(b))
                length = float(np.linalg.norm(b - a))
                cursor = 0.0
                while cursor < length:
                    amount = min(length - cursor, 8 - distance % 8)
                    if distance % 8 < 5 and amount > 1e-8:
                        end = min(cursor + amount, cursor + 5 - distance % 8)
                        if end > cursor:
                            elements.append(
                                Polyline(
                                    [tuple(a + (b - a) * cursor / length), tuple(a + (b - a) * end / length)],
                                    stroke=hidden_color,
                                    stroke_width=1,
                                )
                            )
                    cursor += amount
                    distance += amount
                if len(elements) > max_segments * 4:
                    raise ArchDataError("blueprint.budget", "dash segment budget exceeded")
    parts = {}
    if any(d.part for d in dimensions):
        for part in parts_from_cad(shape, source_units=source_units, target_units=source_units):
            parts[part.id] = part_matrix({"position": part.position, "rotation": part.rotation, "scale": part.scale})
    for dimension in dimensions:
        if not isinstance(dimension, ArchDimension) or (dimension.part is not None and dimension.part not in parts):
            raise ArchDataError("dimensions", "expected ArchDimension with a valid CAD part anchor")
        anchors = []
        for point in (dimension.start, dimension.end):
            anchors.append((parts[dimension.part] @ np.array((*point, 1)))[:3] if dimension.part else np.asarray(point))
        a, b = (np.asarray(screen(project(p))) for p in anchors)
        shift = np.asarray(dimension.offset)
        for p in (a, b):
            elements.append(Polyline([tuple(p), tuple(p + shift)], stroke=dimension.color, stroke_width=1))
        length = float(np.linalg.norm(b - a))
        if length < 1:
            raise ArchDataError("dimensions", "anchors project less than one pixel apart; choose another view")
        elements.append(
            Arrow(
                tuple(a + shift), tuple(b + shift), stroke=dimension.color, stroke_width=1.5, tip_size=min(10, length)
            )
        )
        elements.append(
            Text(
                _format_dimension(math.dist(*anchors) * factor, dimension.precision, target_units),
                font=font,
                font_size=font_size,
                color=dimension.color,
                position=tuple((a + b) / 2 + shift + (0, 16)),
            )
        )
    group = Group(*elements)
    record = {
        **getattr(shape, "_faceless_provenance", {}),
        "generator": "build123d.HLR",
        "units": target_units,
        "source_units": source_units,
        "camera": asdict(camera),
        "linear_deflection": tolerance,
        "viewport": {"width": width, "height": height, "margin": margin},
        "style": {
            "color": color,
            "hidden_color": hidden_color,
            "font": str(font) if font else None,
            "font_size": font_size,
        },
        "max_segments": max_segments,
        "dimensions": [asdict(d) for d in dimensions],
        "versions": _versions("build123d", "cadquery-ocp-novtk", "numpy"),
        "geometry": [(hidden, [p.tolist() for p in points]) for hidden, points in contours],
    }
    group.geometry_provenance = {
        **{k: v for k, v in record.items() if k != "geometry"},
        "fingerprint": hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest(),
    }
    return group
