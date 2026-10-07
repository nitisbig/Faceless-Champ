"""Behavioral checks for drawing visibility, geometry, timing, and the public starter."""

import json
import wave
from dataclasses import FrozenInstanceError, replace

import pytest
from faceless_champ import Bounds, Canvas, Captions, Circle, PillowRenderer, Text
from PIL import Image, ImageChops

from facelesschamp_kit import BuildContext, KitError, Project
from facelesschamp_kit.assets import AssetRegistry
from facelesschamp_kit.blocks import (
    Heading,
    WhiteboardArrow,
    WhiteboardCircle,
    WhiteboardDrawing,
    WhiteboardLine,
    WhiteboardPath,
    WhiteboardRectangle,
)
from facelesschamp_kit.cli import main
from facelesschamp_kit.scaffold import init_project
from facelesschamp_kit.templates import WhiteboardScene, narrated, silent, whiteboard_basic
from facelesschamp_kit.themes import WHITEBOARD


@pytest.fixture
def ctx(tmp_path):
    return BuildContext(tmp_path, canvas=Canvas(1920, 1080))


def drawing():
    return WhiteboardDrawing((WhiteboardCircle((250, 500), 100), WhiteboardCircle((750, 500), 100)))


def recipe(name="board", **kwargs):
    return WhiteboardScene(name, drawing(), **kwargs)


def frame(scene, time):
    return PillowRenderer(1).frame(scene, time, (384, 216)).convert("RGB")


def test_strokes_start_hidden_draw_linearly_and_hold(ctx):
    scene = whiteboard_basic(ctx, scenes=[recipe(duration=4)], draw_fraction=0.5).compile().composition
    strokes = [e for e in scene.entries if isinstance(e.component, Circle)]
    first, second = strokes
    assert second.initial["opacity"] == 0
    assert second.state_at(0.99)["opacity"] == 0
    assert first.state_at(0.5)["draw"] == pytest.approx(0.5)
    assert second.state_at(1)["opacity"] == 1
    assert second.state_at(1)["draw"] == 0
    assert second.state_at(1.5)["draw"] == pytest.approx(0.5)
    assert second.state_at(2)["draw"] == 1
    blank = Image.new("RGB", (384, 216), "white")
    assert ImageChops.difference(frame(scene, 0), blank).getbbox() is None
    # A future stroke never appears in the right-hand half of the frame.
    assert ImageChops.difference(frame(scene, 0.5), blank).crop((192, 0, 384, 216)).getbbox() is None
    assert ImageChops.difference(frame(scene, 0.5), frame(scene, 0.8)).getbbox() is not None
    assert frame(scene, 2).tobytes() == frame(scene, 3.8).tobytes()


def test_scene_clears_and_result_remains_editable(ctx):
    video = whiteboard_basic(ctx, scenes=[recipe("first", duration=2), recipe("second", duration=2)])
    video.segment("overlay", start=3, duration=1).add(Heading("Editable"))
    result = video.compile()
    blank = Image.new("RGB", (384, 216), "white")
    assert ImageChops.difference(frame(result.composition, 2), blank).getbbox() is None
    assert ImageChops.difference(frame(result.composition, 1.8), blank).getbbox() is not None
    assert result.duration == 4
    assert result.report["segments"][-1]["id"] == "overlay"


@pytest.mark.parametrize("size", [(1920, 1080), (1080, 1920)])
def test_uniform_fit_including_edge_strokes_and_arrowheads(tmp_path, size):
    ctx = BuildContext(tmp_path, canvas=Canvas(*size))
    items = WhiteboardDrawing(
        (
            WhiteboardRectangle(0, 0, 1000, 1000, stroke_width=50),
            WhiteboardArrow((0, 0), (1000, 1000), tip_size=80, stroke_width=40),
            WhiteboardCircle((500, 500), 200),
            WhiteboardLine((0, 1000), (1000, 0)),
            WhiteboardPath(((100, 100), (100, 200), (200, 200)), closed=True),
        )
    )
    built = items.compose(ctx, ctx.bounds)
    measured = built.root.bounds
    assert measured.left >= ctx.bounds.left - 1e-6
    assert measured.top >= ctx.bounds.top - 1e-6
    assert measured.right <= ctx.bounds.right + 1e-6
    assert measured.bottom <= ctx.bounds.bottom + 1e-6
    assert built.root.scale_x == built.root.scale_y == 1
    circle = built.children["stroke-2"]
    assert circle.bounds.width == circle.bounds.height
    # A circle-only render remains circular after fitting either canvas.
    video = whiteboard_basic(
        ctx,
        scenes=[
            WhiteboardScene(
                "circle",
                WhiteboardDrawing((WhiteboardCircle((500, 500), 200),)),
                duration=2,
            )
        ],
    )
    output_size = (384, 216) if size[0] > size[1] else (216, 384)
    rendered = PillowRenderer(1).frame(video.compile().composition, 1.8, output_size).convert("RGB")
    box = ImageChops.difference(rendered, Image.new("RGB", output_size, "white")).getbbox()
    assert abs((box[2] - box[0]) - (box[3] - box[1])) <= 1


