"""Structural QA for the silent scene; this module never renders media."""

import math
import random
from itertools import pairwise

from PIL import ImageColor
from scene import CANVAS_SIZE, CHAPTERS, DIAGRAM_BOUNDS, OFFSET, PALETTE, TOTAL_DURATION, VIEWPORT, build_diagram

from faceless_champ import Captions, FlowChamp, FlowDesign, FlowVisual, Image, Rectangle


def _near(a, b, tolerance=1e-7):
    return math.dist(a, b) <= tolerance


def _port(node, state, port_id):
    """Independently calculate a named port using the public recipe and snapshot."""
    port = next(p for p in node.ports if p.id == port_id)
    width, height = node.size
    x, y = {
        "left": (-width / 2, (port.offset - 0.5) * height),
        "right": (width / 2, (port.offset - 0.5) * height),
        "top": ((port.offset - 0.5) * width, -height / 2),
        "bottom": ((port.offset - 0.5) * width, height / 2),
        "center": (0, 0),
    }[port.side]
    if (x or y) and node.symbol in {"circle", "diamond"}:
        divisor = (
            math.hypot(x / (width / 2), y / (height / 2))
            if node.symbol == "circle"
            else abs(x) / (width / 2) + abs(y) / (height / 2)
        )
        x, y = x / divisor, y / divisor
    x, y = x * state["scale"], y * state["scale"]
    angle = math.radians(state["rotation"])
    cx, cy = state["position"]
    return cx + x * math.cos(angle) - y * math.sin(angle), cy + x * math.sin(angle) + y * math.cos(angle)


def _length(path):
    return sum(math.dist(a, b) for a, b in pairwise(path))


def _distance_to_path(point, path):
    result = math.inf
    for a, b in pairwise(path):
        dx, dy = b[0] - a[0], b[1] - a[1]
        span = dx * dx + dy * dy
        progress = max(0, min(1, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / span)) if span else 0
        nearest = a[0] + progress * dx, a[1] + progress * dy
        result = min(result, math.dist(point, nearest))
    return result


def _visible(entry, time):
    return all(
        parent.start <= time
        and (parent.end is None or time < parent.end)
        and parent.state_at(time).get("opacity", 1) > 1e-9
        for parent in (entry, *entry.ancestors())
    )


def _diagnostic_key(snapshot):
    """Warnings vary with geometry and visible membership, not packet positions."""
    elements = tuple(
        (
            name,
            state.get("position"),
            state.get("scale"),
            state.get("rotation"),
            state["opacity"] > 0,
            state["draw"] > 0,
        )
        for name, state in snapshot["elements"].items()
    )
    hidden = tuple(tuple(h["targets"]) for h in snapshot["highlights"] if h["dim"] == 0)
    return elements, hidden


def _sample_times(script):
    times = {i / 4 for i in range(int(TOTAL_DURATION * 4))}
    times.update((0.0, 116.0, 117.0, 118.0, 119.0, 119.999))
    for _, start, end in CHAPTERS:
        times.update((start, (start + end) / 2, end - 0.001))
    for action in script.actions:
        for i in range(len(action.targets)):
            start = action.at + i * action.options.get("stagger", 0)
            times.update((start, start + action.duration / 2, start + action.duration))
        if action.kind == "signal":
            times.update((action.at + 1e-6, action.end - 1e-6))
    return sorted(t for t in times if 0 <= t < TOTAL_DURATION)


