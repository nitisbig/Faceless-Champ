import json
from pathlib import Path

import pytest

from facelesschamp_agent import AgentError, SelectionPlan, plan_project, select_scenes
from facelesschamp_agent.cli import main
from facelesschamp_agent.registry import CapabilityRegistry


@pytest.fixture(scope="module")
def registry():
    return CapabilityRegistry()


def context(text, cues=()):
    return {
        "fingerprint": "input-identity",
        "narration_text": text,
        "sources": [],
        "cues": list(cues),
        "duration": max((c["end"] for c in cues), default=None),
        "warnings": [],
        "truncated": False,
    }


def test_source_clock_covers_preroll_tail_and_preserves_cue_references(registry):
    cues = [
        {"id": "words#9", "start": 0.4, "end": 3, "text": "First collect the inputs."},
        {"id": "words#10", "start": 2.999, "end": 6, "text": "Then transform the inputs."},
        {"id": "words#11", "start": 7.1, "end": 9, "text": "Finally deliver the result."},
    ]
    plan = select_scenes(
        prompt="A process", context=context("", cues), registry=registry, duration=9.32, target_beat_seconds=4
    )
    assert plan.timing == "source"
    assert plan.beats[0].start == 0
    assert sum(b.duration for b in plan.beats) == pytest.approx(9.32)
    assert [c for b in plan.beats for c in b.cue_ids] == [c["id"] for c in cues]
    assert plan.beats[1].start == 2.999
    assert cues[1]["start"] == 2.999
    assert SelectionPlan.model_validate_json(plan.model_dump_json()) == plan


def test_cannot_trim_source_clock_and_short_clocks_stay_positive(registry):
    cues = [{"id": "x", "start": 0, "end": 0.01, "text": "A word"}]
    assert select_scenes(prompt="Tiny", context=context("", cues), registry=registry).beats[0].duration == 0.01
    with pytest.raises(AgentError, match="SOURCE_DURATION"):
        select_scenes(prompt="Tiny", duration=0.001, context=context("", cues), registry=registry)


@pytest.mark.parametrize(
    ("text", "intent", "selected"),
    [
        ("Before each call repeats work. After caching, reuse the result.", "comparison", "recipe:before-after"),
        ("The request travels from the client to the server.", "journey", "recipe:request-journey"),
        ("This time series shows the trend over time.", "trend", "recipe:annotated-trend"),
        ("The parent has two child nodes in this hierarchy.", "hierarchy", "recipe:hierarchy"),
        ("First collect inputs, then transform them, finally deliver.", "sequence", "recipe:process-flow"),
    ],
)
def test_relationship_selection_is_explainable_without_copying_recipe_data(registry, text, intent, selected):
    plan = select_scenes(prompt=text, context=context(text), registry=registry, duration=6)
    beat = plan.beats[0]
    assert beat.intent == intent
    assert beat.selected_capability == selected
    assert beat.evidence and beat.selection_rationale and beat.layout_checks
    assert len(beat.candidates) <= 4
    assert all("example" not in candidate and "guide" not in candidate for candidate in beat.candidates)
    assert beat.requires_authoring
    if intent == "trend":
        assert any("Sourced values" in item for item in beat.required_inputs)


def test_custom_design_and_instructions_override_defaults_without_mutating_them(registry):
    user = "Full screen editor. No headings, callouts or transitions."
    plan = select_scenes(
        prompt="Explain a Python function",
        instructions=user,
        design={"theme": "light", "body_size": 52, "palette": {"accent": "#345678"}},
        context=context("Explain a Python function"),
        registry=registry,
    )
    assert plan.instructions == [user]
    assert plan.design.theme == "light" and plan.design.body_size == 52
    assert plan.design.palette["accent"] == "#345678"
    default = select_scenes(prompt="A subject", context=context("A subject"), registry=registry)
    assert default.design.theme == "clean-flow" and default.design.body_size == 44
    assert default.guidelines["precedence"][0] == "explicit user instructions"
    assert plan.timing == "estimated" and plan.editorial_review == "pending"


def test_empty_and_invalid_requests_are_scoped(registry):
    for kwargs in (
        {"prompt": ""},
        {"prompt": "x", "duration": float("inf")},
        {"prompt": "x", "candidate_limit": 0},
        {"prompt": "x", "instructions": [""]},
    ):
        with pytest.raises(AgentError):
            select_scenes(context=context("x"), registry=registry, **kwargs)


