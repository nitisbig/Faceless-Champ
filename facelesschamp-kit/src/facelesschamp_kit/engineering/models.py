"""Bounded native build123d engineering models, in millimetres.

These are dimensioned teaching models, not tool-specific manufacturing drawings.
The spur gear uses a sampled involute profile with standard full-depth proportions.
"""

import inspect
import math
from copy import deepcopy

from faceless_champ.integrations.build123d import _engine
from faceless_champ.integrations.pyvista.model import ArchDataError, number

__all__ = ["gear_pair", "inline_engine", "piston", "portal_frame", "slider_crank", "spur_gear", "validate_preset"]


def _integer(value, name, low, high):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ArchDataError(name, f"expected integer from {low} to {high}")


def validate_preset(name, params=None):
    """Validate preset parameters without importing a CAD kernel or opening GL."""
    params = {} if params is None else params
    if not isinstance(name, str) or name not in CAD_PRESETS or not isinstance(params, dict):
        raise ArchDataError("cad.preset", "unsupported preset or parameters")
    try:
        bound = inspect.signature(CAD_PRESETS[name]).bind(**params)
        bound.apply_defaults()
    except TypeError as exc:
        raise ArchDataError("cad.params", str(exc)) from exc
    p = bound.arguments
    for key, value in p.items():
        if key not in {"teeth", "cylinders", "bays"}:
            number(value, key, 0 if key == "bore" else 1e-6)
    if name in {"spur_gear", "gear_pair"}:
        if not 5 <= p["pressure_angle"] <= 35:
            raise ArchDataError("pressure_angle", "expected 5 to 35 degrees")
        minimum = math.ceil(2 / math.sin(math.radians(p["pressure_angle"])) ** 2)
        teeth = (p["teeth"],) if name == "spur_gear" else p["teeth"]
        if not isinstance(teeth, (list, tuple)) or (name == "gear_pair" and len(teeth) != 2):
            raise ArchDataError("teeth", "expected two tooth counts")
        for n in teeth:
            _integer(n, "teeth", minimum, 256)
            if p["bore"] >= p["module"] * (n - 2.5):
                raise ArchDataError("bore", "bore must be smaller than the root diameter")
    if name in {"slider_crank", "inline_engine"} and p["rod_length"] <= p["crank_radius"]:
        raise ArchDataError("rod_length", "must exceed crank_radius")
    if name == "inline_engine":
        _integer(p["cylinders"], "cylinders", 1, 8)
        if p["pitch"] <= p["diameter"] + 4:
            raise ArchDataError("pitch", "must exceed piston diameter plus housing wall clearance")
    if name == "portal_frame":
        _integer(p["bays"], "bays", 1, 20)
        if p["member"] >= min(p["bay_width"], p["height"]):
            raise ArchDataError("member", "must be smaller than bay width and height")
    if name == "piston" and p["pin_diameter"] >= min(p["diameter"], p["height"]):
        raise ArchDataError("pin_diameter", "pin must fit inside the piston")
    return deepcopy(dict(p))


def _model(shape, preset, params):
    shape._faceless_provenance = {"preset": preset, "parameters": params}
    return shape


def spur_gear(module=2, teeth=24, width=10, bore=6, pressure_angle=20):
    """External involute spur gear; bore is diameter, shaft axis is local Z.

    Ten samples per involute flank and four samples per circular land bound the
    profile complexity. Undercut configurations are rejected, not approximated.
    """
    p = validate_preset("spur_gear", locals())
    bd = _engine()
    pitch = module * teeth / 2
    root, outer = pitch - 1.25 * module, pitch + module
    base = pitch * math.cos(math.radians(pressure_angle))
    inv_pitch = math.tan(math.radians(pressure_angle)) - math.radians(pressure_angle)
    half = math.pi / (2 * teeth)

    def flank(radius):
        alpha = math.acos(min(1, base / radius))
        return half + inv_pitch - (math.tan(alpha) - alpha)

    points = []

    def point(radius, angle):
        points.append((radius * math.cos(angle), radius * math.sin(angle), 0))

    for i in range(teeth):
        center = i * 2 * math.pi / teeth
        start = max(root, base)
        point(root, center - flank(start))
        radii = [start + (outer - start) * j / 10 for j in range(11)]
        for r in radii:
            point(r, center - flank(r))
        for j in range(1, 5):
            point(outer, center - flank(outer) + 2 * flank(outer) * j / 4)
        for r in reversed(radii[:-1]):
            point(r, center + flank(r))
        point(root, center + flank(start))
        end = center + 2 * math.pi / teeth - flank(start)
        for j in range(1, 4):
            point(root, center + flank(start) + (end - center - flank(start)) * j / 4)
    shape = bd.extrude(bd.Face(bd.Wire.make_polygon(points, close=True)), amount=width)
    if bore:
        shape = shape - bd.Pos(Z=width / 2) * bd.Cylinder(bore / 2, width * 2)
    shape.label = "gear"
    return _model(shape, "spur_gear", p)


