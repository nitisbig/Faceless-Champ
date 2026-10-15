import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from facelesschamp_agent import AgentError, CapabilityRegistry, DesignSpec, VideoPlan
from facelesschamp_agent.cli import main
from facelesschamp_agent.models import ReviewSubmission
from facelesschamp_agent.scaffold import INITIAL_PLAN


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p["scenes"].append(deepcopy(p["scenes"][0])),
        lambda p: p["story"]["beats"][0].update(scene_id="missing"),
        lambda p: p["scenes"][0].update(duration=20),
        lambda p: p["scenes"][0].update(required_assets=["unknown"]),
        lambda p: p["scenes"][0]["content"].update(steps=["only one"]),
        lambda p: p["scenes"][0]["key_events"].append({"at": 10, "label": "late"}),
        lambda p: p["brief"].update(duration=float("inf")),
        lambda p: p["design"].update(palette={"accent": "not a color"}),
    ],
)
def test_plan_constraints(mutate):
    raw = INITIAL_PLAN.model_dump(mode="json")
    mutate(raw)
    with pytest.raises((ValidationError, ValueError)):
        VideoPlan.model_validate(raw)


def test_registry_covers_public_api_and_bundled_docs():
    import faceless_champ

    registry = CapabilityRegistry()
    ids = {e["id"] for e in registry.search()}
    assert {f"faceless_champ.{name}" for name in faceless_champ.__all__} <= ids
    assert registry.check()["ok"]
    assert registry.search("request")
    assert "guide" in registry.describe("faceless_champ.FlowChamp")
    with pytest.raises(AgentError, match="CAPABILITY_ID"):
        registry.describe("CodeEditor")


def test_clean_flow_theme_is_in_plan_schema():
    design = DesignSpec(theme="clean-flow")
    assert DesignSpec.model_validate_json(design.model_dump_json()) == design
    assert "clean-flow" in DesignSpec.model_json_schema()["properties"]["theme"]["enum"]
    assert "clean-flow" in VideoPlan.model_json_schema()["$defs"]["DesignSpec"]["properties"]["theme"]["enum"]


def test_clean_flow_preserves_packaged_font_when_plan_omits_font(project):
    from faceless_champ import Canvas
    from facelesschamp_kit import BuildContext
    from facelesschamp_kit.themes import THEMES

    plan = project.plan
    plan.design.theme = "clean-flow"
    plan.design.palette = {"accent": "#E15422"}
    project.plan_path.write_text(plan.model_dump_json())
    ctx = BuildContext(project.root, Canvas(1920, 1080))
    project.new_video(ctx)
    selected = THEMES["clean-flow"]
    assert ctx.theme.font == selected.font
    assert Path(ctx.theme.font).is_file()
    assert ctx.theme.font_weight == 400
    assert ctx.theme.heading_weight == 700
    assert ctx.theme.accent == "#E15422"
    assert ctx.canvas.bg == selected.background


def test_plan_custom_font_clears_packaged_variable_weights(project):
    from faceless_champ import Canvas
    from facelesschamp_kit import BuildContext

    plan = project.plan
    plan.design.theme = "clean-flow"
    plan.design.font = "assets/custom-font.ttf"
    project.plan_path.write_text(plan.model_dump_json())
    ctx = BuildContext(project.root, Canvas(1920, 1080))
    project.new_video(ctx)
    assert ctx.theme.font == str(project.root / "assets/custom-font.ttf")
    assert ctx.theme.font_weight is None
    assert ctx.theme.heading_weight is None


