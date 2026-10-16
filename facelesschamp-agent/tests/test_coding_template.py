"""Default-only template selection, editable ownership, and export controls."""

import json
import runpy
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from facelesschamp_agent import (
    AgentError,
    CapabilityRegistry,
    install_coding_tutorial,
    load_coding_tutorial,
    plan_project,
    select_scenes,
)
from facelesschamp_agent.delivery import write_render_entrypoint


@pytest.fixture(scope="module")
def registry():
    return CapabilityRegistry()


def context():
    return {
        "fingerprint": "coding-input",
        "narration_text": "Write a Python program and display its output.",
        "sources": [],
        "cues": [],
        "warnings": [],
        "truncated": False,
    }


def test_cpp_topic_can_use_the_language_independent_design(tmp_path):
    from facelesschamp_agent.templates import default_coding_template

    assert default_coding_template(
        root=tmp_path,
        prompt="C++ tutorial",
        context={},
        instructions=[],
        design=None,
        project_design={},
        constraints=[],
        format="landscape",
    )


def test_default_coding_selection_uses_the_separate_template(tmp_path, registry):
    selected = select_scenes(tmp_path, prompt="Teach a Python coding tutorial", context=context(), registry=registry)
    assert selected.design.template == "coding-tutorial"
    assert selected.beats[0].selected_capability == "facelesschamp_kit.CodingTutorialTemplate"
    assert selected.guidelines["template"]["style"] == "templates/coding-tutorial/style.json"
    assert "no headings" in selected.guidelines["template"]["text"].lower()
    assert not (tmp_path / "templates").exists(), "Read-only selection must not copy files"


@pytest.mark.parametrize(
    "direction",
    [
        {"instructions": ["Use only an editor"]},
        {"design": {}},
        {"design": {"theme": "midnight"}},
        {"prompt": "Python tutorial with a purple background"},
        {"format": "shorts"},
    ],
)
def test_custom_direction_bypasses_the_default_template(tmp_path, registry, direction):
    request = {"prompt": "Teach Python", **direction}
    selected = select_scenes(tmp_path, context=context(), registry=registry, **request)
    assert selected.design.template is None and "template" not in selected.guidelines
    assert all(
        not candidate["id"].endswith((".CodingTutorialStyle", ".CodingTutorialTemplate"))
        for beat in selected.beats
        for candidate in beat.candidates
    )
    assert not (tmp_path / "templates").exists()


def test_saved_custom_design_is_preserved_but_the_untouched_starter_allows_fallback(project, registry):
    selected = select_scenes(project.root, prompt="Teach Python", context=context(), registry=registry)
    assert selected.design.template == "coding-tutorial"
    raw = json.loads(project.plan_path.read_text())
    raw["design"]["palette"] = {"background": "#111122"}
    project.plan_path.write_text(json.dumps(raw))
    selected = select_scenes(project.root, prompt="Teach Python", context=context(), registry=registry)
    assert selected.design.template is None and selected.design.palette["background"] == "#111122"


def test_custom_direction_files_and_non_coding_topics_do_not_get_a_template(tmp_path, registry):
    source = {**context(), "narration_text": "A sine function"}
    selected = select_scenes(tmp_path, prompt="Teach a sine function", context=source, registry=registry)
    assert selected.design.template is None
    (tmp_path / "design.md").write_text("Use our own visual system")
    selected = select_scenes(tmp_path, prompt="Teach Python", context=context(), registry=registry)
    assert selected.design.template is None


def test_plan_installs_once_reuses_cache_and_preserves_hacked_style(tmp_path, registry):
    first = plan_project(tmp_path, prompt="Teach Python", registry=registry, duration=6)
    assert first["template"]["id"] == "coding-tutorial"
    again = plan_project(tmp_path, prompt="Teach Python", registry=registry, duration=6)
    assert again["reused"] and again["selection"] == first["selection"]
    style_path = Path(first["template"]["style"])
    style = json.loads(style_path.read_text())
    style["background"] = "#123456"
    style_path.write_text(json.dumps(style))
    edited = style_path.read_bytes()
    changed = plan_project(tmp_path, prompt="Teach Python", registry=registry, duration=6)
    assert changed["selection"] != first["selection"] and style_path.read_bytes() == edited
    assert load_coding_tutorial(tmp_path).canvas().bg == "#123456"
    custom = plan_project(tmp_path, prompt="Teach Python", instructions=["Use custom artwork"], registry=registry)
    assert custom["template"] is None and style_path.read_bytes() == edited


def test_project_style_is_loaded_each_build_and_invalidates_evidence(project):
    pack = install_coding_tutorial(project.root)
    raw = project.plan
    raw.design.template = "coding-tutorial"
    project.plan_path.write_text(raw.model_dump_json())
    before = project.validate()["fingerprint"]
    path = Path(pack["style"])
    style = json.loads(path.read_text())
    style["background"] = "#123456"
    path.write_text(json.dumps(style))
    assert project.validate()["fingerprint"] != before
    compiled = project.kit.build()
    assert compiled.composition.canvas.bg == "#123456"


def test_generated_renderer_passes_fps_and_quality_without_modifying_profiles(tmp_path, monkeypatch, capsys):
    import facelesschamp_agent

    calls = []

    class FakeProject:
        def __init__(self, root):
            self.plan = SimpleNamespace(brief=SimpleNamespace(duration=20))

        def validate(self):
            return {}

        def audit_layout(self):
            return {"status": "passed"}

        def preview(self, path, **kwargs):
            calls.append(kwargs)
            return {}

        def verify(self, path):
            return {"status": "passed"}

        def render(self, path, **kwargs):
            calls.append(kwargs)
            return {"verification": {"status": "passed"}}

    monkeypatch.setattr(facelesschamp_agent, "AgentProject", FakeProject)
    runner = runpy.run_path(str(write_render_entrypoint(tmp_path)))["main"]
    assert runner(["--fps", "60", "--quality", "high"]) == 0
    assert calls[-1] == {"start": 0, "end": 10, "fps": 60, "quality": "high"}
    assert runner(["--full", "--fps", "24", "--quality", "4k"]) == 0
    assert calls[-1] == {"fps": 24, "quality": "4k"}
    capsys.readouterr()


def test_export_overrides_replace_profile_dimensions_and_record_correct_expectations(project, monkeypatch):
    captured = []

    def fake_render(composition, path, **kwargs):
        captured.append(kwargs["settings"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"test video")

    monkeypatch.setattr("facelesschamp_agent.project.render", fake_render)
    before = deepcopy(project.kit.config)
    result = project.preview(project.root / "output/overrides.mp4", start=0, end=1, fps=60, quality="4k")
    assert captured[0].width is None and captured[0].height is None
    assert result["expected"]["width"] == 3840 and result["expected"]["height"] == 2160
    assert result["expected"]["fps"] == 60 and result["source_range"] == [0, 1]
    assert project.kit.config == before


@pytest.mark.parametrize(
    "options", [{"fps": -1}, {"fps": float("nan")}, {"fps": True}, {"quality": "ultra"}, {"quality": []}]
)
def test_invalid_export_overrides_fail_before_building(project, monkeypatch, options):
    monkeypatch.setattr(project, "_build", lambda: pytest.fail("Invalid options must fail before building"))
    with pytest.raises(AgentError, match="EXPORT_"):
        project.preview(project.root / "output/rejected.mp4", start=0, end=1, **options)
