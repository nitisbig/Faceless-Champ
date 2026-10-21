"""Executable, editable examples used by the release evidence generator."""

from importlib.resources import files

from facelesschamp_kit.playground import CanvasItem, CodeCheckpoint, PlaygroundScript, ValueBinding, prepare_playground

from .models import VideoPlan
from .project import AgentProject, init_project


def prepare_example(directory):
    """Explicitly execute a tiny deterministic code/result lesson."""
    source = 'from facelesschamp_kit.playground import runtime\n\nvalues = [2, 4, 6]\ntotal = sum(values)\nruntime.emit("total", total)\nprint("Total:", total)\n'
    script = PlaygroundScript(
        [
            CodeCheckpoint("first", {"lesson.py": source}, "lesson.py", "lesson.py", 0, 0.5, 0.6),
            CodeCheckpoint(
                "change",
                {"lesson.py": source.replace("[2, 4, 6]", "[4, 8, 12]")},
                "lesson.py",
                "lesson.py",
                2,
                2.5,
                2.6,
            ),
        ],
        duration=4,
        mode="backend",
        items=[CanvasItem("total", "variable", "Computed total")],
        bindings=[ValueBinding("total", "total")],
    )
    return prepare_playground(script, cache_dir=directory, timeout=10)


def create_example(destination, kind):
    root = init_project(destination)
    project = AgentProject(root)
    raw = project.plan.model_dump(mode="json")
    raw["brief"].update(title=kind, prompt=f"Explain {kind}")
    if kind == "narrated-system":
        asset_root = files("facelesschamp_kit").joinpath("sample_assets")
        for filename in ("voiceover.wav", "word-cues.srt"):
            (root / filename).write_bytes(asset_root.joinpath(filename).read_bytes())
        raw["brief"].update(duration=30, narration={"audio": "voiceover.wav", "subtitles": "word-cues.srt"})
        rows = [
            (
                "components",
                "process-flow",
                {"steps": ["Content", "Layout", "Motion"]},
                "Reusable video components combine content, layout and motion",
            ),
            (
                "reuse",
                "before-after",
                {"before": "Repeat setup for every project", "after": "Compose shared building blocks"},
                "Shared blocks improve structure and consistency",
            ),
            (
                "production",
                "process-flow",
                {"steps": ["Compose", "Preview", "Export"]},
                "The production system preserves source narration timing",
            ),
        ]
        raw["scenes"] = [
            {
                "id": name,
                "start": i * 10,
                "duration": 10,
                "purpose": purpose,
                "recipe": recipe,
                "content": content,
                "attention_sequence": ["Introduce relationship", "Emphasize result"],
                "key_events": [{"at": 1, "label": "Introduce"}, {"at": 6.2, "label": "Result"}],
            }
            for i, (name, recipe, content, purpose) in enumerate(rows)
        ]
        raw["brief"]["constraints"] = ["Bundled synthetic demonstration speech; not a generated voice provider"]
    elif kind == "chart-explanation":
        raw["brief"]["duration"] = 6
        raw["design"]["theme"] = "light"
        raw["scenes"] = [
            {
                "id": "trend",
                "purpose": "Explain a change in illustrative throughput",
                "start": 0,
                "duration": 6,
                "recipe": "annotated-trend",
                "illustrative": True,
                "content": {
                    "points": [[0, 20], [1, 22], [2, 24], [3, 48], [4, 52]],
                    "label": "Illustrative requests / second",
                    "annotation": "Capacity doubles after adding a worker",
                },
                "key_events": [{"at": 3, "label": "Annotate change"}],
            }
        ]
    elif kind == "code-result":
        prepared = prepare_example(root / ".playground-cache")
        raw["brief"]["duration"] = 4
        raw["scenes"] = [
            {
                "id": "computed",
                "purpose": "Show how changing inputs changes the computed result",
                "start": 0,
                "duration": 4,
                "recipe": "code-result",
                "content": {"prepared": str(prepared.directory.relative_to(root))},
                "key_events": [{"at": 0.6, "label": "First output"}, {"at": 2.6, "label": "Updated output"}],
            }
        ]
    else:
        raise ValueError(f"Unknown example {kind}")
    raw["story"] = {
        "thesis": raw["brief"]["intended_understanding"],
        "beats": [{"scene_id": s["id"], "idea": s["purpose"], "purpose": s["purpose"]} for s in raw["scenes"]],
    }
    plan = VideoPlan.model_validate(raw)
    project.plan_path.write_text(plan.model_dump_json(indent=2) + "\n")
    config = root / "facelesschamp.toml"
    config.write_text(config.read_text().replace('theme = "midnight"', f'theme = "{plan.design.theme}"'))
    (root / "narration.md").write_text(
        "# Narration\n\n" + (root / "word-cues.srt").read_text()
        if kind == "narrated-system"
        else "# Narration draft\n\n" + "\n\n".join(s.purpose for s in plan.scenes) + "\n"
    )
    return project
