"""Structural, timing, feature and layout checks for the actual compiled tour."""

from facelesschamp_kit.compiler import descendants
from videos.main import FEATURES, NOMINAL_SCENES, OVERLAP, TOTAL_DURATION, scene_windows

from faceless_champ import (
    ArchChamp,
    BarChart,
    Captions,
    ChessChamp,
    CodeEditor,
    EarthMap,
    Equation,
    FlowChamp,
    Gauge,
    Image,
    ImageSlot,
    LineChart,
    OutlineMap,
    PieChart,
    PlaygroundCanvas,
    PlaygroundOutput,
    ProgressBar,
    ProgressRing,
    SatelliteMap,
)
from faceless_champ.os_ui import OSClip
from faceless_champ.web import HtmlClip


def check(compiled):
    assert abs(compiled.duration - TOTAL_DURATION) < 1e-9, "The test scene must last exactly 60 seconds"
    assert not compiled.context.captions, "The feature tour has no captions"
    assert not compiled.composition.audio, "The feature tour must remain silent"
    nodes = [node for record in compiled._placements for node in descendants(record["root"])]
    assert not any(isinstance(n, Captions) for n in nodes), "Caption components are not allowed"
    families = {
        "assets": (Image, ImageSlot),
        "oschamp": (OSClip,),
        "codingchamp": (CodeEditor,),
        "prepared-python": (PlaygroundCanvas,),
        "console": (PlaygroundOutput,),
        "html-capture": (HtmlClip,),
        "line-chart": (LineChart,),
        "bar-chart": (BarChart,),
        "donut-chart": (PieChart,),
        "maps": (OutlineMap, SatelliteMap, EarthMap),
        "indicators": (ProgressBar, ProgressRing, Gauge),
        "archchamp": (ArchChamp,),
        "chesschamp": (ChessChamp,),
        "equations": (Equation,),
        "flowchamp": (FlowChamp,),
    }
    coverage = {
        name: sorted({type(n).__name__ for n in nodes if isinstance(n, types)}) for name, types in families.items()
    }
    assert all(coverage.values()), f"Missing real visual components: {coverage}"
    assert {"OutlineMap", "SatelliteMap", "EarthMap"} <= set(coverage["maps"])
    assert {"ProgressBar", "ProgressRing", "Gauge"} <= set(coverage["indicators"])
    assert any(getattr(n, "focuses", ()) for n in nodes if isinstance(n, HtmlClip)), "Missing HTML selector focus"
    assert any("stroke-0" in p["children"] for p in compiled._placements), "Missing whiteboard stroke"
    assert any("named-flag" in p["id"] for p in compiled._placements), "Missing registry-backed flag"
    assert any(n.mask is not None for n in nodes), "Missing a genuine composition mask"
    for n in nodes:
        if isinstance(n, ArchChamp):
            assert {"orbit", "explode", "highlight", "section"} <= {a.kind for a in n.script.actions}
            assert n.dimensions and n.labels, "Arch tour needs labels and dimensions"
        if isinstance(n, ChessChamp):
            assert len(n.script.moves) == 3, "Chess moves should be legal and deterministic"
        if isinstance(n, FlowChamp):
            assert any(a.kind == "signal" and a.options.get("marker") == "packet" for a in n.script.actions)
    actual = {s["id"]: s for s in compiled.report["segments"]}
    for spec in scene_windows():
        assert abs(actual[spec["id"]]["start"] - spec["start"]) < 1e-9
        assert abs(actual[spec["id"]]["end"] - spec["end"]) < 1e-9
    for left, right in zip(scene_windows(), scene_windows()[1:]):
        assert abs(left["end"] - right["start"] - OVERLAP) < 1e-9
    motion_rows = [p for s in compiled.report["segments"] for p in s["placements"]]
    assert all(p.get("enter") == "flow" and p.get("exit") == "flow" for p in motion_rows), (
        "Every placement must use the clean-flow entrance and outro"
    )
    times = {i / 4 for i in range(240)}
    for _, boundary, _, _ in NOMINAL_SCENES[1:]:
        times.update(boundary + d for d in (-0.31, -0.3, -0.15, 0, 0.15, 0.29, 0.3, 0.31))
    issues = []
    placements_checked = 0
    for time in sorted(times):
        if not 0 <= time < TOTAL_DURATION:
            continue
        for row in compiled.layout_at(time)["placements"]:
            placements_checked += 1
            box = row["bounds"]
            if box["left"] < -1 or box["top"] < -1 or box["right"] > 1921 or box["bottom"] > 1081:
                issues.append({"time": time, "id": row["id"], "bounds": box})
    assert not issues, f"Layout exceeds the design canvas: {issues[:5]}"
    assert not any(a["placeholder"] for a in compiled.report["assets"])
    return {
        "ok": True,
        "duration": compiled.duration,
        "audio_tracks": 0,
        "captions": False,
        "theme": compiled.context.theme.name,
        "nominal_scenes": len(NOMINAL_SCENES),
        "overlap_seconds": OVERLAP,
        "features": list(FEATURES),
        "actual_components": coverage,
        "layout_samples": len(times),
        "placements_checked": placements_checked,
        "layout_issues": issues,
        "prepared_assets": compiled.report["prepared_assets"],
        "full_export_verified": False,
    }
