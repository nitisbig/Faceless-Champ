"""Acceptance checks against source inputs and every encoded-frame geometry state."""

import hashlib
import itertools
import math

import numpy as np

from faceless_champ import Arrow, Equation, Group, Number, PillowRenderer, SubtitleTrack, Text
from faceless_champ.layout import _size

from .design_v2 import PALETTE, SAFE, SURFACE

SOURCE_HASHES = {
    "audio.mp3": "396814cccc3fcf3d84942980e140659a4cbb0fdb63c50835893f04b34bef3256",
    "cue-per-word.srt": "1edb26d6ec2d8a3aa3560829630eabb99fcd3c6dcb62308bc3aab8f70444b254",
}


def luminance(color):
    rgb = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    return sum(x * y for x, y in zip(linear, (0.2126, 0.7152, 0.0722)))


def check(compiled):
    report = compiled.report
    for name, digest in SOURCE_HASHES.items():
        actual = hashlib.sha256((compiled.context.root / name).read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError(f"Original source changed: {name}")
    cues = report["narration"]["cues"]
    if len(cues) != 1379:
        raise ValueError("Expected all 1,379 original cues")
    original = SubtitleTrack.from_srt(compiled.context.root / "cue-per-word.srt", overlap_tolerance=0.001)
    if cues != [{"index": c.index, "start": c.start, "end": c.end} for c in original.cues]:
        raise ValueError("Reported cue timing differs from the source")
    overlaps = [(a["index"], b["index"]) for a, b in itertools.pairwise(cues) if a["end"] > b["start"]]
    if overlaps != [(811, 812), (987, 988), (1102, 1103), (1142, 1143), (1247, 1248), (1248, 1249)]:
        raise ValueError("Original tiny overlaps changed")
    shots = report["visual_events"]
    if shots[0]["start"] != 0 or abs(shots[-1]["end"] - compiled.duration) > 1e-8:
        raise ValueError("Visuals do not cover lead-in and audio tail")
    for left, right in itertools.pairwise(shots):
        if abs(left["end"] - right["start"]) > 1e-8:
            raise ValueError("Gap or overlap between shots")
    events = sorted({t for s in shots for t in s["attention"]})
    gaps = [b - a for a, b in zip(events, events[1:] + [compiled.duration])]
    if max(gaps) > 3 + 1e-8:
        raise ValueError(f"Attention-event gap exceeds 3s: {max(gaps):.3f}")
    scene = compiled.composition
    if len(scene.audio) != 1 or scene.audio[0].start != 0:
        raise ValueError("Expected one narration track at master zero")
    if scene.canvas.bg != "#000000":
        raise ValueError("Background must be pure black")
    contrast = {name: round((luminance(color) + 0.05) / 0.05, 3) for name, color in PALETTE.items()}
    surface_contrast = {
        name: round((luminance(color) + 0.05) / (luminance(SURFACE) + 0.05), 3) for name, color in PALETTE.items()
    }
    if min(surface_contrast.values()) < 4.5:
        raise ValueError("Palette text contrast below 4.5:1")
    for entry in scene.entries:
        c = entry.component
        if isinstance(c, (Text, Equation)) and c.font_size < 32:
            raise ValueError("Text below minimum design size")
    return {
        "passed": True,
        "source_checksums": SOURCE_HASHES,
        "cue_count": len(cues),
        "preserved_overlaps": overlaps,
        "shot_count": len(shots),
        "attention_event_count": len(events),
        "maximum_attention_gap": round(max(gaps), 6),
        "duration": compiled.duration,
        "contrast_on_black": contrast,
        "contrast_on_surfaces": surface_contrast,
    }


def property_values(entry, name, times):
    initial = entry.initial[name]
    values = (
        np.tile(initial, (len(times), 1)) if isinstance(initial, tuple) else np.full(len(times), initial, dtype=float)
    )
    for track in entry.tracks:
        if track.property != name:
            continue
        selected = times >= track.start
        values[selected] = [track.value_at(t) for t in times[selected]]
    return values


def world_matrix(entry, times, cache):
    key = id(entry)
    if key in cache:
        return cache[key]
    pos = property_values(entry, "position", times)
    scale = property_values(entry, "scale", times)
    sx = scale * property_values(entry, "scale_x", times)
    sy = scale * property_values(entry, "scale_y", times)
    r = np.deg2rad(property_values(entry, "rotation", times))
    co, si = np.cos(r), np.sin(r)
    result = np.zeros((len(times), 3, 3))
    result[:, 0, 0] = co * sx
    result[:, 0, 1] = -si * sy
    result[:, 1, 0] = si * sx
    result[:, 1, 1] = co * sy
    origin = entry.component._origin if isinstance(entry.component, Group) else (0, 0)
    result[:, 0, 2] = pos[:, 0] - result[:, 0, 0] * origin[0] - result[:, 0, 1] * origin[1]
    result[:, 1, 2] = pos[:, 1] - result[:, 1, 0] * origin[0] - result[:, 1, 1] * origin[1]
    result[:, 2, 2] = 1
    if entry.parent is not None:
        result = np.matmul(world_matrix(entry.parent, times, cache), result)
    cache[key] = result
    return result


def effective_opacity(entry, times):
    value = property_values(entry, "opacity", times)
    value[(times < entry.start) | (times >= (entry.end if entry.end is not None else float("inf")))] = 0
    for ancestor in entry.ancestors():
        value *= property_values(ancestor, "opacity", times)
        value[(times < ancestor.start) | (times >= (ancestor.end if ancestor.end is not None else float("inf")))] = 0
    return value


def intersects(a, b, gap=0):
    return (a[:, 0] < b[:, 2] + gap) & (a[:, 2] + gap > b[:, 0]) & (a[:, 1] < b[:, 3] + gap) & (a[:, 3] + gap > b[:, 1])


def segment_hits_box(p, q, boxes):
    """Exact line/rectangle intersection; unlike a diagonal line's bounding box."""
    d = q - p
    lower = np.zeros(len(boxes))
    upper = np.ones(len(boxes))
    possible = np.ones(len(boxes), dtype=bool)
    for axis in (0, 1):
        flat = np.abs(d[:, axis]) < 1e-9
        possible &= ~flat | ((p[:, axis] >= boxes[:, axis]) & (p[:, axis] <= boxes[:, axis + 2]))
        denominator = np.where(flat, 1, d[:, axis])
        one = (boxes[:, axis] - p[:, axis]) / denominator
        two = (boxes[:, axis + 2] - p[:, axis]) / denominator
        lower = np.maximum(lower, np.where(flat, 0, np.minimum(one, two)))
        upper = np.minimum(upper, np.where(flat, 1, np.maximum(one, two)))
    return possible & (lower <= upper)


def audit_layout(compiled, fps=30):
    base = check(compiled)
    renderer = PillowRenderer(1, frame_cache_mb=0, caption_cache_mb=0)
    renderer.validate(compiled.composition)
    count = math.ceil(compiled.duration * fps - 1e-9)
    all_times = np.arange(count) / fps
    scene = compiled.composition
    issues = []
    checked = 0
    pairs = 0
    for shot in compiled.report["visual_events"]:
        times = all_times[(all_times >= shot["start"] - 1e-9) & (all_times < shot["end"] - 1e-9)]
        if not len(times):
            continue
        leaves = [
            e
            for e in scene.entries
            if not isinstance(e.component, Group)
            and e.start < shot["end"]
            and (e.end is None or e.end > shot["start"])
            and any(effective_opacity(e, times) > 0.01)
        ]
        matrices = {}
        data = []
        for entry in leaves:
            c = entry.component
            w, h = _size(c, renderer)
            # Fixed number widths reserve all intermediate digits. Their line height
            # includes the widest digit sample, not just the initial small number.
            if isinstance(c, Number):
                state = c.state()
                state["value"] = 88888888
                try:
                    h = max(h, renderer._sprite(c, state, 1, 0).height)
                except ValueError:
                    pass
            corners = np.array([[-w / 2, -h / 2, 1], [w / 2, -h / 2, 1], [w / 2, h / 2, 1], [-w / 2, h / 2, 1]])
            matrix = world_matrix(entry, times, matrices)
            points = np.einsum("nij,kj->nki", matrix, corners)
            box = np.column_stack(
                (
                    points[:, :, 0].min(axis=1),
                    points[:, :, 1].min(axis=1),
                    points[:, :, 0].max(axis=1),
                    points[:, :, 1].max(axis=1),
                )
            )
            visible = effective_opacity(entry, times) > 0.01
            outside = visible & (
                (box[:, 0] < SAFE.left) | (box[:, 1] < SAFE.top) | (box[:, 2] > SAFE.right) | (box[:, 3] > SAFE.bottom)
            )
            if outside.any():
                index = np.flatnonzero(outside)[0]
                issues.append(
                    {
                        "kind": "margin",
                        "time": float(times[index]),
                        "object": getattr(c, "audit_name", type(c).__name__),
                        "bounds": box[index].tolist(),
                    }
                )
            data.append((entry, box, visible, matrix))
            checked += len(times)
        labels = [d for d in data if getattr(d[0].component, "audit_role", None) == "label"]
        solids = [d for d in data if getattr(d[0].component, "audit_role", None) in {"surface", "graphic", "token"}]
        connectors = [d for d in data if getattr(d[0].component, "audit_role", None) == "connector"]
        for i, left in enumerate(labels):
            for right in labels[i + 1 :] + solids:
                lc, rc = left[0].component, right[0].component
                if getattr(rc, "audit_role", None) != "label" and lc.audit_owner == rc.audit_owner:
                    continue  # Documented label containment and icon layering.
                overlap = left[2] & right[2] & intersects(left[1], right[1], gap=2)
                pairs += len(times)
                if overlap.any():
                    issues.append(
                        {
                            "kind": "collision",
                            "time": float(times[np.flatnonzero(overlap)[0]]),
                            "objects": [lc.audit_name, rc.audit_name or type(rc).__name__],
                        }
                    )
            for edge, _, visible, matrix in connectors:
                c = edge.component
                if hasattr(c, "points"):
                    pts = [(x - c.width / 2, y - c.height / 2, 1) for x, y in c.points]
                elif isinstance(c, Arrow):
                    pts = [(-c.width / 2, 0, 1), (c.width / 2, 0, 1)]
                else:
                    continue
                for p, q in itertools.pairwise(pts):
                    pp = np.einsum("nij,j->ni", matrix, p)[:, :2]
                    qq = np.einsum("nij,j->ni", matrix, q)[:, :2]
                    overlap = left[2] & visible & segment_hits_box(pp, qq, left[1])
                    if overlap.any():
                        issues.append(
                            {
                                "kind": "connector-label",
                                "time": float(times[np.flatnonzero(overlap)[0]]),
                                "object": left[0].component.audit_name,
                            }
                        )
                        break
        print(f"  audit {shot['start']:.3f}–{shot['end']:.3f}s / {len(times)} frame states", flush=True)
    result = base | {
        "fps": fps,
        "frames_checked": count,
        "component_frame_states": checked,
        "collision_pair_frame_states": pairs,
        "issues": issues,
        "passed": not issues,
        "allowances": ["same-owner label containment", "depth silhouettes", "halos", "connector/node joins"],
    }
    if issues:
        import json

        (compiled.context.root / "output/layout-audit-v2.json").write_text(json.dumps(result, indent=2) + "\n")
        raise ValueError(f"Layout audit found {len(issues)} issues; see output/layout-audit-v2.json")
    return result
