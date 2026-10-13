import pytest
from faceless_champ import Canvas, PillowRenderer
from facelesschamp_kit import BuildContext, Video
from facelesschamp_kit.recipes import apply_recipe
from facelesschamp_kit.themes import LIGHT, MIDNIGHT

from facelesschamp_agent.examples import prepare_example


@pytest.mark.parametrize("size", [(1920, 1080), (1080, 1920)])
@pytest.mark.parametrize("theme", [LIGHT, MIDNIGHT])
def test_code_result_replays_in_both_formats(tmp_path, size, theme, monkeypatch):
    prepared = prepare_example(tmp_path / "prepared")

    def forbidden(*args, **kwargs):
        raise AssertionError("Replay must not execute code")

    monkeypatch.setattr("subprocess.run", forbidden)
    video = Video(BuildContext(tmp_path, Canvas(*size, theme.background), theme))
    apply_recipe(video.segment("lesson", duration=4), "code-result", {"prepared": str(prepared.directory)})
    compiled = video.compile()
    for time in (0, 0.7, 2.7, 3.95):
        assert PillowRenderer(1).frame(compiled.composition, time, (320, 180)).size == (320, 180)
