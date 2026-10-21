"""Agent policy stays above Kit production, using exactly the validated object."""

import importlib.util
import json
from importlib.resources import files
from pathlib import Path

import pytest
from faceless_champ import ExportProgress as CoreProgress
from facelesschamp_kit import CompiledVideo, ExportProgress
from PIL import Image


def test_agent_delegates_exact_compiled_object_once(project, monkeypatch):
    original_build = project._build
    builds, calls = [], []

    def build():
        result = original_build()
        builds.append(result[0])
        return result

    original_save, original_export = CompiledVideo.save_frame, CompiledVideo.export

    def save(self, *args, **kwargs):
        calls.append(self)
        return original_save(self, *args, **kwargs)

    def export(self, *args, **kwargs):
        calls.append(self)
        return original_export(self, *args, **kwargs)

    monkeypatch.setattr(project, "_build", build)
    monkeypatch.setattr(CompiledVideo, "save_frame", save)
    monkeypatch.setattr(CompiledVideo, "export", export)
    frame = project.frame(0.75)
    preview = project.preview(start=0.5, end=0.7, fps=10)
    assert len(builds) == len(calls) == 2
    assert all(a is b for a, b in zip(builds, calls, strict=True))
    assert frame["artifacts"][0]["source_time"] == 0.75
    assert preview["source_range"] == [0.5, 0.7] and preview["status"] == "exported"
    assert project.verify(preview["artifacts"][0]["path"])["status"] == "passed"
    assert ExportProgress is CoreProgress


def test_failed_kit_export_records_no_success_and_retry_works(project, monkeypatch):
    records = project.state / "records"
    before = set(records.glob("*.json"))

    def fail(*args, **kwargs):
        raise RuntimeError("encoder failed")

    with monkeypatch.context() as patch:
        patch.setattr(CompiledVideo, "export", fail)
        with pytest.raises(RuntimeError, match="encoder failed"):
            project.preview(start=0, end=0.2)
    assert set(records.glob("*.json")) == before
    assert project.preview(start=0, end=0.2, fps=10)["status"] == "exported"


def test_recipe_atlas_allocates_all_rows(tmp_path):
    path = Path(__file__).resolve().parents[1] / "scripts/release_evidence.py"
    spec = importlib.util.spec_from_file_location("release_evidence", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    poster = tmp_path / "poster.png"
    Image.new("RGB", (16, 9), "red").save(poster)
    gallery = module.recipe_gallery([(str(i), poster) for i in range(11)])
    assert gallery.size == (960, 6 * 310)
    assert gallery.getpixel((10, 5 * 310 + 10)) == (255, 0, 0)


def test_packaged_schemas_and_metadata_match_models():
    from facelesschamp_kit import public_capabilities

    from facelesschamp_agent.models import BenchmarkResult, QualityReport, VideoPlan

    resources = files("facelesschamp_agent").joinpath("resources")
    for name, model in (
        ("video-plan", VideoPlan),
        ("quality-report", QualityReport),
        ("benchmark-result", BenchmarkResult),
    ):
        assert json.loads(resources.joinpath(f"{name}.schema.json").read_text()) == model.model_json_schema()
    static = json.loads(resources.joinpath("public-capabilities.json").read_text())
    for name, package in public_capabilities()["packages"].items():
        assert static["packages"][name]["exports"] == package["exports"]
        assert static["packages"][name]["version"] == package["version"]
