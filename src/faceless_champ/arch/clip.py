"""Random-access assembly evaluation and shared structured authoring contract."""

import hashlib
import json
import math
from copy import deepcopy
from dataclasses import asdict

from PIL import Image, ImageDraw

from ..components import Component
from ..typography import load_font
from .camera import ArchCamera, project, world
from .model import (
    ArchDataError,
    ArchDimension,
    ArchLabel,
    ArchMesh,
    ArchPart,
    ArchStyle,
    _format_dimension,
    construct,
    number,
    pyvista,
    text,
    vector,
)
from .script import ArchScript

PRIMITIVES = {
    "cube": {"center", "x_length", "y_length", "z_length"},
    "sphere": {"center", "radius", "theta_resolution", "phi_resolution"},
    "cylinder": {"center", "direction", "radius", "height", "resolution"},
    "cone": {"center", "direction", "radius", "height", "resolution"},
    "plane": {"center", "direction", "i_size", "j_size", "i_resolution", "j_resolution"},
    "torus": {"ringradius", "crosssectionradius", "u_res", "v_res"},
}


def validate_design(data, *, registered_only=False):
    """Validate the JSON contract without creating geometry or a render window."""
    if not isinstance(data, dict) or set(data) - {
        "parts",
        "style",
        "camera",
        "script",
        "labels",
        "dimensions",
        "units",
        "cad",
    }:
        raise ArchDataError("design", "unknown fields or expected an object")
    cad_source = "cad" in data
    if cad_source:
        from .cad import _unit_scale, _validate_source

        if "parts" in data:
            raise ArchDataError("design", "use parts or cad, not both")
        _validate_source(data["cad"])
        _unit_scale("mm", data.get("units", "mm"))
    parts = data.get("parts", []) if cad_source else data.get("parts")
    if not cad_source and (not isinstance(parts, (list, tuple)) or not parts):
        raise ArchDataError("parts", "expected named parts")
    ids = set()
    for p in parts:
        if not isinstance(p, dict) or set(p) - {
            "id",
            "mesh",
            "position",
            "rotation",
            "scale",
            "style",
            "explode_vector",
        }:
            raise ArchDataError("part", "unknown fields")
        id = text(p.get("id"), "id")
        if id in ids or id == "camera":
            raise ArchDataError("id", "duplicate or reserved ID")
        ids.add(id)
        mesh = p.get("mesh")
        if not isinstance(mesh, dict) or len(set(mesh) & {"primitive", "asset", "file"}) != 1:
            raise ArchDataError("mesh", "use exactly one primitive, asset or file source")
        source = next(iter(set(mesh) & {"primitive", "asset", "file"}))
        if set(mesh) - ({"primitive", "params"} if source == "primitive" else {source}):
            raise ArchDataError("mesh", "unknown source fields")
        if source == "primitive":
            kind = mesh["primitive"]
            params = mesh.get("params", {})
            if kind not in PRIMITIVES or not isinstance(params, dict) or set(params) - PRIMITIVES[kind]:
                raise ArchDataError("primitive", "unsupported primitive or parameters")
            for key, value in params.items():
                if key in {"center", "direction"}:
                    vector(value, key)
                    if key == "direction" and not any(value):
                        raise ArchDataError(key, "must be nonzero")
                else:
                    number(value, key, 0.000001)
                    if ("resolution" in key or key.endswith("_res")) and (
                        isinstance(value, bool) or not isinstance(value, int) or value < 3
                    ):
                        raise ArchDataError(key, "expected integer >= 3")
        else:
            text(mesh[source], source)
            if registered_only and source == "file":
                raise ArchDataError("mesh", "recipes require a registered mesh asset")
        for key in ("position", "rotation", "explode_vector"):
            if key in p:
                vector(p[key], key)
        if "scale" in p:
            number(p["scale"], "scale", 0.000001)
        if "style" in p:
            construct(ArchStyle, p["style"])
    if "style" in data:
        construct(ArchStyle, data["style"])
    if "camera" in data:
        construct(ArchCamera, data["camera"])
    if "units" in data:
        text(data["units"], "units")
    for key, cls in (("labels", ArchLabel), ("dimensions", ArchDimension)):
        if not isinstance(data.get(key, []), (list, tuple)):
            raise ArchDataError(key, "expected array")
        for raw in data.get(key, []):
            item = construct(cls, raw)
            if not cad_source and item.part is not None and item.part not in ids:
                raise ArchDataError(key, "unknown anchor part")
    script = ArchScript.from_dict(data.get("script", {}))
    for a in script.actions:
        if not cad_source and any(t not in (ids | {"camera"}) for t in a.targets):
            raise ArchDataError("targets", "unknown part")
        if a.kind not in {"camera_to", "orbit"} and "camera" in a.targets:
            raise ArchDataError("targets", "expected parts")
    return deepcopy(data)


