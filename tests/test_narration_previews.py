import pytest
from PIL import Image as PILImage

from faceless_champ import (
    Canvas,
    CueScene,
    FadeIn,
    PillowRenderer,
    Scene,
    Sequence,
    Square,
    StoryboardSample,
    SubtitleCue,
    SubtitleTrack,
    render_storyboard,
    save_frame,
)


@pytest.fixture
def words():
    return SubtitleTrack(
        [
            SubtitleCue(1, 0.06, 1, "Before"),
            SubtitleCue(4, 2.5, 3, "growth"),
            SubtitleCue(7, 3, 4, "continues"),
            SubtitleCue(8, 4, 5, "after"),
        ]
    )


def test_cue_scene_keeps_source_edges_offsets_and_sequence_clock(words):
    first = CueScene(words, Canvas(160, 240), end_time=2.5).finish()
    second = CueScene(words, first.canvas, start_time=2.5, end_time=4)
    square = Square(20, position=(80, 120), fill="red", stroke=None)
    with second.at_cue(4):
        second.play(FadeIn(square), run_time=0.25)
    with second.at_cue(7, edge="end"):
        second.remove(square)
    assert second.cue_time(7, offset=-0.25) == 0.25
    assert second.cue_time(4, edge="end") == 0.5
    assert second.finish().duration == 1.5
    combined = Sequence(first, second)
    assert combined.starts == [0, 2.5]
    assert combined.duration == 4
    renderer = PillowRenderer(1)
    assert renderer.frame(combined, 2.49, (160, 240)).getpixel((80, 120))[:3] == (0, 0, 0)
    assert renderer.frame(combined, 2.75, (160, 240)).getpixel((80, 120))[:3] == (255, 0, 0)
    assert [(c.start, c.end) for c in words.cues] == [(0.06, 1), (2.5, 3), (3, 4), (4, 5)]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"index": 1},
        {"index": 8},
        {"index": True},
        {"index": 0},
        {"index": 4, "edge": "middle"},
        {"index": 4, "offset": -0.01},
        {"index": 7, "offset": 2},
        {"index": 4, "offset": float("nan")},
    ],
)
def test_cue_scene_rejects_outside_events_and_invalid_inputs(words, kwargs):
    scene = CueScene(words, start_time=2.5, end_time=4)
    with pytest.raises(ValueError):
        scene.cue_time(**kwargs)
    assert scene.time == 0


def test_cue_scene_tail_and_overflow(words, tone):
    assert CueScene(words, start_time=4, end_time=5.5).finish().duration == 1.5
    scene = CueScene(words, start_time=2.5, end_time=4)
    with scene.at_cue(7):
        scene.play(FadeIn(Square()), run_time=1.01)
    with pytest.raises(ValueError, match="extends beyond"):
        scene.finish()
    audio = CueScene(words, start_time=2.5, end_time=4)
    audio.add_audio(tone, start=0)
    with pytest.raises(ValueError, match="extends beyond"):
        audio.finish()
    with pytest.raises(TypeError):
        CueScene("not a track")
    for kwargs in ({"start_time": -1}, {"end_time": 0}, {"start_time": 2, "end_time": 1}):
        with pytest.raises(ValueError):
            CueScene(words, **kwargs)


def test_storyboard_portrait_frames_match_renderer_and_refuse_partial_overwrite(tmp_path):
    scene = Scene(Canvas(60, 90, "white"))
    square = Square(20, fill="red", stroke=None, position=(30, 45))
    scene.play(FadeIn(square), run_time=1).wait(1)
    renderer = PillowRenderer(1)
    samples = [StoryboardSample(1.5, "final"), StoryboardSample(0.5, "reveal"), 1.5]
    output = render_storyboard(scene, samples, tmp_path / "board", size=(60, 90), columns=2, renderer=renderer)
    with PILImage.open(output) as sheet:
        assert sheet.size == (120, 248)
        expected = renderer.frame(scene, 1.5, (60, 90)).convert("RGB")
        assert sheet.crop((0, 0, 60, 90)).tobytes() == expected.tobytes()
    with PILImage.open(output.parent / "02-0000.500s.png") as still:
        assert still.tobytes() == renderer.frame(scene, 0.5, (60, 90)).convert("RGB").tobytes()
    before = {path.name: path.read_bytes() for path in output.parent.iterdir()}
    # The new first sample would have a new path; the third conflicts. Nothing is written.
    with pytest.raises(FileExistsError):
        render_storyboard(scene, [0.1, 0.2, 1.5], output.parent, size=(60, 90))
    assert before == {path.name: path.read_bytes() for path in output.parent.iterdir()}
    render_storyboard(scene, samples, output.parent, size=(60, 90), columns=2, overwrite=True)


def test_preview_validation_and_single_frame_protection(tmp_path):
    scene = Scene(Canvas(60, 90)).wait(1)
    output = save_frame(scene, 0, tmp_path / "frame.png", size=(60, 90))
    with pytest.raises(FileExistsError):
        save_frame(scene, 0, output, size=(60, 90))
    save_frame(scene, 0, output, size=(60, 90), overwrite=True)
    for time in (-1, 1, float("inf"), float("nan")):
        with pytest.raises(ValueError):
            save_frame(scene, time, tmp_path / "invalid.png")
    with pytest.raises(ValueError):
        save_frame(scene, 0, tmp_path / "frame.jpg")
    for kwargs in (
        {"samples": []},
        {"samples": [1]},
        {"samples": [0], "columns": True},
        {"samples": [0], "size": (10, 10)},
        {"samples": [0], "size": (0, 90)},
    ):
        with pytest.raises(ValueError):
            render_storyboard(scene, directory=tmp_path / "invalid", **kwargs)
    assert not (tmp_path / "invalid").exists()
