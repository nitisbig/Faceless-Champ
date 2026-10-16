import json
import runpy
from types import SimpleNamespace

import pytest

from facelesschamp_agent.delivery import write_render_entrypoint
from facelesschamp_agent.errors import AgentError
from facelesschamp_agent.layout import audit_layout, layout_sample_times


def box(left=10, top=10, right=90, bottom=90):
    return {"left": left, "top": top, "right": right, "bottom": bottom}


def setup(rows, *, duration=1, scenes=None, diagnostics=()):
    scene = SimpleNamespace(
        id="scene", start=0, duration=duration, key_events=[], intentional_overlaps=[], allow_bleed=[]
    )
    plan = SimpleNamespace(scenes=scenes or [scene])
    segments = []
    for spec in plan.scenes:
        segments.append(
            {
                "id": spec.id,
                "start": spec.start,
                "end": spec.start + spec.duration,
                "placements": [
                    {"id": r["id"], "children": list(r.get("children", {}))} for r in rows if r["segment"] == spec.id
                ],
            }
        )
    compiled = SimpleNamespace(
        duration=duration,
        composition=SimpleNamespace(canvas=SimpleNamespace(width=100, height=100), entries=[]),
        context=SimpleNamespace(bounds=box()),
        report={"segments": segments, "diagnostics": list(diagnostics)},
        layout_at=lambda time: {"source_time": time, "placements": rows},
    )
    return compiled, plan


def row(identifier="card", *, children=None, bounds=None, ancestors=None, segment="scene"):
    return {
        "id": identifier,
        "segment": segment,
        "bounds": bounds or box(),
        "children": children or {},
        "child_ancestors": ancestors or {},
    }


def test_overlapping_named_siblings_fail_and_repeated_findings_are_compact():
    compiled, plan = setup([row(children={"title": box(20, 20, 65, 40), "subtitle": box(40, 25, 80, 45)})])
    result = audit_layout(compiled, plan, times=[0, 0.5])
    assert result["status"] == "failed"
    (overlap,) = [f for f in result["findings"] if f["code"] == "LAYOUT_OVERLAP"]
    assert overlap["elements"] == ["card/subtitle", "card/title"]
    assert overlap["scene_id"] == "scene"
    assert overlap["occurrences"] == 2
    assert overlap["last_source_time"] == 0.5
    assert overlap["suggested_repair"]


def test_explicit_overlap_pair_is_exact_and_stale_allowances_fail():
    compiled, plan = setup([row(children={"title": box(20, 20, 65, 40), "subtitle": box(40, 25, 80, 45)})])
    plan.scenes[0].intentional_overlaps = [("card/title", "card/subtitle")]
    assert audit_layout(compiled, plan, times=[0.5])["status"] == "passed"
    plan.scenes[0].intentional_overlaps = [("card/title", "card/missing")]
    result = audit_layout(compiled, plan, times=[0.5])
    assert {f["code"] for f in result["findings"]} == {"LAYOUT_ALLOWANCE_UNKNOWN", "LAYOUT_OVERLAP"}


def test_content_containment_does_not_imply_parenthood():
    compiled, plan = setup([row(children={"long_label": box(20, 20, 80, 70), "short_label": box(40, 40, 60, 60)})])
    assert audit_layout(compiled, plan, times=[0.5])["status"] == "failed"


def test_real_ancestry_and_card_surface_do_not_create_false_collisions():
    compiled, plan = setup(
        [
            row(
                children={
                    "surface": box(),
                    "body": box(20, 20, 80, 80),
                    "text": box(30, 30, 70, 50),
                },
                ancestors={"text": ["body"]},
            )
        ]
    )
    assert audit_layout(compiled, plan, times=[0.5])["status"] == "passed"


def test_cross_placement_uses_content_boxes_instead_of_parent_unions():
    compiled, plan = setup(
        [
            row("a", children={"left": box(10, 10, 30, 30), "right": box(70, 10, 90, 30)}),
            row("b", children={"center": box(40, 10, 60, 30)}),
        ]
    )
    assert audit_layout(compiled, plan, times=[0.5])["status"] == "passed"


def test_named_nested_parent_union_does_not_collide_with_sibling_in_its_whitespace():
    compiled, plan = setup(
        [
            row(
                "a",
                children={
                    "body": box(10, 10, 90, 30),
                    "left": box(10, 10, 30, 30),
                    "right": box(70, 10, 90, 30),
                },
                ancestors={"left": ["body"], "right": ["body"]},
            ),
            row("b", children={"center": box(40, 10, 60, 30)}),
        ]
    )
    assert audit_layout(compiled, plan, times=[0.5])["status"] == "passed"


