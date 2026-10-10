"""Timeline and CLI acceptance checks; exports are tested separately as excerpts."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))
from scene.audit import check
from scene.story import build_video

from faceless_champ import Number


@pytest.fixture(scope="module")
def built():
    return build_video()


def test_complete_timeline_and_audio(built):
    video, report = built
    assert check(video, report)["passed"]
    assert len(report["chapters"]) == 9


def test_health_is_correct_when_each_result_is_spoken(built):
    video, _ = built
    scene = video.children[0].children[7]
    numbers = [entry for entry in scene.entries if isinstance(entry.component, Number)]
    for source_time, expected in [(113.8, [70, 100]), (117.31, [85, 100]), (121, [85, 90])]:
        assert [round(e.state_at(source_time - scene.start_time)["value"]) for e in numbers] == expected


@pytest.mark.parametrize("theme", ["ocean", "paper"])
def test_other_themes_keep_valid_layout(theme):
    video, report = build_video(theme)
    assert check(video, report)["passed"]


def test_cli_check_from_another_directory(tmp_path):
    result = subprocess.run(
        [sys.executable, str(PROJECT / "render.py"), "--check"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout)["passed"]


def test_cli_rejects_invalid_fps_without_export():
    result = subprocess.run(
        [sys.executable, str(PROJECT / "render.py"), "--fps", "24"], capture_output=True, text=True, check=False
    )
    assert result.returncode != 0 and "invalid choice" in result.stderr