def test_schema_round_trip_and_cli_from_other_directory(project, tmp_path, monkeypatch, capsys):
    plan = project.plan
    assert VideoPlan.model_validate_json(plan.model_dump_json()) == plan
    monkeypatch.chdir(tmp_path)
    assert main(["--project", str(project.root), "validate", "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["result"]["status"] == "passed"
    assert main(["schema"]) == 0
    assert "$defs" in json.loads(capsys.readouterr().out)["result"]
    assert main(["frame"]) == 1
    assert json.loads(capsys.readouterr().err)["error"]["code"] == "ARGUMENT"


def test_plan_mismatch_and_layout(project):
    assert project.validate()["status"] == "passed"
    source = project.root / "videos/main.py"
    source.write_text(source.read_text().replace("duration=scene.duration)", "duration=scene.duration + 1)"))
    with pytest.raises(AgentError, match="PLAN_TIMING"):
        project.validate()


def test_explicit_no_vision_review(project):
    fingerprint = project.status().fingerprint
    project.review(
        {
            "fingerprint": fingerprint,
            "reviewer": "text-only",
            "kind": "visual",
            "status": "unverified",
            "reviewed_scenes": ["process"],
            "notes": "No image access",
        }
    )
    assert project.status().visual_review == "unverified"
    with pytest.raises(ValidationError):
        ReviewSubmission(fingerprint=fingerprint, reviewer="r", kind="visual", status="passed")


def test_review_evidence_stale_after_code_plan_or_asset_change(project):
    artifact = project.frame(2)["artifacts"][0]
    before = project.status().fingerprint
    submission = {
        "fingerprint": before,
        "reviewer": "test",
        "kind": "visual",
        "status": "passed",
        "reviewed_scenes": ["process"],
        "evidence_artifacts": [artifact["id"]],
    }
    project.review(submission)
    assert project.status().visual_review == "passed"
    source = project.root / "videos/main.py"
    source.write_text(source.read_text() + "\n# changed source\n")
    assert project.status().visual_review == "pending"
    with pytest.raises(AgentError, match="REVIEW_STALE"):
        project.review(submission)
    plan = project.plan
    plan.brief.prompt = "Updated intent"
    project.plan_path.write_text(plan.model_dump_json())
    assert project.status().fingerprint != before


def test_tampered_evidence_and_invalid_review_location(project):
    artifact = project.frame(2)["artifacts"][0]
    submission = {
        "fingerprint": project.status().fingerprint,
        "reviewer": "r",
        "kind": "visual",
        "status": "passed",
        "reviewed_scenes": ["process"],
        "evidence_artifacts": [artifact["id"]],
    }
    Path(artifact["path"]).write_bytes(b"corrupt")
    with pytest.raises(AgentError, match="REVIEW_EVIDENCE"):
        project.review(submission)


def test_storyboard_has_more_than_midpoints(project):
    times = project.sample_times()
    assert 0 in times and 1.2 in times and len(times) > 4
    result = project.storyboard()
    assert len(result["layouts"]) == len(times)
    assert all(Path(a["path"]).is_file() for a in result["artifacts"])


def test_storyboard_timestamps_follow_numeric_frame_order(project, monkeypatch):
    from faceless_champ import render_storyboard

    times = [i / 25 for i in range(120)]
    monkeypatch.setattr(project, "sample_times", lambda: times)
    monkeypatch.setattr(
        "facelesschamp_agent.project.render_storyboard",
        lambda composition, samples, directory: render_storyboard(composition, samples, directory, size=(80, 45)),
    )
    result = project.storyboard()
    frames = [a for a in result["artifacts"] if a["kind"] == "frame"]
    assert len(frames) == len(times)
    assert [a["source_time"] for a in frames] == times
    for index, artifact in enumerate(frames, start=1):
        number, timestamp = Path(artifact["path"]).stem.split("-", 1)
        assert int(number) == index
        assert float(timestamp.removesuffix("s")) == pytest.approx(artifact["source_time"])


def test_data_requires_provenance_or_illustrative_label():
    raw = INITIAL_PLAN.model_dump(mode="json")
    raw["scenes"][0].update(recipe="part-whole", content={"parts": {"a": 2, "b": 3}})
    with pytest.raises(ValidationError):
        VideoPlan.model_validate(raw)
    raw["scenes"][0]["illustrative"] = True
    assert VideoPlan.model_validate(raw)


def test_registry_recipes_have_complete_guides():
    registry = CapabilityRegistry()
    for entry in registry.search(kind="recipe"):
        assert "guide" in registry.describe(entry["id"])
    assert registry.describe("facelesschamp_kit.blocks.CodingPlayground")["preparation"] == "explicit"


def test_missing_required_data_is_scoped(project):
    plan = project.plan.model_dump(mode="json")
    plan["brief"]["assets"] = [{"id": "data", "path": "missing.csv", "kind": "data"}]
    project.plan_path.write_text(json.dumps(plan))
    with pytest.raises(AgentError, match="ASSET_MISSING"):
        project.validate()


def test_review_finding_must_name_real_element(project):
    artifact = project.frame(2)["artifacts"][0]
    with pytest.raises(AgentError, match="REVIEW_TARGET"):
        project.review(
            {
                "fingerprint": project.status().fingerprint,
                "reviewer": "test",
                "kind": "visual",
                "status": "failed",
                "reviewed_scenes": ["process"],
                "evidence_artifacts": [artifact["id"]],
                "findings": [
                    {
                        "scene_id": "process",
                        "source_time": 2,
                        "element": "missing",
                        "code": "layout",
                        "observed": "Too small",
                        "evidence_artifact": artifact["id"],
                        "suggested_repair": "Enlarge",
                    }
                ],
            }
        )


def test_benchmark_contract_and_count():
    from importlib.resources import files

    from facelesschamp_agent.models import BenchmarkResult

    data = json.loads(files("facelesschamp_agent").joinpath("resources/benchmarks.json").read_text())
    assert len({p["id"] for p in data["prompts"]}) == 24
    assert "human_scores" in BenchmarkResult.model_json_schema()["properties"]


def test_missing_artwork_requires_visible_placeholder(project):
    raw = project.plan.model_dump(mode="json")
    raw["brief"]["assets"] = [{"id": "art", "path": "missing.png"}]
    raw["scenes"][0]["required_assets"] = ["art"]
    project.plan_path.write_text(json.dumps(raw))
    with pytest.raises(AgentError, match="ASSET_PLACEHOLDER"):
        project.validate()
    source = project.root / "videos/main.py"
    source.write_text(
        source.read_text().replace(
            "        apply_recipe(segment, scene.recipe, scene.content)",
            "        from facelesschamp_kit.blocks import ImageCard\n"
            "        segment.add(ImageCard('art', mode='auto'), id='art')",
        )
    )
    assert project.validate()["status"] == "passed"
    assert any("Placeholder artwork" in reason for reason in project.status().draft_reasons)
    assert Path(project.frame(2)["artifacts"][0]["path"]).exists()
