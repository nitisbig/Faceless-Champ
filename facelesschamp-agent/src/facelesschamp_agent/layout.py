"""Bounded, deterministic layout checks in source-clock design pixels.

These are geometric checks, not a substitute for inspecting decoded frames.
Only explicitly named overlap pairs suppress content collisions. Decorative
surfaces containing content and placement parent/child unions are structural.
"""

import math
from bisect import bisect_left
from itertools import combinations

from .errors import AgentError

_TOLERANCE = 1.0
_SURFACES = {"surface", "background", "backdrop"}
_BACKGROUNDS = {"background", "backdrop"}
_LIMITATIONS = [
    "Sampled conservative bounds cannot prove collision-free motion between samples.",
    "Opacity and masks do not shrink bounds; inspect decoded frames for visual quality.",
    "Opaque widget internals rely on their compiler diagnostics; unnamed descendants are not separately audited.",
]


def _value(record, name, default=None):
    return record.get(name, default) if isinstance(record, dict) else getattr(record, name, default)


def _box(bounds):
    return {key: float(_value(bounds, key)) for key in ("left", "top", "right", "bottom")}


def _contains(outer, inner, tolerance=_TOLERANCE):
    return (
        outer["left"] - tolerance <= inner["left"]
        and outer["top"] - tolerance <= inner["top"]
        and outer["right"] + tolerance >= inner["right"]
        and outer["bottom"] + tolerance >= inner["bottom"]
    )


def _intersects(left, right):
    return (
        min(left["right"], right["right"]) - max(left["left"], right["left"]) > _TOLERANCE
        and min(left["bottom"], right["bottom"]) - max(left["top"], right["top"]) > _TOLERANCE
    )


def _name(identifier):
    return identifier.rsplit("/", 1)[-1].lower().replace("-", "_")


def _grid(start, end, *, frequency=12, maximum=181):
    if end <= start:
        return [start]
    count = min(maximum - 1, max(1, math.ceil((end - start) * frequency)))
    return [start + (end - start) * i / count for i in range(count + 1)]


def layout_sample_times(compiled, plan):
    """Scene, transition, track and key-event samples, always before duration.

    Static scenes use at most 17 uniform samples each at one sample per second.
    Overlapping geometry-motion windows share a dense 12 Hz grid (at most 61
    samples per continuous interval). Every event, track boundary and keyframe
    retains its exact before/at/after samples, including very short scenes.
    """
    duration = float(compiled.duration)
    if not math.isfinite(duration) or duration <= 0:
        raise AgentError("LAYOUT_TIME", "Layout audit requires a positive finite composition duration")
    times = set()
    uniform = set()
    motion_windows = []

    def boundary(time, low=0.0, high=duration):
        for point in (math.nextafter(time, -math.inf), time, time - 1 / 120, time + 1 / 120):
            if low <= point < high and 0 <= point < duration:
                times.add(point)

    for scene in plan.scenes:
        start = float(scene.start)
        end = min(duration, start + float(scene.duration))
        uniform.update(t for t in _grid(start, end, frequency=1, maximum=17) if 0 <= t < duration and start <= t < end)
        boundary(start)
        boundary(end)
        for event in scene.key_events:
            at = start + float(event.at)
            boundary(at, start, end)
            boundary(at + float(event.duration), start, end)
            middle = at + float(event.duration) / 2
            if start <= middle < end:
                times.add(middle)
    for segment in compiled.report.get("segments", []):
        for placement in segment.get("placements", []):
            start, end = placement.get("start", segment["start"]), placement.get("end", segment["end"])
            for left, right, geometric in (
                (start, start + placement.get("enter_duration", 0), placement.get("enter") in {"flow", "pop"}),
                (end - placement.get("exit_duration", 0), end, placement.get("exit") == "flow"),
            ):
                boundary(left)
                boundary(right)
                if geometric and right > left:
                    motion_windows.append((left, right))
    for entry in getattr(compiled.composition, "entries", []):
        boundary(entry.start)
        if entry.end is not None:
            boundary(entry.end)
        for track in entry.tracks:
            # Opacity does not shrink layout_at's conservative reserved bounds.
            # Placement/event boundaries already cover its visual transition.
            if getattr(track, "property", None) == "opacity":
                continue
            start, end = float(track.start), float(track.start + track.duration)
            boundary(start)
            boundary(end)
            motion_windows.append((start, end))
            for progress, _ in track.keyframes or ():
                boundary(start + progress * track.duration)
    merged = []
    for start, end in sorted(motion_windows):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    for start, end in merged:
        uniform.update(t for t in _grid(start, end, maximum=61) if 0 <= t < duration)
    # Float arithmetic can generate several almost identical grid points. Keep
    # every required boundary (nextafter is intentional), but omit redundant
    # uniform points beside them.
    required = sorted(times)
    for time in uniform:
        index = bisect_left(required, time)
        neighbors = required[max(0, index - 1) : index + 1]
        if not any(abs(time - other) < 1e-9 for other in neighbors):
            times.add(time)
    return sorted(times)


