"""Rendering, timing, and audio contracts exercised by equation-render."""

import sys

import pytest

from faceless_champ import (
    Canvas,
    Draw,
    Equation,
    Grid,
    Layer,
    PillowRenderer,
    Polyline,
    Rectangle,
    Scene,
    Sequence,
    Write,
    linear,
)
from faceless_champ.export import _audio_events


def test_delayed_grid_padding_and_held_final_state():
    child = Scene(Canvas(40, 40, "red")).wait(1)
    grid = Grid(child, rows=1, columns=1, canvas=Canvas(100, 100, "blue"), padding=10, start_times=[2])
    renderer = PillowRenderer(1)
    assert grid.duration == 3
    assert renderer.frame(grid, 1.99, (100, 100)).getpixel((50, 50))[:3] == (0, 0, 255)
    frame = renderer.frame(grid, 2, (100, 100))
    assert frame.getpixel((9, 50))[:3] == (0, 0, 255)
    assert frame.getpixel((10, 50))[:3] == (255, 0, 0)
    assert frame.getpixel((90, 50))[:3] == (0, 0, 255)
    assert renderer.frame(grid, 4, (100, 100)).getpixel((50, 50))[:3] == (255, 0, 0)


@pytest.mark.parametrize("options", [{"padding": 50}, {"padding": (1, 2)}, {"start_times": [-1]}, {"start_times": []}])
def test_grid_rejects_invalid_offsets_and_padding(options):
    with pytest.raises(ValueError):
        Grid(Scene(), rows=1, columns=1, canvas=Canvas(100, 100), **options)


def test_layer_composites_alpha_and_holds_shorter_children():
    base = Scene(Canvas(100, 100, "blue")).wait(3)
    overlay = Scene(Canvas(100, 100, "#00000000"))
    overlay.add(Rectangle(width=20, height=20, fill="#ff000080", stroke=None, position=(50, 50))).wait(1)
    layer = Layer(base, overlay)
    renderer = PillowRenderer(1)
    renderer.validate(layer)
    assert layer.duration == 3
    assert renderer.frame(layer, 2, (100, 100)).getpixel((50, 50)) == (128, 0, 127, 255)
    assert renderer.frame(layer, 2, (100, 100)).getpixel((10, 10)) == (0, 0, 255, 255)


def test_nested_layer_grid_audio_offsets_and_crossfade_envelopes(tone):
    clip = Scene(Canvas(100, 100)).add_audio(tone, start=0.25, trim_end=0.5).wait(1)
    grid = Grid(clip, rows=1, columns=1, start_times=[1.5])
    layer = Layer(Scene().wait(3), grid)
    sequence = Sequence(Scene().wait(2), layer, crossfade=0.5)
    events = _audio_events(sequence)
    assert len(events) == 1
    assert events[0][1] == pytest.approx(3.25)
    assert events[0][2] == (("in", 1.5, 0.5),)


def test_polyline_draw_follows_segment_lengths_and_frames_are_deterministic():
    scene = Scene(Canvas(100, 100, "#00000000"))
    path = Polyline([(10, 10), (90, 10), (90, 90)], stroke="white", stroke_width=2)
    scene.play(Draw(path), run_time=1, rate_func=linear)
    renderer = PillowRenderer(1)
    assert renderer.frame(scene, 0, (100, 100)).getbbox() is None
    middle = renderer.frame(scene, 0.5, (100, 100))
    assert middle.getpixel((50, 10))[3] > 0
    assert middle.getpixel((90, 50))[3] == 0
    assert renderer.frame(scene, 1, (100, 100)).getpixel((90, 50))[3] > 0
    assert renderer.frame(scene, 0.5, (100, 100)).tobytes() == middle.tobytes()


def test_rounded_rectangle_and_closed_polyline_fill():
    scene = Scene(Canvas(100, 100, "#00000000"))
    scene.add(Rectangle(width=80, height=80, corner_radius=20, fill="red", stroke=None, position=(50, 50)))
    frame = PillowRenderer(1).frame(scene, 0, (100, 100))
    assert frame.getpixel((11, 11))[3] == 0
    assert frame.getpixel((50, 50))[:3] == (255, 0, 0)
    scene = Scene(Canvas(100, 100, "#00000000"))
    scene.add(Polyline([(10, 10), (90, 10), (50, 90)], closed=True, fill="lime", stroke=None))
    assert PillowRenderer(1).frame(scene, 0, (100, 100)).getpixel((50, 30))[:3] == (0, 255, 0)


def test_equation_write_keeps_layout_and_fits_width(tmp_path, monkeypatch):
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    pytest.importorskip("matplotlib")
    scene = Scene(Canvas(360, 160, "#00000000"))
    math = Equation(r"x=\frac{-b\pm\sqrt{b^2-4ac}}{2a}", font_size=72, max_width=160, position=(180, 80))
    scene.play(Write(math), run_time=1)
    renderer = PillowRenderer(1)
    renderer.validate(scene)
    assert renderer.frame(scene, 0, (360, 160)).getbbox() is None
    complete = renderer.frame(scene, 1, (360, 160))
    partial = renderer.frame(scene, 0.5, (360, 160))
    left, top, right, bottom = complete.getbbox()
    assert right - left <= 160
    assert partial.crop((left, top, 180, bottom)).tobytes() == complete.crop((left, top, 180, bottom)).tobytes()
    assert partial.getbbox()[2] <= 180
    assert renderer.frame(scene, 0.5, (360, 160)).tobytes() == partial.tobytes()


def test_equation_dependency_error_is_actionable(monkeypatch):
    monkeypatch.setitem(sys.modules, "matplotlib", None)
    scene = Scene().add(Equation("x^2"))
    with pytest.raises(RuntimeError, match="uv sync --extra equations"):
        PillowRenderer().validate(scene)


def test_equation_syntax_error_fails_before_export(tmp_path, monkeypatch):
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    pytest.importorskip("matplotlib")
    with pytest.raises(ValueError, match="Invalid Equation"):
        PillowRenderer().validate(Scene().add(Equation(r"\notarealcommand{x}")))