def gear_pair(module=2, teeth=(24, 48), width=10, bore=6, pressure_angle=20):
    """Two meshing gears with stable driver/driven labels and pitch-center spacing."""
    p = validate_preset("gear_pair", locals())
    bd = _engine()
    driver = spur_gear(module, teeth[0], width, bore, pressure_angle)
    driven = spur_gear(module, teeth[1], width, bore, pressure_angle)
    driver.label, driven.label = "driver", "driven"
    # A tooth faces +X on the driver. Place a gap at -X on the driven;
    # odd tooth counts already have a gap there at zero rotation.
    phase = 180 / teeth[1] if teeth[1] % 2 == 0 else 0
    driven.location = bd.Location((module * sum(teeth) / 2, 0, 0), (0, 0, phase))
    return _model(bd.Compound(children=[driver, driven], label="gear-pair"), "gear_pair", p)


def piston(diameter=12, height=14, pin_diameter=3):
    """Piston centered on its pin, bore axis X and pin axis Z, with ring grooves."""
    p = validate_preset("piston", locals())
    bd = _engine()
    body = bd.Rot(0, 90, 0) * bd.Cylinder(diameter / 2, height)
    body -= bd.Cylinder(pin_diameter / 2, diameter * 2)
    for x in (height * 0.22, height * 0.36):
        ring = bd.Cylinder(diameter, height * 0.035) - bd.Cylinder(diameter * 0.46, height * 0.07)
        body -= bd.Pos(X=x) * bd.Rot(0, 90, 0) * ring
    body.label = "piston"
    return _model(body, "piston", p)


def slider_crank(crank_radius=10, rod_length=35, diameter=12):
    """Canonical XY rest assembly matching ArchScript.slider_crank, crank angle zero."""
    p = validate_preset("slider_crank", locals())
    bd = _engine()
    r, length = crank_radius, rod_length
    crank = bd.Box(r, r * 0.35, r * 0.25, align=(bd.Align.MIN, bd.Align.CENTER, bd.Align.CENTER))
    crank += bd.Pos(X=r) * bd.Cylinder(r * 0.2, r * 0.4)
    crank.label = "crank"
    rod = bd.Box(length, diameter * 0.2, diameter * 0.18, align=(bd.Align.MIN, bd.Align.CENTER, bd.Align.CENTER))
    rod.label, rod.location = "rod", bd.Location((r, 0, 0))
    head = piston(diameter=diameter, height=diameter * 1.15, pin_diameter=diameter * 0.2)
    head.location = bd.Location((r + length, 0, 0))
    return _model(bd.Compound(children=[crank, rod, head], label="slider-crank"), "slider_crank", p)


def inline_engine(cylinders=4, crank_radius=10, rod_length=35, diameter=12, pitch=24):
    """Dimensioned inline teaching engine: repeated slider-cranks, shaft and bored block."""
    p = validate_preset("inline_engine", locals())
    bd = _engine()
    children = []
    for i in range(cylinders):
        mechanism = slider_crank(crank_radius, rod_length, diameter)
        mechanism.label, mechanism.location = f"cylinder-{i + 1}", bd.Location((0, 0, i * pitch))
        children.append(mechanism)
    span = (cylinders - 1) * pitch + diameter + 8
    center = crank_radius + rod_length
    block = bd.Pos(center, 0, (cylinders - 1) * pitch / 2) * bd.Box(4 * crank_radius + diameter, diameter + 8, span)
    for i in range(cylinders):
        bore = (
            bd.Pos(center, 0, i * pitch) * bd.Rot(0, 90, 0) * bd.Cylinder(diameter * 0.53, 5 * crank_radius + diameter)
        )
        block -= bore
    block.label = "block"
    shaft = bd.Pos(Z=(cylinders - 1) * pitch / 2) * bd.Cylinder(crank_radius * 0.18, span)
    shaft.label = "shaft"
    return _model(bd.Compound(children=[*children, block, shaft], label="inline-engine"), "inline_engine", p)


def portal_frame(bays=3, bay_width=4000, height=3000, depth=3000, member=200):
    """Named rectangular columns/beams; dimensions in mm and Z up."""
    p = validate_preset("portal_frame", locals())
    bd = _engine()
    children = []
    for i in range(bays + 1):
        for side, y in enumerate((0, depth)):
            column = bd.Pos(i * bay_width, y, height / 2) * bd.Box(member, member, height)
            column.label = f"column-{i}-{side}"
            children.append(column)
        beam = bd.Pos(i * bay_width, depth / 2, height) * bd.Box(member, depth + member, member)
        beam.label = f"crossbeam-{i}"
        children.append(beam)
    for i in range(bays):
        for side, y in enumerate((0, depth)):
            beam = bd.Pos((i + 0.5) * bay_width, y, height) * bd.Box(bay_width, member, member)
            beam.label = f"beam-{i}-{side}"
            children.append(beam)
    return _model(bd.Compound(children=children, label="portal-frame"), "portal_frame", p)


CAD_PRESETS = {f.__name__: f for f in (spur_gear, gear_pair, piston, slider_crank, inline_engine, portal_frame)}
