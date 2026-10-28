import json
from dataclasses import dataclass

import pytest
from faceless_champ import Plugin, Text, Theme
from faceless_champ import plugins as registry
from faceless_champ.theme import THEMES

from facelesschamp_kit import KitError, shot_video
from facelesschamp_kit.blocks.base import BlockBuild
from facelesschamp_kit.cli import main
from facelesschamp_kit.shots import all_shots
from facelesschamp_kit.themes import resolve_theme


@dataclass(frozen=True)
class Banner:
    """A single centered word."""

    word: str

    def compose(self, ctx, bounds):
        text = Text(self.word, role="title", position=bounds.center)
        return BlockBuild(text, {"word": text})


@pytest.fixture(autouse=True)
def plugin(monkeypatch):
    monkeypatch.setattr(registry, "_registered", {})
    monkeypatch.setattr(registry, "_report", {})
    monkeypatch.setattr(registry, "_discovered", True)
    registry.register(
        Plugin(name="banners", shots={"banner": Banner}, themes={"sunrise": Theme("sunrise", THEMES["paper"].colors)})
    )


def test_plugin_shot_and_theme_work_in_kit(tmp_path, capsys, monkeypatch):
    assert "banner" in all_shots() and "stat" in all_shots()
    video = shot_video("banner", {"word": "Hello"}, theme="sunrise", duration=2, root=tmp_path)
    assert video.composition.canvas.bg == THEMES["paper"].colors.background
    assert resolve_theme("sunrise").name == "sunrise" and resolve_theme("neon").name == "neon"
    with pytest.raises(KitError, match="sunrise"):
        resolve_theme("nope")
    monkeypatch.chdir(tmp_path)
    assert main(["shot", "--list"]) == 0
    assert json.loads(capsys.readouterr().out)["banner"] == ["word"]
    assert main(["shot", "banner", '{"word": "Hi"}', "--theme", "sunrise", "--frame", "1"]) == 0
    assert json.loads(capsys.readouterr().out.strip().splitlines()[-1])["ok"]
    assert main(["doctor"]) in (0, 1)
    assert any(item["name"] == "banners" for item in json.loads(capsys.readouterr().out)["plugins"])
