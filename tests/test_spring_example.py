"""Keep the public spring showcase renderable and its advertised content visible."""

import runpy
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from faceless_champ import Group, Polyline, Sequence, Text

EXAMPLE = Path(__file__).resolve().parents[1] / "examples/spring_motion/render.py"


@pytest.fixture(scope="module")
def example():
    return runpy.run_path(str(EXAMPLE))


def test_showcase_timing_equal_travel_and_terminal_holds(example):
    shots = example["build_shots"]()
    assert [shot.scene.duration for shot in shots] == [4, 3, 3]
    assert Sequence(*(shot.scene for shot in shots)).duration == 10
    comparison = shots[0].scene
    motions = [track for entry in comparison.entries for track in entry.tracks if track.property == "position"]
    assert len(motions) == 5
    for track in motions:
        assert track.initial[0] == track.target[0]
        assert track.initial[1] - track.target[1] == 160
        assert track.start == 0.45
        assert track.duration == pytest.approx(2.6)
    for shot in shots:
        last_end = max(track.start + track.duration for entry in shot.scene.entries for track in entry.tracks)
        assert shot.scene.duration - last_end >= 0.5


def test_showcase_sampled_safe_margins(example):
    result = example["audit_layout"](example["build_shots"]())
    assert result["minimum_canvas_clearance_px"] >= 20


def test_text_connections_and_group_members_are_visible_at_rest(example):
    _, transforms, network = example["build_shots"]()
    words = [
        entry
        for entry in transforms.scene.entries
        if isinstance(entry.component, Text) and "Words" in entry.component.text
    ]
    assert len(words) == 1
    assert words[0].state_at(2.9)["opacity"] == 1
    edges = [entry for entry in network.scene.entries if isinstance(entry.component, Polyline)]
    assert len(edges) == 4
    assert all(entry.state_at(2.9)["opacity"] == 1 for entry in edges)
    groups = [visual for visual in transforms.visuals if isinstance(visual, Group)]
    assert any(
        len(group.children) == 3 and all(isinstance(child, Group) for child in group.children) for group in groups
    )


def test_storyboard_cli_uses_public_preview_path_and_protects_outputs(tmp_path):
    output = tmp_path / "preview.mp4"
    command = [sys.executable, str(EXAMPLE), "--storyboard-only", "--output", str(output)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    board = tmp_path / "storyboard/storyboard.png"
    with Image.open(board) as image:
        assert image.size == (1440, 1216)
    assert not output.exists()
    rejected = subprocess.run(command, check=False, capture_output=True, text=True)
    assert rejected.returncode != 0
    assert "FileExistsError" in rejected.stderr