def test_plan_reuses_identical_artifacts_and_refreshes_changes(tmp_path):
    script = tmp_path / "voiceover.md"
    script.write_text("First collect inputs. Then deliver the result.")
    request = {"prompt": "Explain this process", "duration": 6}
    first = plan_project(tmp_path, **request)
    second = plan_project(tmp_path, **request)
    assert second["reused"] and first["selection"] == second["selection"]
    Path(second["context"]).write_text("{}")
    assert not plan_project(tmp_path, **request)["reused"]
    script.write_text("Before requests repeated work. After caching reuse results.")
    changed = plan_project(tmp_path, **request)
    assert changed["selection"] != first["selection"]
    custom = plan_project(tmp_path, **request, instructions=["Use a light palette"])
    assert changed["selection"] != custom["selection"]
    (tmp_path / "future-icon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    assert plan_project(tmp_path, **request)["selection"] != changed["selection"]


def test_cli_plans_without_an_existing_executable_project(tmp_path, monkeypatch, capsys):
    root = tmp_path / "new-video"
    root.mkdir()
    (root / "voicover.md").write_text("First collect inputs, then deliver the result.")
    monkeypatch.chdir(tmp_path)
    assert (
        main(
            [
                "--project",
                str(root),
                "plan",
                "--prompt",
                "Teach this process",
                "--instructions",
                "No headings",
                "--format",
                "shorts",
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)["result"]
    plan = SelectionPlan.model_validate_json(Path(result["selection"]).read_text())
    assert plan.format == "shorts" and plan.instructions == ["No headings"]
    assert not (root / "agent-plan.json").exists()


def test_planning_keeps_existing_plan_and_scene_source(project):
    before = {p: (project.root / p).read_bytes() for p in ("agent-plan.json", "videos/main.py")}
    result = plan_project(project.root, prompt="Improve scene direction")
    assert result["status"] == "ready_for_authoring"
    assert all((project.root / p).read_bytes() == data for p, data in before.items())


def test_project_direction_is_inherited_before_partial_user_overrides(tmp_path, registry):
    original = {
        "design": {
            "theme": "light",
            "font": "assets/Custom.ttf",
            "body_size": 54,
            "palette": {"background": "#F0F0F0", "accent": "#CC3300"},
        },
        "brief": {"constraints": ["No captions", "Use a full-screen editor"]},
    }
    path = tmp_path / "agent-plan.json"
    path.write_text(json.dumps(original))
    plan = select_scenes(
        tmp_path,
        prompt="Use recipe:before-after to explain the comparison",
        instructions=["Use faceless_champ.FlowChamp", "Allow captions"],
        design={"body_size": 56, "palette": {"accent": "#335577"}},
        context=context("Before this was slow. After the change it is fast."),
        registry=registry,
    )
    assert plan.design.theme == "light" and plan.design.body_size == 56
    assert plan.design.font == "assets/Custom.ttf"
    assert plan.design.palette == {"background": "#F0F0F0", "accent": "#335577"}
    assert plan.instructions == ["Use faceless_champ.FlowChamp", "Allow captions"]
    assert plan.guidelines["project_constraints"] == original["brief"]["constraints"]
    assert plan.beats[0].selected_capability == "faceless_champ.FlowChamp"
    assert json.loads(path.read_text()) == original


def test_project_duration_hold_and_portrait_format_are_inherited(tmp_path, registry):
    (tmp_path / "agent-plan.json").write_text(json.dumps({"brief": {"duration": 12.32, "format": "shorts"}}))
    source = context(
        "", [{"id": "words#7", "start": 0.4, "end": 12, "text": "First show the subject, then its result."}]
    )
    inherited = select_scenes(tmp_path, prompt="Teach this idea", context=source, registry=registry)
    assert inherited.duration == 12.32 and inherited.format == "shorts"
    assert inherited.beats[-1].start + inherited.beats[-1].duration == pytest.approx(12.32)
    assert "portrait" in inherited.beats[0].composition
    explicit = select_scenes(
        tmp_path, prompt="Teach this idea", duration=13, format="landscape", context=source, registry=registry
    )
    assert explicit.duration == 13 and explicit.format == "landscape"
    with pytest.raises(AgentError, match="SOURCE_DURATION"):
        select_scenes(tmp_path, prompt="Teach this idea", duration=11, context=source, registry=registry)


def test_stale_project_duration_extends_to_the_complete_source_clock(tmp_path, registry):
    (tmp_path / "agent-plan.json").write_text(json.dumps({"brief": {"duration": 8, "format": "shorts"}}))
    source = context("", [{"id": "words#9", "start": 0, "end": 12, "text": "A complete idea."}])
    plan = select_scenes(tmp_path, prompt="Teach the full idea", context=source, registry=registry)
    assert plan.duration == 12
    assert any("brief.duration" in warning and "extended" in warning for warning in plan.warnings)


def test_new_project_format_defaults_to_landscape(tmp_path, registry):
    plan = select_scenes(tmp_path, prompt="A new subject", context=context("A new subject"), registry=registry)
    assert plan.format == "landscape"


def test_full_screen_user_direction_precedes_prompt_and_recipe_heuristics(tmp_path, registry):
    plan = select_scenes(
        tmp_path,
        prompt="Use recipe:before-after",
        instructions=["Full screen editor. No headings, callouts or transitions."],
        context=context("Before each call was slow. After caching reuse the result."),
        registry=registry,
    )
    beat = plan.beats[0]
    assert beat.selected_capability == "facelesschamp_kit.blocks.CodeEditor"
    assert "across the full frame" in beat.composition
    assert "requested treatment takes priority" in beat.selection_rationale
    assert beat.candidates[0]["reasons"] == ["User/project direction: full-screen editor direction"]


def test_explicit_capability_exclusions_are_respected(tmp_path, registry):
    plan = select_scenes(
        tmp_path,
        prompt="Explain the before and after comparison",
        instructions=["Do not use recipe:before-after"],
        context=context("Before repeated work. After reuse the result."),
        registry=registry,
    )
    assert all(candidate["id"] != "recipe:before-after" for candidate in plan.beats[0].candidates)


def test_exact_recipe_id_supports_markdown_quoting(tmp_path, registry):
    plan = select_scenes(
        tmp_path,
        prompt="A request travels from the client to the server",
        instructions=["Use `recipe:before-after`."],
        context=context("The request travels from the client to the server."),
        registry=registry,
    )
    assert plan.beats[0].selected_capability == "recipe:before-after"


def test_retrieval_uses_bounded_supplement_hints_and_compact_asset_refs(tmp_path, registry, monkeypatch):
    source = context("An abstract idea needs a clear representation.")
    source["sources"] = [
        {
            "path": "measurements.json",
            "kind": "data",
            "size": 20000,
            "checksum": "data-hash",
            "text": "laboratory calibration microscope " * 1000,
        }
    ]
    source["assets"] = [
        {"path": "assets/custom.woff2", "kind": "font", "size": 100, "checksum": "font-hash"},
        {"path": "assets/icon.svg", "kind": "icon", "size": 20, "checksum": "icon-hash"},
    ]
    queries = []
    recommend = registry.recommend

    def capture(query, **kwargs):
        queries.append(query)
        return recommend(query, **kwargs)

    monkeypatch.setattr(registry, "recommend", capture)
    plan = select_scenes(
        tmp_path,
        prompt="Teach microscope calibration",
        instructions="Use spatial annotations",
        context=source,
        registry=registry,
    )
    assert "microscope" in queries[0] and "spatial annotations" in queries[0]
    assert "calibration" in queries[0] and len(queries[0]) < 2500
    assert {entry["path"] for entry in plan.sources} == {"measurements.json", "assets/custom.woff2", "assets/icon.svg"}
    assert all("text" not in entry for entry in plan.sources)
    assert "laboratory calibration microscope " * 2 not in plan.model_dump_json()


def test_unrelated_supplements_cannot_replace_overview_intent(tmp_path, registry):
    source = context("The subject is a subtle phenomenon.")
    source["sources"] = [
        {
            "path": "unrelated.py",
            "kind": "code",
            "size": 30,
            "checksum": "unrelated-code",
            "text": "The Python function uses code and syntax.",
        }
    ]
    plan = select_scenes(tmp_path, prompt="Explain the subject", context=source, registry=registry)
    assert plan.beats[0].intent == "overview"
    assert not any("Supplement reference:" in item for item in plan.beats[0].evidence)


def test_cached_planning_skips_recommendations_and_recovers_tampering(tmp_path, registry, monkeypatch):
    (tmp_path / "voiceover.md").write_text("First collect inputs, then transform them, finally deliver the result.")
    first = plan_project(tmp_path, prompt="Explain the process", registry=registry)
    recommend = registry.recommend

    def unexpected(*args, **kwargs):
        pytest.fail("A valid cache hit must not rank capabilities again")

    monkeypatch.setattr(registry, "recommend", unexpected)
    second = plan_project(tmp_path, prompt="Explain the process", registry=registry)
    assert second["reused"] and second["selection"] == first["selection"]
    assert "context and selection" in second["next_actions"][0]
    monkeypatch.setattr(registry, "recommend", recommend)
    path = Path(first["selection"])
    data = json.loads(path.read_text())
    data["beats"][0]["purpose"] = "A valid but tampered cache value"
    path.write_text(json.dumps(data))
    assert not plan_project(tmp_path, prompt="Explain the process", registry=registry)["reused"]
    assert json.loads(path.read_text())["beats"][0]["purpose"] != "A valid but tampered cache value"


def test_cache_identity_includes_budgets_config_and_algorithm(tmp_path, registry, monkeypatch):
    from facelesschamp_agent import planning

    (tmp_path / "voiceover.md").write_text("An idea to explain.")
    (tmp_path / "cue-per-word.srt").write_text("7\n00:00:00,000 --> 00:00:05,000\nAn idea to explain.\n")
    request = {"prompt": "Explain the supplied subject", "registry": registry}
    short = plan_project(tmp_path, max_chars=5, **request)
    before = Path(short["selection"]).read_bytes()
    complete = plan_project(tmp_path, max_chars=500, **request)
    assert complete["selection"] != short["selection"]
    assert Path(short["selection"]).read_bytes() == before
    config = tmp_path / "agent-plan.json"
    config.write_text(json.dumps({"design": {"theme": "light"}, "brief": {"constraints": ["Use brief labels"]}}))
    constrained = plan_project(tmp_path, paths=["voiceover.md", "cue-per-word.srt"], **request)
    config.write_text(json.dumps({"design": {"theme": "whiteboard"}, "brief": {"constraints": ["Use brief labels"]}}))
    changed = plan_project(tmp_path, paths=["voiceover.md", "cue-per-word.srt"], **request)
    assert changed["selection"] != constrained["selection"]
    changed_plan = json.loads(Path(changed["selection"]).read_text())
    assert changed_plan["design"]["theme"] == "whiteboard"
    assert any(source["path"] == "agent-plan.json" for source in changed_plan["sources"])
    monkeypatch.setattr(planning, "PLANNING_VERSION", planning.PLANNING_VERSION + 1)
    new_algorithm = plan_project(tmp_path, paths=["voiceover.md", "cue-per-word.srt"], **request)
    assert new_algorithm["selection"] != changed["selection"]
    monkeypatch.setattr(planning, "_implementation_digest", lambda: "new-installed-implementation")
    assert (
        plan_project(tmp_path, paths=["voiceover.md", "cue-per-word.srt"], **request)["selection"]
        != new_algorithm["selection"]
    )


def test_implementation_identity_hashes_actual_planner_and_model_bytes(tmp_path, monkeypatch):
    from facelesschamp_agent import planning

    for name in ("planning.py", "models.py", "registry.py", "context.py"):
        (tmp_path / name).write_text("# Initial installed source\n")
    monkeypatch.setattr(planning, "__file__", str(tmp_path / "planning.py"))
    initial = planning._implementation_digest()
    (tmp_path / "models.py").write_text("# Updated validation semantics\n")
    model_changed = planning._implementation_digest()
    assert model_changed != initial
    (tmp_path / "planning.py").write_text("# Updated scene selection semantics\n")
    assert planning._implementation_digest() != model_changed


def test_generator_instructions_survive_validation_and_cache(tmp_path, registry):
    (tmp_path / "voiceover.md").write_text("A small subject")
    first = plan_project(tmp_path, prompt="Explain this", instructions=(v for v in ["No headings"]), registry=registry)
    second = plan_project(tmp_path, prompt="Explain this", instructions=(v for v in ["No headings"]), registry=registry)
    assert first["instructions"] == ["No headings"] and second["reused"]


def test_nested_guidelines_do_not_mutate_defaults(tmp_path, registry):
    first = select_scenes(tmp_path, prompt="An idea", context=context("An idea"), registry=registry)
    first.guidelines["precedence"].append("Changed by a consumer")
    first.guidelines["canvas"]["landscape"][0] = 999
    second = select_scenes(tmp_path, prompt="An idea", context=context("An idea"), registry=registry)
    assert second.guidelines["precedence"] == [
        "explicit user instructions",
        "project design and constraints",
        "defaults below",
    ]
    assert second.guidelines["canvas"]["landscape"] == [1920, 1080]


def test_untimed_incomplete_narration_is_rejected(tmp_path, registry):
    (tmp_path / "voiceover.md").write_text("A long narration cannot be represented by its initial excerpt alone.")
    with pytest.raises(AgentError, match="CONTEXT_INCOMPLETE"):
        plan_project(tmp_path, prompt="Cover the complete narration", max_chars=8, registry=registry)


def test_invalid_or_external_project_direction_is_structured(tmp_path, registry):
    root = tmp_path / "project"
    root.mkdir()
    config = root / "agent-plan.json"
    config.write_text("Not JSON")
    with pytest.raises(AgentError, match="PROJECT_DIRECTION"):
        select_scenes(root, prompt="A subject", context=context("A subject"), registry=registry)
    config.unlink()
    outside = tmp_path / "outside.json"
    outside.write_text("{}")
    config.symlink_to(outside)
    with pytest.raises(AgentError, match="PROJECT_DIRECTION"):
        select_scenes(root, prompt="A subject", context=context("A subject"), registry=registry)