def _check_traffic(clip, authored):
    """Inspect signal joins in both directions, including each repeated traversal."""
    actions = [a for a in clip.script.actions if a.kind == "signal"]
    records = authored["traffic"]
    assert len(actions) == len(records), "Every packet action needs an authored traffic record"
    edges = {edge.id: edge for edge in clip.graph.edges}
    joins = 0
    for record in records:
        matching = [
            a
            for a in actions
            if a.targets == tuple(record["edges"])
            and abs(a.at - record["start"]) < 1e-8
            and abs(a.end - record["end"]) < 1e-8
            and a.options.get("direction", "forward") == record["direction"]
            and a.options.get("repeat", 1) == record["repeat"]
        ]
        assert len(matching) == 1, f"Traffic record does not match one action: {record['id']}"
        action = matching[0]
        assert action.options.get("marker") == "capsule", "Traffic should use native capsule markers"
        color = ImageColor.getcolor(action.options.get("color", clip.theme.accent), "RGBA")
        assert color[3] == 255 and color == ImageColor.getcolor(record["color"], "RGBA"), (
            "Native traffic markers need the authored opaque semantic color"
        )
        route = [edges[name] for name in action.targets]
        assert all(a.target == b.source for a, b in pairwise(route)), f"Disconnected traffic: {record['id']}"
        midpoint = clip.state_at(action.at + action.duration / 2)["elements"]
        paths = [midpoint[name]["path"] for name in action.targets]
        spans = [_length(path) for path in paths]
        total = sum(spans)
        assert total > 0, f"Zero-length traffic route: {record['id']}"
        cumulative = 0.0
        for i, (left, right) in enumerate(pairwise(paths)):
            assert _near(left[-1], right[0]), f"Packet would jump between edges: {record['id']}"
            cumulative += spans[i]
            fraction = cumulative / total
            if record["direction"] == "reverse":
                fraction = 1 - fraction
            cycle_duration = action.duration / record["repeat"]
            for cycle in range(record["repeat"]):
                time = action.at + (cycle + fraction) * cycle_duration
                epsilon = min(1e-6, cycle_duration / 10000)
                before, after = clip.state_at(time - epsilon), clip.state_at(time + epsilon)
                a = [s for s in before["signals"] if s["edge"] in action.targets]
                b = [s for s in after["signals"] if s["edge"] in action.targets]
                assert len(a) == len(b) == 1, f"Packet disappears at an edge join: {record['id']}"
                assert math.dist(a[0]["position"], b[0]["position"]) < 0.25, (
                    f"Packet discontinuity at {time:.6f}s: {record['id']}"
                )
                joins += 1
    return joins


def _check_design_assets(entries):
    """Verify installed design artwork is present, without rasterizing it."""
    design = FlowDesign.named("networking")
    packaged = {path.resolve() for path in design.asset_paths}
    assert len(packaged) >= 8 and all(path.is_file() for path in packaged), "Bundled networking icons are missing"
    pack = next(iter(packaged)).parent
    assert pack.name == "networking", "Networking icons must resolve from the installed design assets"
    background = pack / "backdrop.png"
    assert background.is_file(), "The bundled networking background is missing"
    assets = set()
    backgrounds = 0
    rounded_shapes = 0
    for entry in entries:
        component = entry.component
        if isinstance(component, Image) and component.path is not None:
            path = component.path.resolve()
            if path.is_relative_to(pack):
                assert path.is_file() and path.suffix.lower() == ".png", f"Missing pack PNG: {path}"
                assets.add(path.relative_to(pack).as_posix())
                backgrounds += path == background
        if isinstance(component, Rectangle):
            assert component.corner_radius > 0, "UI rectangles need rounded corners"
            rounded_shapes += 1
    assert {path.name for path in packaged} <= assets, "Use all eight approved networking icons"
    assert backgrounds == 1, "The composition needs one bundled design background"
    assert rounded_shapes, "The premium UI needs rounded component surfaces"
    return sorted(assets), rounded_shapes


def _check_card_alignment(cards, states, time, offset):
    checked = 0
    for target, entries in cards.items():
        visible = [entry for entry in entries if _visible(entry, time)]
        assert len(visible) <= 1, f"Duplicate visible card at {time:.6f}s: {target}"
        for entry in visible:
            state = entry.state_at(time)
            node = states[target]
            expected = tuple(value + shift for value, shift in zip(node["position"], offset))
            assert _near(state["position"], expected, tolerance=0.15), (
                f"Card and its connection anchor diverge at {time:.6f}s: {target}"
            )
            assert abs(state["scale"] - node["scale"]) <= 0.001, (
                f"Card pop and its connection scale diverge at {time:.6f}s: {target}"
            )
            checked += 1
    return checked