def test_viewbox_whitespace_is_preserved(ctx):
    built = WhiteboardDrawing((WhiteboardCircle((100, 500), 50),)).compose(ctx, Bounds(0, 0, 1000, 1000))
    assert built.root.bounds.center == (100, 500)


@pytest.mark.parametrize("size", [(1920, 1080), (1080, 1920)])
def test_label_and_caption_reservation(ctx, size):
    ctx.canvas = Canvas(*size)
    ctx.captions = True
    video = whiteboard_basic(ctx, scenes=[recipe(duration=2, label="An idea")])
    result = video.compile()
    label, drawing_placement = result.report["segments"][0]["placements"]
    assert label["bounds"]["bottom"] <= ctx.bounds.top + ctx.bounds.height * 0.15 + 1
    assert drawing_placement["bounds"]["top"] >= ctx.bounds.top + ctx.bounds.height * 0.15 - 1
    assert drawing_placement["bounds"]["bottom"] <= ctx.bounds.bottom + 1
    text = next(e for e in result.composition.entries if isinstance(e.component, Text))
    assert text.state_at(0)["opacity"] == 0
    assert text.state_at(1)["opacity"] == 1


def test_no_label_uses_all_safe_area(ctx):
    video = whiteboard_basic(ctx, scenes=[recipe(duration=1)])
    assert len(video.segments[0].placements) == 1
    assert video.segments[0].placements[0].bounds == ctx.bounds


def test_label_overflow_has_scene_scope(ctx):
    with pytest.raises(KitError) as error:
        whiteboard_basic(ctx, scenes=[recipe(duration=1, label="enormousword" * 100)]).compile()
    assert error.value.code == "TEXT_FIT"
    assert error.value.scope["segment"] == "board"


def test_fresh_builds_and_immutable_inputs(ctx):
    points = [[100, 100], [200, 200]]
    path = WhiteboardPath(points)
    drawings = [path]
    block = WhiteboardDrawing(drawings, viewbox=[1000, 1000])
    points[0][0] = 999
    drawings.clear()
    assert block.drawings[0].points[0] == (100, 100)
    with pytest.raises(FrozenInstanceError):
        block.viewbox = (1, 1)
    item = WhiteboardScene("board", block, duration=2)
    with pytest.raises(FrozenInstanceError):
        item.duration = 3
    video = whiteboard_basic(ctx, scenes=[item])
    first, second = video.compile(), video.compile()
    assert not {id(e.component) for e in first.composition.entries} & {
        id(e.component) for e in second.composition.entries
    }
    assert frame(first.composition, 1).tobytes() == frame(second.composition, 1).tobytes()


def test_theme_override_and_existing_templates(ctx):
    custom = replace(WHITEBOARD, background="#FAFAFA", foreground="#123456")
    compiled = whiteboard_basic(ctx, scenes=[recipe(duration=1)], theme=custom).compile()
    assert compiled.context.theme == custom
    assert compiled.composition.canvas.bg == custom.background
    assert (
        next(e.component for e in compiled.composition.entries if isinstance(e.component, Circle)).stroke == "#123456"
    )
    assert callable(silent) and callable(narrated)


def narration_context(tmp_path):
    with wave.open(str(tmp_path / "voice.wav"), "wb") as stream:
        stream.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
        stream.writeframes(b"\0\0" * 32000)
    (tmp_path / "cues.srt").write_text(
        "7\n00:00:00,250 --> 00:00:00,750\nFirst\n\n"
        "19\n00:00:01,250 --> 00:00:02,000\nSecond\n\n"
        "55\n00:00:02,500 --> 00:00:03,500\nTail\n"
    )
    return BuildContext(
        tmp_path,
        assets=AssetRegistry(
            tmp_path,
            {
                "voice": {"type": "audio", "path": "voice.wav"},
                "cues": {"type": "subtitle", "path": "cues.srt"},
            },
        ),
    )


def test_original_cue_indices_audio_tail_and_captions(tmp_path):
    ctx = narration_context(tmp_path)
    video = whiteboard_basic(
        ctx,
        scenes=[recipe("first", cues=("first", "second")), recipe("last", start=1.25, duration=1)],
        audio="voice",
        subtitles="cues",
        markers={"first": 7, "second": 19},
        captions=True,
    )
    result = video.compile()
    first, last = result.report["segments"]
    assert (first["start"], first["end"], first["cues"]) == (0.25, 1.25, [7, 19])
    assert (last["authored_end"], last["end"]) == (2.25, 4)
    assert result.report["diagnostics"][0]["code"] == "AUDIO_TAIL_HOLD"
    assert result.report["narration"]["cues"][-1]["index"] == 55
    captions = next(e for e in result.composition.entries if isinstance(e.component, Captions))
    assert captions.start == 0
    assert captions.component.bounds.height <= ctx.caption_space
    assert [cue.start for cue in captions.component.track.cues] == [0.25, 1.25, 2.5]
    assert result.composition.audio[0].start == 0
    last_stroke = [e for e in result.composition.entries if isinstance(e.component, Circle)][-1]
    assert last_stroke.state_at(3.9)["draw"] == 1