def test_full_bleed_background_is_structural_but_panel_name_cannot_hide_content_overlap():
    compiled, plan = setup(
        [
            row("back", bounds=box(0, 0, 100, 100), children={"background": box(0, 0, 100, 100)}),
            row("card", bounds=box(20, 20, 80, 60), children={"text": box(20, 20, 80, 60)}),
        ]
    )
    assert audit_layout(compiled, plan, times=[0.5])["status"] == "passed"
    compiled, plan = setup([row(children={"panel": box(), "text": box(30, 30, 70, 50)})])
    assert audit_layout(compiled, plan, times=[0.5])["status"] == "failed"


def test_canvas_and_safe_overflow_are_distinct_and_bleed_keeps_canvas_gate():
    compiled, plan = setup([row(bounds=box(0, 20, 40, 50))])
    assert {f["code"] for f in audit_layout(compiled, plan, times=[0])["findings"]} == {"LAYOUT_SAFE_OVERFLOW"}
    plan.scenes[0].allow_bleed = ["card"]
    assert audit_layout(compiled, plan, times=[0])["status"] == "passed"
    compiled.layout_at = lambda time: {"placements": [row(bounds=box(-4, 20, 40, 50))]}
    assert {f["code"] for f in audit_layout(compiled, plan, times=[0])["findings"]} == {"LAYOUT_CANVAS_OVERFLOW"}


def test_internal_engine_diagnostics_are_not_lost():
    compiled, plan = setup(
        [row()],
        diagnostics=[
            {
                "code": "FLOW_LABEL_OVERLAP",
                "segment": "scene",
                "placement": "card",
                "elements": ["a", "b"],
                "source_time": 0.25,
            }
        ],
    )
    result = audit_layout(compiled, plan, times=[0.5])
    (finding,) = result["findings"]
    assert finding["code"] == "FLOW_LABEL_OVERLAP"
    assert finding["source_time"] == 0.25
    assert finding["elements"] == ["card/a", "card/b"]
    assert result["status"] == "failed"


def test_dense_samples_include_very_short_scenes_track_keyframes_and_transition_boundaries():
    first = SimpleNamespace(id="a", start=0, duration=0.001, key_events=[])
    second = SimpleNamespace(id="b", start=0.001, duration=1.999, key_events=[SimpleNamespace(at=0.5, duration=0.2)])
    compiled, plan = setup([], duration=2, scenes=[first, second])
    compiled.composition.entries = [
        SimpleNamespace(
            start=0,
            end=2,
            tracks=[
                SimpleNamespace(
                    start=0.15,
                    duration=0.4,
                    keyframes=((0, 0), (0.3, 1), (1, 2)),
                )
            ],
        )
    ]
    samples = layout_sample_times(compiled, plan)
    assert samples == sorted(set(samples))
    assert any(0 < t < 0.001 for t in samples)
    assert any(abs(t - 0.27) < 1e-10 for t in samples)
    assert 0.501 in samples and 0.601 in samples and 0.701 in samples
    assert len([t for t in samples if 0.15 <= t <= 0.55]) >= 6
    assert all(0 <= t < 2 for t in samples)


def test_static_scene_samples_are_bounded_and_opacity_tracks_do_not_repeat_geometry_checks():
    compiled, plan = setup([row()], duration=120)
    initial = layout_sample_times(compiled, plan)
    assert len(initial) <= 24
    compiled.composition.entries = [
        SimpleNamespace(
            start=0,
            end=120,
            tracks=[SimpleNamespace(property="opacity", start=i, duration=0.6, keyframes=None) for i in range(100)],
        )
    ]
    assert layout_sample_times(compiled, plan) == initial


def test_overlapping_motion_tracks_share_uniform_sampling_but_keep_each_boundary():
    compiled, plan = setup([row()], duration=4)
    track = SimpleNamespace(property="position", start=1, duration=0.6, keyframes=None)
    compiled.composition.entries = [SimpleNamespace(start=0, end=4, tracks=[track])]
    initial = layout_sample_times(compiled, plan)
    compiled.composition.entries[0].tracks *= 20
    assert layout_sample_times(compiled, plan) == initial
    compiled.composition.entries[0].tracks.append(
        SimpleNamespace(property="position", start=1.1, duration=0.3, keyframes=None)
    )
    samples = layout_sample_times(compiled, plan)
    assert 1.1 in samples and 1.4 in samples
    assert any(t < 1.1 and 1.1 - t < 1e-10 for t in samples)


def test_missing_scene_coverage_and_opaque_content_cannot_pass():
    scenes = [SimpleNamespace(id=name, start=i, duration=1, key_events=[]) for i, name in enumerate(("a", "b"))]
    compiled, plan = setup([], duration=2, scenes=scenes)
    result = audit_layout(compiled, plan, times=[0.5])
    assert {f["code"] for f in result["findings"]} == {"LAYOUT_SCENE_UNSAMPLED", "LAYOUT_NO_PLACEMENTS"}
    assert result["status"] == "failed"