def _check_contrast():
    """Measure the authored text pairs using relative sRGB luminance."""

    def luminance(value):
        rgb = ImageColor.getcolor(value, "RGB")
        channels = [channel / 255 for channel in rgb]
        linear_rgb = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
        return sum(value * weight for value, weight in zip(linear_rgb, (0.2126, 0.7152, 0.0722)))

    result = {}
    for foreground, background in (
        ("ink", "surface"),
        ("muted", "surface"),
        ("blue", "pale_blue"),
        ("violet", "pale_violet"),
        ("teal", "pale_teal"),
    ):
        light, dark = sorted((luminance(PALETTE[foreground]), luminance(PALETTE[background])), reverse=True)
        ratio = (light + 0.05) / (dark + 0.05)
        assert ratio >= 4.5, f"Text contrast is below 4.5:1 for {foreground}/{background}: {ratio:.3f}"
        result[f"{foreground}/{background}"] = round(ratio, 3)
    return result


def _layout_cache(entries):
    """Measure each immutable root once, then audit its public transform tracks."""
    roots = []
    for entry in entries:
        properties = {track.property for track in entry.tracks}
        if entry.parent is not None:
            assert properties <= {"opacity"}, "A child geometry animation requires a fresh layout audit"
            continue
        assert properties <= {"position", "scale", "opacity"}, "Unsupported animated root geometry"
        initial = entry.initial
        assert initial["rotation"] == 0 and initial.get("scale_x", 1) == initial.get("scale_y", 1) == 1, (
            "The cached layout audit expects uniform root scaling without rotation"
        )
        assert entry.component.anchor == "center", "The cached layout audit expects centered roots"
        box = entry.component.bounds
        x, y = initial["position"]
        scale = initial["scale"]
        local = ((box.left - x) / scale, (box.top - y) / scale, (box.right - x) / scale, (box.bottom - y) / scale)
        roots.append((entry, local))
    return roots


def _root_bounds(entry, local, time):
    state = entry.state_at(time)
    x, y = state["position"]
    scale = state["scale"]
    return {
        "left": x + local[0] * scale,
        "top": y + local[1] * scale,
        "right": x + local[2] * scale,
        "bottom": y + local[3] * scale,
    }


def _check_layout(compiled, entries, times):
    roots = _layout_cache(entries)
    checked, issues, unique = 0, [], set()
    for time in times:
        sample = []
        for entry, local in roots:
            if time < entry.start or (entry.end is not None and time >= entry.end):
                continue
            box = _root_bounds(entry, local, time)
            sample.append(tuple(box.values()))
            checked += 1
            if (
                box["left"] < -1
                or box["top"] < -1
                or box["right"] > CANVAS_SIZE[0] + 1
                or box["bottom"] > CANVAS_SIZE[1] + 1
            ):
                issues.append({"time": time, "id": getattr(entry.component, "training_id", ""), "bounds": box})
        unique.add(tuple(sample))
    assert not issues, f"Components exceed the design canvas: {issues[:5]}"

    public_times = (0.8, 14.8, 34.5, 73.0, 118.0)
    public_boxes = 0
    for time in public_times:
        for placement in compiled.layout_at(time)["placements"]:
            short_id = placement["id"].rsplit("/", 1)[-1]
            candidates = []
            for entry, local in roots:
                if not entry.start <= time or (entry.end is not None and time >= entry.end):
                    continue
                tag = getattr(entry.component, "training_id", "")
                if tag == short_id or (tag.startswith("card-") and short_id.startswith(tag + "-")):
                    candidates.append((entry, local))
            assert len(candidates) == 1, f"Cannot match public layout placement: {placement['id']}"
            entry, local = candidates[0]
            cached = _root_bounds(entry, local, time)
            assert all(abs(cached[key] - placement["bounds"][key]) <= 1e-6 for key in cached), (
                f"Cached bounds differ from public layout_at at {time:.6f}s: {placement['id']}"
            )
            for box in placement["children"].values():
                assert (
                    box["left"] >= cached["left"] - 1e-6
                    and box["top"] >= cached["top"] - 1e-6
                    and box["right"] <= cached["right"] + 1e-6
                    and box["bottom"] <= cached["bottom"] + 1e-6
                ), f"A fixed child exceeds its audited root: {placement['id']}"
            public_boxes += 1
    return checked, len(unique), issues, len(public_times), public_boxes


