import json

import pytest
from faceless_champ import Canvas, PillowRenderer

from facelesschamp_kit import BuildContext, KitError, Project
from facelesschamp_kit.blocks import CodingPlayground
from facelesschamp_kit.cli import main
from facelesschamp_kit.scaffold import init_project


@pytest.mark.parametrize("kind", ["concept", "backend"])
def test_template_preparation_and_build_contract(tmp_path, monkeypatch, kind):
    root = init_project(tmp_path / kind, "coding-" + kind)
    project = Project(root)
    with pytest.raises(KitError) as error:
        project.validate()
    assert error.value.code == "PLAYGROUND_UNPREPARED"
    report = project.prepare()
    assert report["duration"] == 6
    assert report["prepared_assets"][0]["status"] == "prepared"
    assert set(report["segments"][0]["placements"][0]["children"]) == {"editor", "canvas", "output"}
    import subprocess

    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("Build executed code"))
    compiled = project.build()
    image = PillowRenderer(1).frame(compiled.composition, 4.4, (960, 540))
    assert image.size == (960, 540)
    project.validate()
    source = root / "videos/main.py"
    source.write_text(source.read_text().replace("duration=6", "duration=7"))
    with pytest.raises(KitError) as error:
        project.build()
    assert error.value.code == "PLAYGROUND_UNPREPARED"


def test_cli_preparation_json_and_catalog(tmp_path, capsys):
    root = init_project(tmp_path / "project", "coding-concept")
    assert main(["--project", str(root), "--json", "prepare"]) == 0
    assert json.loads(capsys.readouterr().out)["prepared_assets"][0]["status"] == "prepared"
    assert main(["list", "blocks"]) == 0
    assert "CodingPlayground" in json.loads(capsys.readouterr().out)


def test_stacked_layout_and_minimum_size(tmp_path):
    from facelesschamp_kit.playground import prepare_playground

    from facelesschamp_kit.sample_assets.coding_concept import script

    p = prepare_playground(script(), cache_dir=tmp_path / "cache")
    ctx = BuildContext(tmp_path, canvas=Canvas(1080, 1920))
    built = CodingPlayground(p, layout="stacked").compose(ctx, ctx.bounds)
    assert set(built.children) == {"editor", "canvas", "output"}
    with pytest.raises(KitError, match="minimum"):
        CodingPlayground(p, font_size=12).compose(ctx, ctx.bounds)
