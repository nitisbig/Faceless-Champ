"""Explicitly timed 3D demonstration tracks with immutable arguments."""

from copy import deepcopy
from dataclasses import dataclass

from .camera import ArchCamera
from .model import ArchDataError, color, construct, number, vector


@dataclass(frozen=True)
class ArchAction:
    kind: str
    targets: tuple
    at: float
    duration: float
    args: tuple

    @property
    def options(self):
        return dict(self.args)


PROPERTIES = {
    "move": "position",
    "explode": "position",
    "camera_to": "camera",
    "orbit": "camera",
    "hide": "visible",
    "show": "visible",
}
OPTIONS = {
    "move": {"position"},
    "rotate": {"rotation"},
    "scale": {"value"},
    "opacity": {"value"},
    "explode": {"factor"},
    "highlight": {"color"},
    "show": set(),
    "hide": set(),
    "camera_to": {"camera"},
    "orbit": {"degrees"},
    "section": {"origin", "normal", "cap", "contour"},
}


class ArchScript:
    def __init__(self):
        self._actions = []
        self._hold = 0

    @property
    def actions(self):
        return tuple(self._actions)

    @property
    def duration(self):
        return max(self._hold, max((a.at + a.duration for a in self.actions), default=0))

    def wait(self, duration=1):
        self._hold = self.duration + number(duration, "wait", 0)
        return self

    def _add(self, kind, targets, *, at=None, duration=1, **options):
        if set(options) != OPTIONS[kind]:
            raise ArchDataError("action", "unknown or missing action options")
        targets = (targets,) if isinstance(targets, str) else tuple(targets)
        if not targets or len(set(targets)) != len(targets) or any(not isinstance(t, str) or not t for t in targets):
            raise ArchDataError("targets", "expected unique nonempty target IDs")
        at = self.duration if at is None else number(at, "at", 0)
        duration = number(duration, "duration", 0.000001)
        for old in self.actions:
            if (
                PROPERTIES.get(old.kind, old.kind) == PROPERTIES.get(kind, kind)
                and set(old.targets) & set(targets)
                and max(at, old.at) < min(at + duration, old.at + old.duration) - 1e-9
            ):
                raise ArchDataError("actions", f"conflicting {kind} tracks")
        self._actions.append(ArchAction(kind, targets, at, duration, tuple(sorted(deepcopy(options).items()))))
        return self

    def move(self, targets, position, **timing):
        return self._add("move", targets, position=vector(position, "position"), **timing)

    def rotate(self, targets, rotation, **timing):
        return self._add("rotate", targets, rotation=vector(rotation, "rotation"), **timing)

    def scale(self, targets, value, **timing):
        return self._add("scale", targets, value=number(value, "scale", 0.000001), **timing)

    def opacity(self, targets, value, **timing):
        value = number(value, "opacity", 0)
        if value > 1:
            raise ArchDataError("opacity", "must be <= 1")
        return self._add("opacity", targets, value=value, **timing)

    def explode(self, targets, factor=1, **timing):
        return self._add("explode", targets, factor=number(factor, "factor"), **timing)

    def highlight(self, targets, color_value="#ffcc66", **timing):
        return self._add("highlight", targets, color=color(color_value), **timing)

    def hide(self, targets, **timing):
        return self._add("hide", targets, **timing)

    def show(self, targets, **timing):
        return self._add("show", targets, **timing)

    def camera_to(self, camera, **timing):
        if not isinstance(camera, ArchCamera):
            raise ArchDataError("camera", "expected ArchCamera")
        return self._add("camera_to", "camera", camera=camera, **timing)

    def orbit(self, degrees=90, **timing):
        return self._add("orbit", "camera", degrees=number(degrees, "degrees"), **timing)

    def section(self, targets, origin, normal=(1, 0, 0), *, cap=False, contour=True, **timing):
        normal = vector(normal, "normal")
        if not any(normal) or not isinstance(cap, bool) or not isinstance(contour, bool):
            raise ArchDataError("section", "expected nonzero normal and boolean cap/contour")
        return self._add(
            "section", targets, origin=vector(origin, "origin"), normal=normal, cap=cap, contour=contour, **timing
        )

    def to_dict(self):
        from dataclasses import asdict

        return {
            "actions": [
                {
                    "kind": a.kind,
                    "targets": list(a.targets),
                    "at": a.at,
                    "duration": a.duration,
                    **{k: asdict(v) if isinstance(v, ArchCamera) else v for k, v in a.options.items()},
                }
                for a in self.actions
            ],
            "duration": self.duration,
        }

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or set(data) - {"actions", "duration"}:
            raise ArchDataError("script", "expected actions and optional duration")
        result = cls()
        allowed = {
            "move",
            "rotate",
            "scale",
            "opacity",
            "explode",
            "highlight",
            "hide",
            "show",
            "camera_to",
            "orbit",
            "section",
        }
        if not isinstance(data.get("actions", []), (list, tuple)):
            raise ArchDataError("actions", "expected array")
        for raw in data.get("actions", []):
            if not isinstance(raw, dict):
                raise ArchDataError("action", "expected object")
            action = deepcopy(raw)
            kind = action.pop("kind", None)
            targets = action.pop("targets", ["camera"])
            if kind not in allowed:
                raise ArchDataError("action.kind", "unknown action")
            if kind in {"camera_to", "orbit"} and targets not in (["camera"], ("camera",), "camera"):
                raise ArchDataError("targets", "camera actions require camera target")
            if "camera" in action:
                action["camera"] = construct(ArchCamera, action["camera"])
            if kind == "highlight" and "color" in action:
                action["color_value"] = action.pop("color")
            try:
                getattr(result, kind)(**action) if kind in {"camera_to", "orbit"} else getattr(result, kind)(
                    targets, **action
                )
            except TypeError as exc:
                raise ArchDataError("action", str(exc)) from exc
        if "duration" in data:
            result._hold = number(data["duration"], "duration", result.duration)
        return result
