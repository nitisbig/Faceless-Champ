"""Migrated public APIs, frozen rendering and chess discovery absence."""

import hashlib
import importlib
import json
import runpy
from importlib.metadata import version
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def test_moved_public_names_are_owned_by_kit():
    import faceless_champ as core

    import facelesschamp_kit as kit

    assert len(core._MOVED) == 52
    for name, module in core._MOVED.items():
        assert name not in core.__all__
        assert getattr(kit, name) is getattr(importlib.import_module(module), name)
    for name in ("ArchMesh", "ArchPart", "ArchStyle", "ArchCamera"):
        assert getattr(core, name).__module__.startswith("faceless_champ.integrations.pyvista")


def test_full_domain_fixture_pixels_match_frozen_reference(tmp_path):
    from faceless_champ import PillowRenderer

    reference = json.loads((ROOT / "tests/fixtures/m1-v1-reference.json").read_text())
    if {name: version(name) for name in reference["versions"]} != reference["versions"]:
        pytest.skip("Exact pixels require the frozen Pillow/font stack")
    scenes = runpy.run_path(str(ROOT / "tests/fixtures/minimal_scenes.py"))["scenes"](tmp_path)
    for name, node in scenes.items():
        with PillowRenderer() as renderer:
            renderer.validate(node)
            for time in (0, 0.35, 1.25, 1.9, 0.35):
                digest = hashlib.sha256(renderer.frame(node, time, (320, 180)).tobytes()).hexdigest()
                assert digest == reference["frames"][f"{name}:{time}"], (name, time)


def test_chess_starter_and_blocks_are_unavailable(tmp_path):
    from facelesschamp_kit import blocks, templates
    from facelesschamp_kit.diagnostics import KitError
    from facelesschamp_kit.scaffold import init_project

    assert not hasattr(blocks, "ChessBoard")
    assert not hasattr(templates, "chesschamp")
    with pytest.raises(KitError, match="Choose"):
        init_project(tmp_path / "retired", "chesschamp")
    assert not (tmp_path / "retired").exists()