def test_last_cue_window_reaches_audio_end(tmp_path):
    video = whiteboard_basic(
        narration_context(tmp_path),
        scenes=[recipe(cues=("first", None))],
        audio="voice",
        subtitles="cues",
        markers={"first": 7},
    )
    assert video.segments[0].start == 0.25
    assert video.segments[0].end == 4


@pytest.mark.parametrize("fraction", [0, -1, 1, 2, True, float("nan"), float("inf")])
def test_invalid_draw_fraction(ctx, fraction):
    with pytest.raises(KitError):
        whiteboard_basic(ctx, scenes=[recipe(duration=1)], draw_fraction=fraction)


@pytest.mark.parametrize(
    "factory",
    [
        lambda: WhiteboardPath([]),
        lambda: WhiteboardPath([(1, 2), (1, 2)]),
        lambda: WhiteboardPath([(1, 2), (3, 4)], closed=True),
        lambda: WhiteboardPath(None),
        lambda: WhiteboardLine((1, 2), (1, 2)),
        lambda: WhiteboardArrow((0, 0), (10, 0)),
        lambda: WhiteboardRectangle(0, 0, 0, 5),
        lambda: WhiteboardCircle((5, 5), -1),
        lambda: WhiteboardCircle((5, 5), True),
        lambda: WhiteboardCircle((5, 5), 1, color="invalid-color"),
        lambda: WhiteboardCircle((5, 5), 1, stroke_width=0),
        lambda: WhiteboardCircle((float("nan"), 5), 1),
        lambda: WhiteboardDrawing([]),
        lambda: WhiteboardDrawing(["circle"]),
        lambda: WhiteboardDrawing([WhiteboardCircle((0, 0), 2)]),
        lambda: WhiteboardDrawing([WhiteboardCircle((5, 5), 2)], viewbox=(0, 100)),
    ],
)
def test_invalid_geometry(factory):
    with pytest.raises(KitError):
        factory()


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"duration": 0},
        {"duration": float("inf")},
        {"duration": 1, "start": -1},
        {"duration": 1, "cues": ("a", None)},
        {"cues": ("a",)},
        {"cues": ("a", "")},
        {"duration": 1, "label": ""},
    ],
)
def test_invalid_recipe_timing_is_scoped(kwargs):
    with pytest.raises(KitError) as error:
        recipe(**kwargs)
    assert error.value.scope["segment"] == "board"


@pytest.mark.parametrize("scenes", [[], None, ["invalid"]])
def test_missing_scenes(ctx, scenes):
    with pytest.raises(KitError):
        whiteboard_basic(ctx, scenes=scenes)


def test_overlapping_duplicate_and_out_of_order_scenes(ctx):
    for items in (
        [recipe("a", duration=2), recipe("b", start=1, duration=2)],
        [recipe("a", duration=2), recipe("a", duration=2)],
        [recipe("a", start=5, duration=1), recipe("b", start=0, duration=1)],
    ):
        with pytest.raises(KitError):
            whiteboard_basic(ctx, scenes=items)


def test_missing_narration_and_unknown_marker(tmp_path):
    ctx = narration_context(tmp_path)
    with pytest.raises(KitError, match="NARRATION"):
        whiteboard_basic(ctx, scenes=[recipe(cues=("first", None))])
    with pytest.raises(KitError, match="NARRATION"):
        whiteboard_basic(ctx, scenes=[recipe(duration=1)], audio="voice")
    with pytest.raises(KitError) as error:
        whiteboard_basic(
            ctx,
            scenes=[recipe(cues=("missing", None))],
            audio="voice",
            subtitles="cues",
            markers={"first": 7},
        )
    assert error.value.code == "CUE_MARKER"
    assert error.value.scope["segment"] == "board"


def test_cli_starter_and_registered_theme(tmp_path, capsys):
    root = tmp_path / "demo"
    assert main(["init", str(root), "--template", "whiteboard-basic"]) == 0
    capsys.readouterr()
    assert main(["list", "templates"]) == 0
    assert "whiteboard-basic" in json.loads(capsys.readouterr().out)
    assert main(["list", "themes"]) == 0
    assert "whiteboard" in json.loads(capsys.readouterr().out)
    assert main(["--project", str(root), "validate", "main"]) == 0
    capsys.readouterr()
    project = Project(root)
    result = project.build()
    assert result.duration == 10
    assert (result.composition.canvas.width, result.composition.canvas.height) == (1920, 1080)
    assert result.report["theme"]["name"] == "whiteboard"
    assert result.report["assets"] == []
    assert len(result.report["segments"]) == 2
    assert "WhiteboardScene" in (root / "videos/main.py").read_text()
    project.config["videos"]["main"]["format"] = "shorts"
    assert project.build().composition.canvas.width == 1080
    with pytest.raises(KitError, match="DESTINATION"):
        init_project(root, "whiteboard-basic")