def check(compiled):
    """Return JSON-safe evidence for the compiled tutorial without rendering it."""
    scene = compiled.composition
    entries = scene.entries
    clips = [entry.component for entry in entries if isinstance(entry.component, FlowChamp)]
    assert len(clips) == 2, "The scene needs a primary connection layer and its matching soft glow"
    primary = [clip for clip in clips if getattr(clip, "training_id", None) == "connections"]
    glows = [clip for clip in clips if getattr(clip, "training_id", None) == "connection-glow"]
    assert len(primary) == len(glows) == 1, "Identify the primary and glow FlowChamp layers"
    clip, glow = primary[0], glows[0]
    assert abs(compiled.duration - TOTAL_DURATION) < 1e-9, "The tutorial must last exactly 120 seconds"
    assert TOTAL_DURATION == 120.0
    assert (scene.canvas.width, scene.canvas.height) == tuple(CANVAS_SIZE) == (1920, 1080)
    assert (clip.width, clip.height) == tuple(VIEWPORT)
    assert not scene.audio, "The tutorial must remain silent"
    assert compiled.report["narration"] is None, "The build must not attach narration"
    assert not compiled.context.captions, "Captions must be disabled"
    assert not any(isinstance(e.component, Captions) for e in entries), "Caption components are not allowed"
    assert len(compiled.report["segments"]) == 1, "The evolving diagram lives in one segment"
    assert not compiled.report["diagnostics"], f"Kit diagnostics: {compiled.report['diagnostics'][:5]}"
    assert clip.graph.layout == "manual", "The tutorial uses an authored stable layout"
    assert all(layer.source_start == 0 for layer in clips), "FlowChamp layers must share the master clock"
    assert clip.theme.font and "dmsans" in clip.theme.font.lower().replace("-", ""), "Use bundled DM Sans"
    for layer in clips:
        assert ImageColor.getcolor(layer.theme.surface, "RGBA")[3] == 0, "Logical node faces must be transparent"
        assert ImageColor.getcolor(layer.theme.node_stroke, "RGBA")[3] == 0, "Logical node outlines must be transparent"
        assert layer.theme.stroke == PALETTE["wire"], "Connections need a persistent neutral base"
        assert layer.theme.highlight_width == 0, "Focus transitions must preserve the cable width"
    assert glow.graph.to_dict() == clip.graph.to_dict(), "The glow must use the same bound graph"
    assert (glow.width, glow.height) == tuple(VIEWPORT), "The glow viewport differs from the primary layer"
    assert not any(action.kind == "signal" for action in glow.script.actions), "The glow must not duplicate packets"
    assert glow.script.to_dict()["actions"] == [
        action for action in clip.script.to_dict()["actions"] if action["kind"] != "signal"
    ], "Both connection layers must use identical geometry timing"
    pack_assets, rounded_shapes = _check_design_assets(entries)
    contrast = _check_contrast()

    graph, authored_script, authored = build_diagram()
    assert graph.to_dict() == clip.graph.to_dict(), "The compiled graph differs from the scene recipe"
    assert authored_script.to_dict() == clip.script.to_dict(), "The compiled script differs from the scene recipe"
    nodes = {node.id: node for node in clip.graph.nodes}
    assert all(node.symbol == "rounded_rectangle" and not node.label for node in nodes.values()), (
        "Flow nodes reserve rounded card faces; labels belong to the asset UI"
    )
    cards = {}
    for entry in entries:
        if getattr(entry.component, "training_id", "").startswith("card-"):
            target = entry.component.training_id.removeprefix("card-")
            cards.setdefault(target, []).append(entry)
    assert set(cards) == set(nodes), "Each logical node needs an authored asset card"
    assert not any(getattr(entry.component, "training_id", "").startswith("packet-") for entry in entries), (
        "Native FlowChamp capsules replace project-local packet overlays"
    )
    clip_entry = next(entry for entry in entries if entry.component is clip)
    assert clip_entry.initial["scale"] == 1, "Card alignment expects the authored 1:1 diagram viewport"
    connections = [
        entry
        for entry in entries
        if isinstance(entry.component, FlowVisual) and getattr(entry.component, "training_id", "") == "connections"
    ]
    assert len(connections) == 1, "The core design must own the two bound connection layers"
    assert connections[0].parent is None and clip_entry.parent is connections[0], (
        "The diagram must inherit its design viewport's world placement"
    )
    assert connections[0].component.face_bounds == DIAGRAM_BOUNDS, "The connection design's world bounds changed"
    offset = tuple(OFFSET)
    for edge in clip.graph.edges:
        assert edge.route == "bezier" and not edge.waypoints, "Connections need automatic Bezier controls"
        assert edge.source_port and edge.target_port, "Connections must bind to named node ports"
    for action in clip.script.actions:
        assert action.at >= 0 and action.end <= TOTAL_DURATION + 1e-9, "Action exceeds the scene clock"
        if action.kind == "draw":
            assert action.options.get("tool") == "none", "Drawing tools must stay hidden"

    times = _sample_times(clip.script)
    diagnostics_cache = {}
    geometry_issues = []
    signal_samples = 0
    card_samples = 0
    for time in times:
        snapshot = clip.state_at(time)
        glow_snapshot = glow.state_at(time)
        assert glow_snapshot["elements"] == snapshot["elements"], f"Glow and primary connections diverge at {time:.6f}s"
        assert not glow_snapshot["signals"] and not glow_snapshot["tools"], "The glow layer adds visual tools"
        assert not snapshot["tools"], f"Visible drawing tool at {time:.6f}s"
        states = snapshot["elements"]
        card_samples += _check_card_alignment(cards, states, time, offset)
        for edge in clip.graph.edges:
            path = states[edge.id]["path"]
            assert len(path) >= 2 and all(math.isfinite(value) for point in path for value in point), (
                f"Invalid connection path at {time:.6f}s: {edge.id}"
            )
            assert _near(path[0], _port(nodes[edge.source], states[edge.source], edge.source_port)), (
                f"Detached source port at {time:.6f}s: {edge.id}"
            )
            assert _near(path[-1], _port(nodes[edge.target], states[edge.target], edge.target_port)), (
                f"Detached target port at {time:.6f}s: {edge.id}"
            )
        for signal in snapshot["signals"]:
            assert signal["marker"] == "capsule", f"Unexpected native traffic marker at {time:.6f}s"
            assert ImageColor.getcolor(signal["color"], "RGBA")[3] == 255, (
                f"Native capsule is transparent at {time:.6f}s"
            )
            assert _distance_to_path(signal["position"], states[signal["edge"]]["path"]) < 1e-6, (
                f"Packet left its connection at {time:.6f}s: {signal['edge']}"
            )
            signal_samples += 1
        active = [a for a in clip.script.actions if a.kind == "signal" and a.at <= time < a.end]
        assert len(snapshot["signals"]) <= len(active), f"Unexpected packet at {time:.6f}s"
        for action in active:
            matching = [signal for signal in snapshot["signals"] if signal["edge"] in action.targets]
            assert len(matching) == 1, f"Packet hidden during active traffic at {time:.6f}s"
            assert ImageColor.getcolor(matching[0]["color"], "RGBA") == ImageColor.getcolor(
                action.options.get("color", clip.theme.accent), "RGBA"
            ), f"Native capsule lost its authored semantic color at {time:.6f}s"
        key = _diagnostic_key(snapshot)
        if key not in diagnostics_cache:
            diagnostics_cache[key] = clip.diagnostics_at(time)
            geometry_issues.extend(diagnostics_cache[key])
    assert not geometry_issues, f"Flow geometry warnings: {geometry_issues[:5]}"

    # Revisit times in shuffled order to prove the public snapshots do not depend
    # on rendering order or on a previous seek.
    seeks = sorted(set(times[:: max(1, len(times) // 30)] + [119.999]))
    references = {time: clip.state_at(time) for time in seeks}
    glow_references = {time: glow.state_at(time) for time in seeks}
    random.Random(4701).shuffle(seeks)
    for time in seeks:
        assert clip.state_at(time) == references[time], f"Nondeterministic seek at {time:.6f}s"
        assert glow.state_at(time) == glow_references[time], f"Nondeterministic glow seek at {time:.6f}s"

    for move in authored["moves"]:
        target = move["target"]
        assert _near(clip.state_at(move["start"])["elements"][target]["position"], move["source"]), (
            f"Move starts from the wrong position: {target}"
        )
        assert _near(clip.state_at(move["end"])["elements"][target]["position"], move["destination"]), (
            f"Move ends at the wrong position: {target}"
        )

    layout_checked, layout_samples, layout_issues, public_layout_samples, public_layout_boxes = _check_layout(
        compiled, entries, times
    )

    final = clip.state_at(116.0)
    final_glow = glow.state_at(116.0)
    assert not final["signals"] and not final["tools"], "The final hold must be quiet"
    for time in (116.5, 117.0, 118.0, 119.0, 119.999):
        assert clip.state_at(time) == final, "The completed diagram changes during its final hold"
        assert glow.state_at(time) == final_glow, "The connection glow changes during its final hold"
        for entry in entries:
            if _visible(entry, 116.0):
                assert _visible(entry, time) and entry.state_at(time) == entry.state_at(116.0), (
                    "An overlay changes during the final hold"
                )

    joins = _check_traffic(clip, authored)
    return {
        "ok": True,
        "duration": compiled.duration,
        "canvas": list(CANVAS_SIZE),
        "flow_viewport": list(VIEWPORT),
        "audio_tracks": len(scene.audio),
        "captions": False,
        "design_revision": 2,
        "library_design": "networking",
        "reusable_design_in_library": True,
        "asset_pack": "Networking_UI_Pack_assets",
        "pack_assets": pack_assets,
        "rounded_shapes_checked": rounded_shapes,
        "text_contrast_ratios": contrast,
        "minimum_text_contrast": 4.5,
        "chapters": [{"id": name, "start": start, "end": end} for name, start, end in CHAPTERS],
        "continuous_flow_clips": len(clips),
        "continuous_logical_diagrams": 1,
        "connection_layers": len(clips),
        "nodes": len(nodes),
        "connections": len(clip.graph.edges),
        "actions": len(clip.script.actions),
        "geometry_samples": len(times),
        "unique_geometry_diagnostics": len(diagnostics_cache),
        "geometry_issues": geometry_issues,
        "layout_boxes_checked": layout_checked,
        "unique_layout_samples": layout_samples,
        "public_layout_crosschecks": public_layout_samples,
        "public_layout_boxes_checked": public_layout_boxes,
        "layout_issues": layout_issues,
        "packet_samples": signal_samples,
        "card_anchor_samples": card_samples,
        "visible_capsule_samples": signal_samples,
        "packet_start_precision_samples": 0,
        "packet_start_tolerance_seconds": 0,
        "packet_join_samples": joins,
        "traffic_actions": len(authored["traffic"]),
        "eased_moves": len(authored["moves"]),
        "deterministic_seeks": len(seeks),
        "final_hold": {"start": 116.0, "end": 120.0, "verified": True},
        "media_rendered": False,
        "visual_review": "approved design; library migration not rendered",
        "full_export_verified": False,
        "limitations": [],
    }
