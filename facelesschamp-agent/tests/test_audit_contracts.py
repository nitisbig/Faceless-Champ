"""Design, durable evidence, and packaged schema contracts."""

import json
import shutil
from importlib.resources import files

import pytest
from faceless_champ.typography import DEFAULT_FONT

from facelesschamp_agent import AgentError
from facelesschamp_agent.cli import main
from facelesschamp_agent.models import BenchmarkResult, QualityReport


@pytest.mark.parametrize("field", ["text_engine", "surface_mode", "font", "font_weight", "heading_weight", "captions"])
def test_build_rejects_effective_design_mismatch(project, field):
    plan = project.plan
    if field == "text_engine":
        plan.design.text_engine = "skia"
        change = 'ctx.theme = replace(ctx.theme, text_engine="pillow")'
    elif field == "surface_mode":
        plan.design.surface_mode = "vector"
        change = 'ctx.theme = replace(ctx.theme, surface_mode="raster")'
    elif field == "font":
        shutil.copyfile(DEFAULT_FONT, project.root / "assets/custom.ttf")
        plan.design.font = "assets/custom.ttf"
        change = "ctx.theme = replace(ctx.theme, font=None)"
    elif field == "captions":
        plan.design.captions = True
        change = "ctx.captions = False"
    else:
        plan.design.theme = "clean-flow"
        change = f"ctx.theme = replace(ctx.theme, {field}=300)"
    project.plan_path.write_text(plan.model_dump_json())
    source = project.root / "videos/main.py"
    source.write_text(
        source.read_text().replace(
            "video = project.new_video(ctx)",
            "video = project.new_video(ctx)\n    from dataclasses import replace\n    " + change,
        )
    )
    with pytest.raises(AgentError, match="PLAN_DESIGN") as error:
        project._build()
    assert error.value.scope["property"] == field


def test_design_font_normalization_accepts_equivalent_paths(project):
    shutil.copyfile(DEFAULT_FONT, project.root / "assets/custom.ttf")
    plan = project.plan
    plan.design.font = "assets/custom.ttf"
    project.plan_path.write_text(plan.model_dump_json())
    source = project.root / "videos/main.py"
    source.write_text(
        source.read_text().replace(
            "video = project.new_video(ctx)",
            "video = project.new_video(ctx)\n    from dataclasses import replace\n"
            '    ctx.theme = replace(ctx.theme, font=str(ctx.root / "assets/../assets/custom.ttf"))',
        )
    )
    assert project._build()[0].duration == plan.brief.duration


@pytest.mark.parametrize(
    "damaged",
    [
        "{broken",
        "{}",
        "[]",
        '{"id":"bad","operation":"frame","fingerprint":"old","artifacts":null}',
        '{"id":"bad","operation":"frame","fingerprint":"old","artifacts":[{}]}',
        '{"id":"bad","operation":"review","fingerprint":"old","artifacts":[]}',
        '{"id":"bad","operation":"audit-layout","fingerprint":"old","artifacts":[],"status":"failed"}',
    ],
)
def test_corrupt_evidence_is_scoped_and_preserved(project, damaged, capsys):
    good = project.validate()
    records = project.state / "records"
    good_path = records / (good["id"] + ".json")
    original = good_path.read_bytes()
    broken = records / "damaged.json"
    broken.write_text(damaged)
    assert main(["--project", str(project.root), "status"]) == 1
    error = json.loads(capsys.readouterr().err)["error"]
    assert error["code"] == "EVIDENCE_RECORD"
    assert error["path"] == str(broken)
    assert error["suggested_fix"]
    assert broken.read_text() == damaged
    assert good_path.read_bytes() == original


def test_packaged_benchmark_schema_matches_current_payload():
    schema = json.loads(files("facelesschamp_agent").joinpath("resources/benchmark-result.schema.json").read_text())
    result = BenchmarkResult(
        prompt_id="audit",
        agent="test",
        model="local",
        outcome="complete",
        completion_seconds=1,
        quality=QualityReport(fingerprint="current"),
    )
    properties = schema["$defs"]["QualityReport"]["properties"]
    assert set(result.model_dump(mode="json")["quality"]) <= set(properties)
    assert schema == BenchmarkResult.model_json_schema()
