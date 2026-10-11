from types import SimpleNamespace

import pytest
from faceless_champ import Canvas, PillowRenderer
from faceless_champ.os_ui import OSScript

from facelesschamp_kit import Video
from facelesschamp_kit.blocks import FinderWindow, OSWalkthrough, SettingsWindow
from facelesschamp_kit.context import BuildContext
from facelesschamp_kit.diagnostics import KitError
from facelesschamp_kit.project import Project
from facelesschamp_kit.scaffold import init_project


@pytest.mark.parametrize("block_type", [FinderWindow, SettingsWindow, OSWalkthrough])
@pytest.mark.parametrize("canvas", [Canvas(1920, 1080), Canvas(1080, 1920)])
def test_fresh_blocks_fit_and_render(tmp_path, block_type, canvas):
    ctx = BuildContext(tmp_path, canvas=canvas)
    block = block_type(script=OSScript().wait(1))
    first, second = block.compose(ctx, ctx.bounds), block.compose(ctx, ctx.bounds)
    assert first.root is not second.root
    assert first.bounds.left >= ctx.bounds.left - 1
    assert first.bounds.bottom <= ctx.bounds.bottom + 1
    video = Video(ctx)
    video.segment("ui", duration=1).add(block)
    compiled = video.compile()
    PillowRenderer(1).frame(compiled.composition, 0.5, (216, 384) if canvas.height > canvas.width else (384, 216))


def test_script_overflow_and_narration_tail_cannot_extend_actions(tmp_path):
    for voice in (None, SimpleNamespace(duration=8, track=None)):
        video = Video(BuildContext(tmp_path))
        video.voice = voice
        video.segment("ui", duration=2).add(OSWalkthrough(script=OSScript().wait(3)))
        with pytest.raises(KitError, match="MOTION_WINDOW"):
            video.compile()


def test_placement_offset_and_source_start(tmp_path):
    video = Video(BuildContext(tmp_path, canvas=Canvas(1920, 1080)))
    script = OSScript().open_settings().set_value("appearance:theme", "dark")
    video.segment("ui", start=3, duration=3).add(OSWalkthrough(script=script, source_start=1), at=1, duration=1)
    compiled = video.compile()
    renderer = PillowRenderer(1)
    assert (
        renderer.frame(compiled.composition, 4.1, (384, 216)).tobytes()
        != renderer.frame(compiled.composition, 4.9, (384, 216)).tobytes()
    )


def test_scaffold_os_ui(tmp_path):
    root = tmp_path / "demo"
    init_project(root, template="os-ui")
    assert "landscape" in (root / "facelesschamp.toml").read_text()
    assert "0.1.0rc5" in (root / "pyproject.toml").read_text()
    project = Project(root)
    compiled = project.build("main")
    assert compiled.duration == 35


def test_narration_cues_keep_the_source_clock(tmp_path):
    import wave

    with wave.open(str(tmp_path / "voice.wav"), "wb") as audio:
        audio.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
        audio.writeframes(b"\0\0" * 32000)
    (tmp_path / "cues.srt").write_text(
        "7\n00:00:01,000 --> 00:00:02,001\nDark mode\n\n19\n00:00:02,000 --> 00:00:03,000\nHold\n"
    )
    video = Video(BuildContext(tmp_path, canvas=Canvas(1920, 1080)))
    video.narration(audio="voice.wav", subtitles="cues.srt", markers={"change": 7}, overlap_tolerance=0.001)
    segment = video.segment("settings", duration=3)
    script = OSScript().set_value("appearance:theme", "dark", at=segment.cue_time(7))
    segment.add(SettingsWindow(script=script))
    compiled = video.compile()
    assert compiled.duration == 4
    assert len(compiled.composition.audio) == 1
    assert compiled.composition.audio[0].start == 0
    clip = compiled.composition.entries[0].component
    assert clip.state_at(1.59)["appearance"] == "light"
    assert clip.state_at(1.6)["appearance"] == "dark"
    assert video.voice.track.cue(7).end == 2.001
    assert video.voice.track.cue(19).start == 2