def audit_layout(compiled, plan, *, times=None):
    """Return a compact report with concrete repairs; never change scene code.

    ``intentional_overlaps`` contains exact pairs of placement or
    ``placement/child`` IDs. ``allow_bleed`` permits specified IDs to extend into
    the safe margin, while canvas clipping is still an error. Unknown explicit
    allowances fail so misspelled or stale exceptions cannot silently pass.
    """
    duration = float(compiled.duration)
    if times is None:
        samples = layout_sample_times(compiled, plan)
    else:
        samples = []
        for time in times:
            if isinstance(time, bool):
                raise AgentError("LAYOUT_TIME", "Sample times must be finite numbers before composition end")
            try:
                time = float(time)
            except (ValueError, TypeError) as exc:
                raise AgentError("LAYOUT_TIME", "Sample times must be finite numbers") from exc
            if not math.isfinite(time) or not 0 <= time < duration:
                raise AgentError("LAYOUT_TIME", "Sample times must be finite numbers before composition end")
            samples.append(time)
        samples = sorted(set(samples))
        if not samples:
            raise AgentError("LAYOUT_TIME", "Supply at least one sample time")
    canvas = compiled.composition.canvas
    canvas_box = {"left": 0.0, "top": 0.0, "right": float(canvas.width), "bottom": float(canvas.height)}
    safe_box = _box(compiled.context.bounds)
    scenes = {scene.id: scene for scene in plan.scenes}
    segments = {segment["id"]: segment for segment in compiled.report.get("segments", [])}
    findings = {}
    observed_scenes = set()

    def add(code, time, scene_id, elements, observed, repair, *, severity="error", **details):
        elements = sorted(set(elements))
        key = (code, scene_id, tuple(elements), severity)
        if key in findings:
            findings[key]["last_source_time"] = max(findings[key]["last_source_time"], float(time))
            findings[key]["occurrences"] += 1
            return
        findings[key] = {
            "code": code,
            "source_time": float(time),
            "last_source_time": float(time),
            "scene_id": scene_id,
            "elements": elements,
            "severity": severity,
            "observed": observed,
            "suggested_repair": repair,
            "occurrences": 1,
            **details,
        }

    allowances, bleed = {}, {}
    for scene in plan.scenes:
        placements = segments.get(scene.id, {}).get("placements", [])
        known = {p["id"] for p in placements}
        known |= {f"{p['id']}/{child}" for p in placements for child in p.get("children", [])}
        allowances[scene.id] = {frozenset(pair) for pair in _value(scene, "intentional_overlaps", [])}
        bleed[scene.id] = set(_value(scene, "allow_bleed", []))
        explicit = set().union(*allowances[scene.id]) if allowances[scene.id] else set()
        for identifier in sorted((explicit | bleed[scene.id]) - known):
            add(
                "LAYOUT_ALLOWANCE_UNKNOWN",
                scene.start,
                scene.id,
                [identifier],
                "Layout exception does not reference a compiled placement or named child.",
                "Use an existing placement or placement/child ID from the build report.",
            )

    def allowed(left, right, scene_ids):
        pairs = {
            frozenset((a, b))
            for a in (left["id"], left["placement"])
            for b in (right["id"], right["placement"])
            if a != b
        }
        return any(pairs & allowances.get(scene_id, set()) for scene_id in scene_ids)

    def structural(left, right):
        if left["placement"] == right["placement"] and (
            left["id"] in right["ancestors"] or right["id"] in left["ancestors"]
        ):
            return True
        # Exact surface targets are part of the kit's card/widget contracts.
        # Cross-placement decoration is limited to a containing background;
        # ordinary panels must declare their intended cross-placement overlap.
        return any(
            outer["named_child"]
            and _name(outer["id"]) in (_SURFACES if outer["placement"] == inner["placement"] else _BACKGROUNDS)
            and _contains(outer["bounds"], inner["bounds"])
            for outer, inner in ((left, right), (right, left))
        )

    for time in samples:
        layout = compiled.layout_at(time)
        leaves = []
        active = {s.id for s in plan.scenes if s.start <= time < s.start + s.duration}
        observed_scenes.update(active)
        for placement in layout.get("placements", []):
            scene_id = placement["segment"]
            observed_scenes.add(scene_id)
            root = {"id": placement["id"], "placement": placement["id"], "scene_id": scene_id}
            children = placement.get("children", {})
            named_parents = {
                ancestor for values in placement.get("child_ancestors", {}).values() for ancestor in values
            }
            boxes = [(placement["id"], placement["bounds"])] + [
                (f"{placement['id']}/{child}", box) for child, box in children.items()
            ]
            for identifier, box in boxes:
                box = _box(box)
                if (
                    not all(math.isfinite(v) for v in box.values())
                    or box["right"] < box["left"]
                    or box["bottom"] < box["top"]
                ):
                    add(
                        "LAYOUT_BOUNDS_INVALID",
                        time,
                        scene_id,
                        [identifier],
                        "Bounds are invalid or non-finite.",
                        "Repair the element geometry and animation values before rendering.",
                    )
                    continue
                ink = (
                    placement.get("ink_bounds", box)
                    if identifier == placement["id"]
                    else (placement.get("child_ink_bounds", {}).get(identifier.split("/", 1)[-1], box))
                )
                if not _contains(canvas_box, _box(ink)):
                    add(
                        "LAYOUT_CANVAS_OVERFLOW",
                        time,
                        scene_id,
                        [identifier],
                        "Element bounds extend beyond the output canvas and may be clipped.",
                        "Move or uniformly scale the element to fit the canvas throughout its motion.",
                        bounds=box,
                    )
                is_background = (identifier != placement["id"] and _name(identifier) in _BACKGROUNDS) or (
                    identifier == placement["id"] and children and all(_name(name) in _BACKGROUNDS for name in children)
                )
                is_bleed = identifier in bleed.get(scene_id, set()) or placement["id"] in bleed.get(scene_id, set())
                if not is_background and not is_bleed and not _contains(safe_box, box):
                    add(
                        "LAYOUT_SAFE_OVERFLOW",
                        time,
                        scene_id,
                        [identifier],
                        "Element bounds extend into the reserved safe or caption area.",
                        "Reflow inside the content bounds or declare the exact intended allow_bleed ID.",
                        bounds=box,
                    )
                if identifier != placement["id"] or not children:
                    child = identifier.removeprefix(placement["id"] + "/")
                    if child in named_parents:
                        continue
                    leaves.append(
                        {
                            **root,
                            "id": identifier,
                            "bounds": box,
                            "named_child": identifier != placement["id"],
                            "ancestors": [
                                f"{placement['id']}/{name}"
                                for name in placement.get("child_ancestors", {}).get(child, [])
                            ],
                        }
                    )
        for left, right in combinations(leaves, 2):
            if not _intersects(left["bounds"], right["bounds"]):
                continue
            scene_ids = {left["scene_id"], right["scene_id"]}
            if allowed(left, right, scene_ids) or structural(left, right):
                continue
            add(
                "LAYOUT_OVERLAP",
                time,
                left["scene_id"],
                [left["id"], right["id"]],
                "Conservative content bounds overlap at a sampled source time.",
                "Increase spacing, reflow or resize the elements; declare an exact intentional_overlaps pair only after visual review.",
            )
        for scene_id in active:
            if not any(row.get("segment") == scene_id for row in layout.get("placements", [])):
                add(
                    "LAYOUT_NO_PLACEMENTS",
                    time,
                    scene_id,
                    [],
                    "No auditable kit placement is active in this scene at the sampled time.",
                    "Inspect the frame and register named kit handles for authored content.",
                )

    for item in compiled.report.get("diagnostics", []):
        code = item.get("code", "")
        if not any(term in code.upper() for term in ("BOUND", "OVERFLOW", "OVERLAP", "CLIP", "TEXT_FIT")):
            continue
        scene_id = item.get("segment")
        if scene_id not in scenes:
            continue
        scene = scenes[scene_id]
        time = item.get("source_time", scene.start)
        placement = item.get("placement", "")
        elements = item.get("elements", [item["element"]] if item.get("element") else [placement])
        elements = [f"{placement}/{e}" if placement and e != placement else e for e in elements]
        if "OVERLAP" in code.upper() and len(elements) == 2:
            candidates = [{"id": element, "placement": placement, "scene_id": scene_id} for element in elements]
            if allowed(*candidates, {scene_id}):
                continue
        add(
            code,
            time,
            scene_id,
            elements,
            "The engine reported an internal layout diagnostic.",
            "Repair the referenced node, label or widget allocation and rerun the audit.",
            diagnostic=item,
        )
    values = sorted(
        findings.values(), key=lambda item: (item["source_time"], item["scene_id"], item["code"], item["elements"])
    )
    missing = sorted(set(scenes) - observed_scenes)
    for scene_id in missing:
        scene = scenes[scene_id]
        add(
            "LAYOUT_SCENE_UNSAMPLED",
            scene.start,
            scene_id,
            [],
            "The supplied sample times do not cover this planned scene.",
            "Include at least one source time from every scene or use the default sampler.",
        )
    if missing:
        values = sorted(findings.values(), key=lambda item: (item["source_time"], item["scene_id"], item["code"]))
    return {
        "status": "failed" if any(f["severity"] == "error" for f in values) else "passed",
        "sample_times": samples,
        "scene_ids": sorted(observed_scenes),
        "findings": values,
        "canvas": canvas_box,
        "safe_bounds": safe_box,
        "conservative": True,
        "full_export_verified": False,
        "limitations": list(_LIMITATIONS),
    }
