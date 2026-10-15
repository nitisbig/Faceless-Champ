"""Sample the complete authored scene without exporting the full movie."""

from facelesschamp_kit.compiler import descendants
from videos.main import NOMINAL_SCENES, OVERLAP, TOTAL_DURATION, scene_windows

from faceless_champ import Captions, FlowChamp


def check(compiled):
    assert compiled.duration == TOTAL_DURATION
    assert not compiled.composition.audio, "The scene must be silent"
    assert not compiled.context.captions
    assert compiled.context.theme.name == "clean-flow"
    nodes = [n for p in compiled._placements for n in descendants(p["root"])]
    assert not any(isinstance(n, Captions) for n in nodes)
    clips = [n for n in nodes if isinstance(n, FlowChamp)]
    assert len(clips) == 4
    actual = {row["id"]: row for row in compiled.report["segments"]}
    for row in scene_windows():
        assert actual[row["id"]]["start"] == row["start"]
        assert actual[row["id"]]["end"] == row["end"]
    for a, b in zip(scene_windows(), scene_windows()[1:]):
        assert abs(a["end"] - b["start"] - OVERLAP) < 1e-9
    flow_samples = 0
    flow_issues = []
    for clip in clips:
        assert any(a.kind == "signal" and a.options.get("marker") == "packet" for a in clip.script.actions)
        assert all(a.options.get("tool") == "none" for a in clip.script.actions if a.kind == "draw")
        assert not clip.diagnostics, f"Initial graph problem: {clip.diagnostics}"
        times = {i / 8 for i in range(65)}
        for action in clip.script.actions:
            for i in range(len(action.targets)):
                start = action.at + i * action.options.get("stagger", 0)
                times.update((start, start + action.duration / 2, start + action.duration))
        for time in sorted(times):
            flow_samples += 1
            flow_issues.extend(clip.diagnostics_at(time))
    assert not flow_issues, f"Flow layout issues: {flow_issues[:8]}"
    times = {i / 8 for i in range(int(TOTAL_DURATION * 8))}
    for _, start, _, _ in NOMINAL_SCENES[1:]:
        times.update(start + d for d in (-0.31, -0.3, -0.15, 0, 0.15, 0.3, 0.31))
    issues = []
    for time in sorted(times):
        for placement in compiled.layout_at(time)["placements"]:
            b = placement["bounds"]
            if b["left"] < -1 or b["top"] < -1 or b["right"] > 1921 or b["bottom"] > 1081:
                issues.append({"time": time, "placement": placement["id"], "bounds": b})
    assert not issues, f"Canvas overflow: {issues[:5]}"
    assert not any(a["placeholder"] for a in compiled.report["assets"])
    return {
        "ok": True,
        "duration": compiled.duration,
        "audio_tracks": 0,
        "captions": False,
        "theme": compiled.context.theme.name,
        "views": len(clips),
        "overlap_seconds": OVERLAP,
        "flow_samples": flow_samples,
        "layout_samples": len(times),
        "layout_issues": issues,
        "flow_issues": flow_issues,
        "full_export_verified": False,
    }