@pytest.mark.parametrize("times", [[], [-1], [1], [float("nan")], [True]])
def test_invalid_samples_are_rejected(times):
    compiled, plan = setup([row()])
    with pytest.raises(AgentError, match="LAYOUT_TIME"):
        audit_layout(compiled, plan, times=times)


def test_real_starter_has_layout_coverage(project):
    compiled, plan, _ = project._build()
    result = audit_layout(compiled, plan)
    assert result["status"] == "passed", result["findings"]
    assert result["scene_ids"] == ["process"]
    assert result["full_export_verified"] is False


def test_entrypoint_anchors_project_and_relative_outputs_when_invoked_elsewhere(tmp_path, monkeypatch, capsys):
    root = tmp_path / "project"
    root.mkdir()
    target = write_render_entrypoint(root)
    called = []

    class FakeProject:
        def __init__(self, path):
            called.append(("root", path))
            self.plan = SimpleNamespace(brief=SimpleNamespace(duration=40))

        def validate(self):
            return {"status": "passed"}

        def audit_layout(self):
            return {"status": "passed"}

        def preview(self, path, *, start, end):
            called.append(("preview", path, start, end))
            return {"artifacts": [{"path": str(path)}]}

        def verify(self, path):
            called.append(("verify", path))
            return {"status": "passed"}

    import facelesschamp_agent

    monkeypatch.setattr(facelesschamp_agent, "AgentProject", FakeProject)
    monkeypatch.chdir(tmp_path)
    namespace = runpy.run_path(str(target))
    assert namespace["main"](["--output", "output/test.mp4"]) == 0
    assert called == [
        ("root", root),
        ("preview", root / "output/test.mp4", 0, 10),
        ("verify", root / "output/test.mp4"),
    ]
    report = json.loads(capsys.readouterr().out)
    assert report["delivery"] == "preview" and report["full_export_verified"] is False


def test_entrypoint_preserves_user_renderer_and_is_idempotent(tmp_path):
    target = write_render_entrypoint(tmp_path)
    assert write_render_entrypoint(tmp_path) == target
    target.write_text("# authored renderer\n")
    with pytest.raises(AgentError, match="RENDER_EXISTS"):
        write_render_entrypoint(tmp_path)
    assert target.read_text() == "# authored renderer\n"


def test_entrypoint_repeated_default_exports_use_unique_project_relative_outputs(tmp_path, monkeypatch, capsys):
    import facelesschamp_agent

    outputs = []

    class FakeProject:
        def __init__(self, root):
            self.plan = SimpleNamespace(brief=SimpleNamespace(duration=20))

        def validate(self):
            return {"status": "passed"}

        def audit_layout(self):
            return {"status": "passed"}

        def preview(self, path, **kwargs):
            outputs.append(path)
            return {}

        def verify(self, path):
            return {"status": "passed"}

    monkeypatch.setattr(facelesschamp_agent, "AgentProject", FakeProject)
    namespace = runpy.run_path(str(write_render_entrypoint(tmp_path)))
    assert namespace["main"]([]) == namespace["main"]([]) == 0
    assert len(set(outputs)) == 2
    assert all(path.parent == tmp_path / "output/agent" and path.name.startswith("preview-") for path in outputs)
    capsys.readouterr()


@pytest.mark.parametrize("failure", ["layout", "build", "verification", "runtime"])
def test_entrypoint_gates_export_and_reports_structural_failures_as_json(tmp_path, monkeypatch, capsys, failure):
    from facelesschamp_kit.diagnostics import KitError

    import facelesschamp_agent

    calls = []

    class FakeProject:
        def __init__(self, root):
            self.plan = SimpleNamespace(brief=SimpleNamespace(duration=20))

        def validate(self):
            if failure == "build":
                raise KitError("LAYOUT", "Block exceeds allocated bounds", segment="scene", placement="scene/card")
            return {"status": "passed"}

        def audit_layout(self):
            return {"status": "failed" if failure == "layout" else "passed"}

        def preview(self, path, **kwargs):
            calls.append("preview")
            if failure == "runtime":
                raise RuntimeError("ffmpeg is required for export")
            return {}

        def verify(self, path):
            return {"status": "failed"}

    monkeypatch.setattr(facelesschamp_agent, "AgentProject", FakeProject)
    namespace = runpy.run_path(str(write_render_entrypoint(tmp_path)))
    assert namespace["main"]([]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "failed"
    assert calls == (["preview"] if failure in {"verification", "runtime"} else [])
    if failure == "build":
        assert result["error"]["code"] == "LAYOUT"
    if failure == "runtime":
        assert result["error"]["message"] == "ffmpeg is required for export"