class ArchChamp(Component):
    def __init__(
        self,
        parts,
        script=None,
        *,
        width=1600,
        height=900,
        camera=None,
        style=None,
        labels=(),
        dimensions=(),
        units="model units",
        font=None,
        source_start=0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if isinstance(parts, ArchMesh):
            parts = [ArchPart("model", parts)]
        if not isinstance(parts, (list, tuple)) or not parts or any(not isinstance(p, ArchPart) for p in parts):
            raise ArchDataError("parts", "expected ArchPart sequence or ArchMesh")
        if len({p.id for p in parts}) != len(parts):
            raise ArchDataError("parts", "duplicate IDs")
        self.parts = tuple(deepcopy(parts))
        self.style = deepcopy(style or ArchStyle())
        self.script = deepcopy(script or ArchScript())
        if not isinstance(self.style, ArchStyle) or not isinstance(self.script, ArchScript):
            raise ArchDataError("arch", "expected ArchStyle and ArchScript")
        self.width, self.height = number(width, "width", 1), number(height, "height", 1)
        self.units, self.font = text(units, "units"), font
        prepared_units = {p.mesh.provenance.get("units") for p in self.parts} - {None}
        if len(prepared_units) > 1 or (prepared_units and units != "model units" and units not in prepared_units):
            raise ArchDataError("units", "prepared geometry units differ; convert geometry before labeling it")
        self.labels, self.dimensions = tuple(deepcopy(labels)), tuple(deepcopy(dimensions))
        self.duration = self.script.duration
        self.source_start = number(source_start, "source_start", 0)
        if self.source_start > self.duration:
            raise ArchDataError("source_start", "exceeds script duration")
        self._parts = {p.id: p for p in self.parts}
        for item in (*self.labels, *self.dimensions):
            if not isinstance(item, (ArchLabel, ArchDimension)) or (item.part and item.part not in self._parts):
                raise ArchDataError("annotation", "invalid type or unknown part")
        self._actions = tuple(sorted(self.script.actions, key=lambda a: a.at))
        for a in self._actions:
            if any(t not in self._parts and t != "camera" for t in a.targets):
                raise ArchDataError("targets", "unknown part")
            if a.kind not in {"orbit", "camera_to"} and "camera" in a.targets:
                raise ArchDataError("targets", "expected parts")
        # Field and cap constraints fail before export, without a GL context.
        for p in self.parts:
            s, mesh = p.style or self.style, p.mesh._dataset
            arrays = mesh.point_data if s.association == "point" else mesh.cell_data
            for key in (s.scalars, s.vectors):
                if key and key not in arrays:
                    raise ArchDataError(key, "field missing in selected association")
            if s.scalars and arrays[s.scalars].ndim != 1:
                raise ArchDataError("scalars", "expected scalar field")
            for key in (s.scalars, s.vectors):
                if key and arrays[key].dtype.kind not in "fiu":
                    raise ArchDataError(key, "fields must be numeric")
            if s.vectors and (arrays[s.vectors].ndim != 2 or arrays[s.vectors].shape[1] != 3):
                raise ArchDataError("vectors", "expected three-component vectors")
            if s.concept == "heatmap" and not s.scalars:
                raise ArchDataError("heatmap", "requires a supplied scalar field")
            capped = any(a.kind == "section" and p.id in a.targets and a.options["cap"] for a in self._actions)
            if (capped or s.concept == "voxel") and (s.scalars or s.vectors):
                raise ArchDataError("fields", "capped sections and voxelization do not preserve supplied fields")
            if capped or s.concept == "voxel":
                surface = mesh.extract_surface(algorithm="dataset_surface").triangulate()
                if not surface.is_manifold:
                    raise ArchDataError("surface", "capping and voxelization require a closed manifold surface")
        self.camera = camera or ArchCamera()
        if not isinstance(self.camera, ArchCamera):
            raise ArchDataError("camera", "expected ArchCamera")
        center, radius = self._framing()
        self.parallel_scale = radius * 1.25 * max(1, self.height / self.width)
        if camera is None:
            offset = (0, -4, 0) if self.style.concept == "blueprint" else (4, -4, 3)
            self.camera = ArchCamera(tuple(center[i] + offset[i] * radius for i in range(3)), tuple(center))
        self.fingerprint = hashlib.sha256(
            json.dumps(
                {
                    "parts": [
                        {
                            "id": p.id,
                            "mesh": p.mesh.fingerprint,
                            **({"provenance": p.mesh.provenance} if p.mesh.provenance else {}),
                            "position": p.position,
                            "rotation": p.rotation,
                            "scale": p.scale,
                            "style": asdict(p.style or self.style),
                            "explode": p.explode_vector,
                        }
                        for p in self.parts
                    ],
                    "script": self.script.to_dict(),
                    "camera": asdict(self.camera),
                    "units": units,
                    "viewport": [self.width, self.height],
                    "source_start": self.source_start,
                    "font": str(self.font) if self.font is not None else None,
                    "labels": [asdict(v) for v in self.labels],
                    "dimensions": [asdict(v) for v in self.dimensions],
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()

    @classmethod
    def from_data(cls, data, **kwargs):
        pv = pyvista()
        data = pv.wrap(data)
        if isinstance(data, pv.MultiBlock):
            parts = []

            def collect(block, prefix=""):
                for i, child in enumerate(block):
                    if child is None:
                        continue
                    name = prefix + (block.get_block_name(i) or f"part-{i}")
                    if isinstance(child, pv.MultiBlock):
                        collect(child, name + "/")
                    else:
                        parts.append(ArchPart(name, ArchMesh.from_data(child)))

            collect(data)
            return cls(parts, **kwargs)
        return cls(ArchMesh.from_data(data), **kwargs)

    @classmethod
    def from_file(cls, path, **kwargs):
        from pathlib import Path

        path = Path(path)
        if not path.is_file():
            raise ArchDataError("file", f"file not found: {path}")
        return cls.from_data(pyvista().read(path), **kwargs)

    @classmethod
    def from_dict(cls, data, *, mesh_resolver=None, cad_resolver=None, **kwargs):
        data = validate_design(data)
        parts = []
        pv = pyvista()
        constructors = {
            "cube": pv.Cube,
            "sphere": pv.Sphere,
            "cylinder": pv.Cylinder,
            "cone": pv.Cone,
            "plane": pv.Plane,
            "torus": pv.ParametricTorus,
        }
        if "cad" in data:
            from .cad import _parts_from_source

            parts = list(_parts_from_source(data["cad"], data.get("units", "mm"), cad_resolver))
        for raw in data.get("parts", []):
            p = dict(raw)
            spec = p.pop("mesh")
            if "primitive" in spec:
                mesh = ArchMesh.from_data(constructors[spec["primitive"]](**spec.get("params", {})))
            else:
                if "asset" in spec and mesh_resolver is None:
                    raise ArchDataError("asset", "provide mesh_resolver for registered assets")
                path = mesh_resolver(spec["asset"]) if "asset" in spec else spec["file"]
                mesh = ArchMesh.from_file(path)
            if "style" in p:
                p["style"] = construct(ArchStyle, p["style"])
            parts.append(ArchPart(mesh=mesh, **p))
        return cls(
            parts,
            ArchScript.from_dict(data.get("script", {})),
            style=construct(ArchStyle, data["style"]) if "style" in data else None,
            camera=construct(ArchCamera, data["camera"]) if "camera" in data else None,
            labels=[construct(ArchLabel, v) for v in data.get("labels", [])],
            dimensions=[construct(ArchDimension, v) for v in data.get("dimensions", [])],
            units=data.get("units", "mm" if "cad" in data else "model units"),
            **kwargs,
        )

    def _initial(self):
        return {
            p.id: {
                "position": p.position,
                "rotation": p.rotation,
                "scale": p.scale,
                "opacity": (p.style or self.style).opacity,
                "color": (p.style or self.style).color,
                "highlighted": False,
                "visible": True,
                "section": None,
            }
            for p in self.parts
        }

    def geometry_record(self):
        """Portable geometry and preparation identity for Kit/Agent evidence."""
        result = {"fingerprint": self.fingerprint, "meshes": {p.id: p.mesh.fingerprint for p in self.parts}}
        provenance = {p.id: p.mesh.provenance for p in self.parts if p.mesh.provenance}
        if provenance:
            result["provenance"] = provenance
        return result

    def state_at(self, time):
        time = number(time, "time", 0)
        states, camera = self._initial(), self.camera
        for id in states:
            first = next((a for a in self._actions if a.kind in {"show", "hide"} and id in a.targets), None)
            if first is not None and first.kind == "show":
                states[id]["visible"] = False
        for a in self._actions:
            if time < a.at:
                continue
            progress = min(1, (time - a.at) / a.duration)
            if a.easing == "smooth":
                from ..animation import smooth

                progress = smooth(progress)
            o = a.options

            if a.kind in {"spin", "slider_crank"}:
                import numpy as np

                from .mechanical import _poses

                for id, delta in zip(a.targets, _poses(a, progress)):
                    combined = (
                        delta
                        if a.kind == "slider_crank"
                        else np.asarray(states[id].get("mechanical", np.eye(4))) @ delta
                    )
                    states[id]["mechanical"] = tuple(tuple(float(v) for v in row) for row in combined)
                continue

            def blend(old, new, progress=progress):
                if isinstance(old, (tuple, list)):
                    return tuple(x + (y - x) * progress for x, y in zip(old, new))
                return old + (new - old) * progress

            if a.kind == "camera_to":
                target = o["camera"]
                # Camera frame degeneracy is rejected by ArchCamera, before GL calls.
                camera = ArchCamera(
                    blend(camera.position, target.position),
                    blend(camera.focal_point, target.focal_point),
                    blend(camera.up, target.up),
                    target.projection if progress == 1 else camera.projection,
                    blend(camera.zoom, target.zoom),
                    blend(camera.view_angle, target.view_angle),
                )
                continue
            if a.kind == "orbit":
                angle = math.radians(o["degrees"] * progress)
                x, y, z = [camera.position[i] - camera.focal_point[i] for i in range(3)]
                position = (
                    camera.focal_point[0] + x * math.cos(angle) - y * math.sin(angle),
                    camera.focal_point[1] + x * math.sin(angle) + y * math.cos(angle),
                    camera.focal_point[2] + z,
                )
                camera = ArchCamera(
                    position, camera.focal_point, camera.up, camera.projection, camera.zoom, camera.view_angle
                )
                continue
            for id in a.targets:
                s = states[id]
                if a.kind in {"move", "rotate", "scale", "opacity"}:
                    key = {"move": "position", "rotate": "rotation"}.get(a.kind, a.kind)
                    s[key] = blend(s[key], o.get(key, o.get("value")))
                elif a.kind == "explode":
                    dest = tuple(
                        self._parts[id].position[i] + self._parts[id].explode_vector[i] * o["factor"] for i in range(3)
                    )
                    s["position"] = blend(s["position"], dest)
                elif a.kind == "highlight":
                    s["highlighted"] = True
                    from PIL import ImageColor

                    s["color"] = "#" + "".join(
                        f"{round(v):02x}" for v in blend(ImageColor.getrgb(s["color"]), ImageColor.getrgb(o["color"]))
                    )
                elif a.kind in {"hide", "show"}:
                    s["visible"] = a.kind == "show"
                elif a.kind == "section":
                    mesh = self._parts[id].mesh._dataset
                    norm = math.sqrt(sum(v * v for v in o["normal"]))
                    center = world(mesh.center, id, states)
                    start = (
                        s["section"]["origin"]
                        if s["section"]
                        else tuple(center[i] + o["normal"][i] / norm * mesh.length * s["scale"] for i in range(3))
                    )
                    s["section"] = {**o, "origin": blend(start, o["origin"])}
        return {"time": time, "parts": states, "camera": camera}

    def _framing(self):
        import numpy as np

        times = {0, self.duration, *(a.at + a.duration for a in self._actions)}
        centers, radii = [], []
        for time in times:
            for p in self.parts:
                s = self.state_at(time)["parts"][p.id]
                centers.append(world(p.mesh._dataset.center, p.id, {p.id: s}))
                radii.append(max(0.01, p.mesh._dataset.length / 2) * s["scale"])
                # Cover the complete analytic trajectory, including extrema between
                # action endpoints. Existing components keep their previous framing.
                from .mechanical import _travel_bound

                travel = sum(
                    _travel_bound(a, a.targets.index(p.id), p.mesh._dataset.center)
                    for a in self._actions
                    if a.kind in {"spin", "slider_crank"} and p.id in a.targets
                )
                radii[-1] += travel * s["scale"]
        low = np.min([np.array(c) - r for c, r in zip(centers, radii)], axis=0)
        high = np.max([np.array(c) + r for c, r in zip(centers, radii)], axis=0)
        center = (low + high) / 2
        return center, max(0.1, max(float(np.linalg.norm(np.asarray(c) - center)) + r for c, r in zip(centers, radii)))

    def frame_key(self, age):
        t = min(self.duration, self.source_start + number(max(0, age), "age", 0))
        if any(a.at <= t < a.at + a.duration for a in self._actions):
            return t
        return max((a.at + a.duration for a in self._actions if a.at + a.duration <= t), default=0)

    def project_at(self, time, points, *, part=None):
        state = self.state_at(time)
        if part is not None and part not in self._parts:
            raise ArchDataError("part", "unknown projection target")
        return tuple(
            project(
                world(vector(p, "point"), part, state["parts"]),
                state["camera"],
                self.width,
                self.height,
                self.parallel_scale,
            )
            for p in points
        )

    def _annotations(self, time, factor=1):
        state = self.state_at(time)

        def projected(p, part):
            if part and not state["parts"][part]["visible"]:
                return None
            return project(
                world(p, part, state["parts"]), state["camera"], self.width, self.height, self.parallel_scale
            )

        for i, label in enumerate(self.labels):
            point = projected(label.point, label.part)
            if point:
                yield (
                    f"label-{i}",
                    label.text,
                    point,
                    (point[0] + label.offset[0], point[1] + label.offset[1]),
                    label,
                    None,
                )
        for i, dim in enumerate(self.dimensions):
            start, end = projected(dim.start, dim.part), projected(dim.end, dim.part)
            if start and end:
                a, b = world(dim.start, dim.part, state["parts"]), world(dim.end, dim.part, state["parts"])
                distance = math.dist(a, b)
                center = ((start[0] + end[0]) / 2 + dim.offset[0], (start[1] + end[1]) / 2 + dim.offset[1])
                yield f"dimension-{i}", _format_dimension(distance, dim.precision, self.units), start, center, dim, end

    def annotation_overlay(self, time, factor=1):
        image = Image.new("RGBA", (max(1, round(self.width * factor)), max(1, round(self.height * factor))))
        draw = ImageDraw.Draw(image)
        for _, text_value, start, center, item, end in self._annotations(time):
            f = load_font(self.font, max(1, round(item.font_size * factor)))
            c = tuple(v * factor for v in center)
            a = tuple(v * factor for v in start)
            if end:
                b = tuple(v * factor for v in end)
                shift = tuple(v * factor for v in item.offset)
                aa, bb = tuple(a[i] + shift[i] for i in range(2)), tuple(b[i] + shift[i] for i in range(2))
                draw.line([a, aa, bb, b], fill=item.color, width=max(1, round(factor)))
                for x, y in (aa, bb):
                    draw.line(
                        (x - 4 * factor, y - 4 * factor, x + 4 * factor, y + 4 * factor),
                        fill=item.color,
                        width=max(1, round(factor)),
                    )
            else:
                draw.line([a, c], fill=item.color, width=max(1, round(factor)))
                draw.ellipse(
                    (a[0] - 3 * factor, a[1] - 3 * factor, a[0] + 3 * factor, a[1] + 3 * factor), fill=item.color
                )
            box = draw.textbbox(c, text_value, font=f, anchor="mm")
            draw.rectangle(
                (box[0] - 4 * factor, box[1] - 3 * factor, box[2] + 4 * factor, box[3] + 3 * factor),
                fill=(0, 0, 0, 210),
            )
            draw.text(c, text_value, font=f, fill=item.color, anchor="mm")
        return image

    def diagnostics_at(self, time):
        draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        boxes, result = [], []
        for id, value, _, center, item, _ in self._annotations(time):
            b = draw.textbbox(center, value, font=load_font(self.font, round(item.font_size)), anchor="mm")
            b = (b[0] - 4, b[1] - 3, b[2] + 4, b[3] + 3)
            if b[0] < 0 or b[1] < 0 or b[2] > self.width or b[3] > self.height:
                result.append({"code": "ARCH_ANNOTATION_BOUNDS", "element": id, "time": time})
            for other, old in boxes:
                if min(b[2], old[2]) > max(b[0], old[0]) and min(b[3], old[3]) > max(b[1], old[1]):
                    result.append({"code": "ARCH_ANNOTATION_OVERLAP", "elements": [id, other], "time": time})
            boxes.append((id, b))
        return tuple(result)

    def frame_image(self, age, factor=1):
        """Standalone frame with a short-lived session; compositions reuse owned sessions."""
        from .rendering import ArchSession

        with ArchSession(self, factor) as session:
            return session.frame(age)
