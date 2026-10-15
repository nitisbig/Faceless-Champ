"""Behavioral preparation boundaries and structural acceptance for this fixture."""

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "facelesschamp-kit/src"), str(PROJECT)]

from facelesschamp_kit import BuildContext, Project
from facelesschamp_kit.diagnostics import KitError
from facelesschamp_kit.themes import CLEAN_FLOW
from videos import main as story

from faceless_champ import Canvas, Text
from faceless_champ.web import WebError


def context(root=PROJECT):
    return BuildContext(
        root, Canvas(1920, 1080, CLEAN_FLOW.background), CLEAN_FLOW, safe_margin=48, caption_space=0, captions=False
    )


def test_normal_build_never_executes_or_captures():
    if not (PROJECT / ".fc-kit/web/reference.json").is_file():
        pytest.skip("Run python3 render.py --prepare first")
    with (
        patch("faceless_champ.prepare_playground", side_effect=AssertionError("Python execution during replay")),
        patch.object(story, "capture_html", side_effect=AssertionError("Browser launch during replay")),
    ):
        compiled = story.build(context()).compile()
    assert compiled.duration == 60
    assert not compiled.composition.audio
    assert all(
        p["enter"] == "flow" and p["exit"] == "flow" for s in compiled.report["segments"] for p in s["placements"]
    )


def test_missing_checkpoint_requires_explicit_prepare(tmp_path):
    with (
        patch("faceless_champ.prepare_playground", side_effect=AssertionError("Must not auto-execute")),
        pytest.raises(KitError) as result,
    ):
        context(tmp_path).playground(story.code_script(), fps=30)
    assert result.value.code == "PLAYGROUND_UNPREPARED"


def test_changed_html_fails_before_browser_capture(tmp_path):
    reference = tmp_path / ".fc-kit/web/reference.json"
    reference.parent.mkdir(parents=True)
    reference.write_text(json.dumps({"fingerprint": "old-source", "directory": "captures/old"}))
    with (
        patch.object(story, "capture_html", side_effect=AssertionError("Must not auto-capture")),
        pytest.raises(WebError, match="WEB_STALE"),
    ):
        story.prepared_web(context(tmp_path))


def test_duration_overlap_and_silent_feature_coverage():
    if not (PROJECT / ".fc-kit/web/reference.json").is_file():
        pytest.skip("Run python3 render.py --prepare first")
    from checks import check

    result = check(Project(PROJECT).build("main", strict_assets=True))
    assert result["ok"] and result["audio_tracks"] == 0
    assert result["nominal_scenes"] == 7 and result["overlap_seconds"] == 0.6
    assert result["layout_samples"] >= 240
    assert result["full_export_verified"] is False


def test_quality_alone_does_not_select_full_export():
    spec = importlib.util.spec_from_file_location("clean_flow_render", PROJECT / "render.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    composition = type("Composition", (), {})()
    compiled = type("Compiled", (), {"composition": composition})()
    with (
        patch.object(module.Project, "build", return_value=compiled),
        patch.object(module, "render", return_value="preview.mp4") as render_call,
    ):
        assert module.main(["--quality", "high"]) == 0
        assert render_call.call_args.kwargs["start_time"] == 0
        assert render_call.call_args.kwargs["end_time"] == 6
        assert module.main(["--full"]) == 0
        assert render_call.call_args.kwargs["end_time"] == 60


def test_major_handoffs_never_stack_two_headings():
    if not (PROJECT / ".fc-kit/web/reference.json").is_file():
        pytest.skip("Run python3 render.py --prepare first")
    compiled = Project(PROJECT).build("main", strict_assets=True)
    labels = {row[3] for row in story.NOMINAL_SCENES}
    headings = [e for e in compiled.composition.entries if isinstance(e.component, Text) and e.component.text in labels]
    for _, boundary, _, _ in story.NOMINAL_SCENES[1:]:
        for offset in (-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3):
            time = boundary + offset
            visible = [e for e in headings if e.start <= time < e.end and e.state_at(time)["opacity"] > 1e-6]
            assert len(visible) <= 1, f"Stacked headings at {time:g}s"
    for left, right in zip(story.NOMINAL_SCENES, story.NOMINAL_SCENES[1:]):
        layers = {
            segment["id"]: [p["z_index"] for p in segment["placements"]] for segment in compiled.report["segments"]
        }
        assert max(layers[left[0]]) < min(layers[right[0]])


def test_intrinsic_reveals_start_concealed_without_a_flash():
    if not (PROJECT / ".fc-kit/web/reference.json").is_file():
        pytest.skip("Run python3 render.py --prepare first")
    scene = Project(PROJECT).build("main", strict_assets=True).composition
    properties = set()
    for entry in scene.entries:
        for track in entry.tracks:
            if track.property not in {"clip", "draw", "reveal"}:
                continue
            properties.add(track.property)
            assert track.start == pytest.approx(entry.start)
            value = entry.state_at(entry.start)[track.property]
            if track.property == "clip":
                assert value[2] == 0 or value[3] == 0
            else:
                assert value == 0
    assert properties == {"clip", "draw", "reveal"}
