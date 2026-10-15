"""Saved workspace design contracts, independent of media rendering."""

import subprocess
from dataclasses import FrozenInstanceError
from itertools import pairwise

import pytest

from faceless_champ import Bounds, Canvas, CodingChamp, Rectangle, Scene
from faceless_champ.coding_workspace import CodeWindow, CodeWorkspaceDesign


def test_named_design_preserves_approved_geometry_and_timing():
    design = CodeWorkspaceDesign.named("clean-flow")
    assert design.bounds == design.editor_full == Bounds(0, 0, 1920, 1080)
    assert design.background == "#E8E6E2"
    assert design.theme.background == "#14161A"
    assert design.unit == 1
    assert design.editor_split.left == 48
    assert design.editor_split.top == pytest.approx(194.4)
    assert design.editor_split.width == 1228.8
    assert design.editor_split.height == pytest.approx(691.2)
    assert design.terminal_bounds.left == 1308.8
    assert design.terminal_bounds.right == 1872
    assert design.terminal_bounds.top == design.editor_split.top
    assert design.code_bounds == Bounds(48, 144, 1872, 1024)
    assert (design.code_size, design.terminal_size) == (54, 32)
    assert (design.shrink_duration, design.restore_duration) == (0.8, 0.9)
    assert (design.terminal_entrance_duration, design.terminal_exit_duration) == (0.6, 0.45)
    with pytest.raises(FrozenInstanceError):
        design.editor_scale = 0.5


def test_scaled_translated_design_keeps_face_center_as_fixed_pivot():
    design = CodeWorkspaceDesign(bounds=Bounds(100, 50, 1060, 590))
    assert design.unit == 0.5
    assert design.code_bounds == Bounds(124, 122, 1036, 562)
    assert design.editor_split.center == pytest.approx((431.2, 320))
    editor = design.window(design.editor_full, "functions.py", fullscreen=True)
    terminal = design.window(design.terminal_bounds, "Terminal")
    assert editor.position == editor._origin == design.bounds.center
    assert terminal.position == terminal._origin == design.terminal_bounds.center
    assert editor.header.height == 40
    assert terminal.header.height == 32
    assert terminal.face.corner_radius == 11
    assert editor.heading.font_size == 15
    assert terminal.heading.font_size == 13


@pytest.mark.parametrize("bounds", [Bounds(0, 0, 1920, 1080), Bounds(100, 50, 1060, 590), Bounds(0, 0, 3840, 2160)])
def test_workspace_rejects_terminal_allocations_too_narrow_for_chrome(bounds):
    with pytest.raises(ValueError, match="terminal width.*chrome"):
        CodeWorkspaceDesign(bounds=bounds, editor_scale=0.9)


@pytest.mark.parametrize("fullscreen", [False, True])
@pytest.mark.parametrize("unit", [0.5, 1, 2])
def test_direct_windows_reject_narrow_chrome_allocations(fullscreen, unit):
    with pytest.raises(ValueError, match="width.*chrome"):
        CodeWindow(Bounds(20, 10, 20 + 64 * unit, 10 + 200 * unit), title="Terminal", fullscreen=fullscreen, unit=unit)


@pytest.mark.parametrize("title", ["Terminal", "a_very_long_filename_" * 12 + ".py", "Terminal\n" * 12])
@pytest.mark.parametrize("fullscreen", [False, True])
@pytest.mark.parametrize("unit", [0.5, 1, 2])
def test_generated_chrome_fits_minimum_window_face_and_header(title, fullscreen, unit):
    face = Bounds(100, 50, 100 + 192 * unit, 50 + 200 * unit)
    window = CodeWindow(face, title=title, fullscreen=fullscreen, unit=unit)
    assert window.heading.text == title
    assert 0 < window.heading.scale <= 1
    for component in (*window.children[5:8], window.heading):
        box = component.bounds
        assert face.left <= box.left < box.right <= face.right + 1e-9
        assert face.top <= box.top < box.bottom <= face.top + window.header.height + 1e-9
    assert window.heading.bounds.right <= face.right - 24 * unit + 1e-9
    assert window.position == window._origin == face.center


def test_default_titles_preserve_saved_typography_and_positions():
    design = CodeWorkspaceDesign()
    for box, title, fullscreen, size, top in (
        (design.editor_full, "functions.py", True, 30, 22),
        (design.terminal_bounds, "Terminal", False, 26, 16),
    ):
        window = design.window(box, title, fullscreen=fullscreen)
        assert window.heading.font_size == size
        assert window.heading.scale == 1
        assert window.heading.position == (box.left + 144, box.top + top)


def test_complete_editor_scales_uniformly_and_returns_with_seekable_children():
    design = CodeWorkspaceDesign(bounds=Bounds(0, 0, 960, 540))
    box = design.code_bounds
    content = CodingChamp(
        "def greet():\n    print('Hello')\n\ngreet()",
        width=box.width,
        height=box.height,
        font_size=design.code_size * design.unit,
        chrome=False,
        position=(box.left, box.top),
        anchor="top_left",
    )
    editor = design.window(design.editor_full, "functions.py", fullscreen=True, children=(content,))
    scene = Scene(Canvas(960, 540, design.background))
    scene.add(editor)
    with scene.at(1):
        scene.play(
            design.editor_motion(editor, running=True), *design.editor_corners(editor, running=True), run_time=0.8
        )
    with scene.at(3):
        scene.play(
            design.editor_motion(editor, running=False), *design.editor_corners(editor, running=False), run_time=0.9
        )
    scene.wait_until(4)
    scene.build()
    initial = scene.bounds_at(content, 0)
    split = scene.bounds_at(content, 2)
    assert split.width / initial.width == pytest.approx(0.64)
    assert split.height / initial.height == pytest.approx(0.64)
    assert scene._objects[editor].state_at(2)["position"] == pytest.approx(design.editor_split.center)
    assert scene._objects[editor].state_at(2)["scale_x"] == 1
    assert scene._objects[editor].state_at(2)["scale_y"] == 1
    assert scene._objects[editor.face].state_at(2)["corner_radius"] == 16
    halfway = scene.bounds_at(content, 1.4)
    assert split.width < halfway.width < initial.width
    for time in (4, 0, 2, 1.4, 4):
        measured = scene.bounds_at(content, time)
        if time in (0, 4):
            assert measured == initial
        elif time == 2:
            assert measured == split
        else:
            assert measured == halfway
    assert scene._objects[editor.face].state_at(4)["corner_radius"] == 0


def test_terminal_pop_and_exit_keep_authored_position_and_visibility():
    design = CodeWorkspaceDesign(bounds=Bounds(20, 10, 980, 550))
    terminal = design.window(design.terminal_bounds, "Terminal")
    scene = Scene(Canvas(1000, 560))
    with scene.at(1):
        scene.play(design.terminal_in(terminal), run_time=design.terminal_entrance_duration)
    with scene.at(3):
        scene.play(design.terminal_out(terminal), run_time=design.terminal_exit_duration)
    with scene.at(3.45):
        scene.remove(terminal)
    scene.build()
    entry = scene._objects[terminal]
    assert entry.start == 1
    assert entry.end == 3.45
    assert entry.state_at(1)["opacity"] == 0
    assert entry.state_at(1)["scale"] == 0.94
    assert entry.state_at(1)["position"][1] == design.terminal_bounds.center[1] + 14
    assert 0 < entry.state_at(1.3)["opacity"] < 1
    assert entry.state_at(2)["position"] == design.terminal_bounds.center
    assert entry.state_at(2)["scale"] == entry.state_at(2)["opacity"] == 1
    assert entry.state_at(3.45)["opacity"] == 0
    assert entry.state_at(3.45)["scale"] == 0.96
    assert entry.state_at(3.45)["position"][1] == design.terminal_bounds.center[1] + 9


def test_fluid_motion_is_monotonic_with_settled_endpoints():
    values = [CodeWorkspaceDesign.fluid(index / 100) for index in range(101)]
    assert values[0] == 0
    assert values[-1] == 1
    assert all(first <= second for first, second in pairwise(values))
    epsilon = 1e-6
    assert CodeWorkspaceDesign.fluid(epsilon) / epsilon < 1e-4
    assert (1 - CodeWorkspaceDesign.fluid(1 - epsilon)) / epsilon < 1e-4


@pytest.mark.parametrize(
    "options,message",
    [
        ({"bounds": (0, 0, 1920, 1080)}, "Bounds"),
        ({"bounds": Bounds(0, 0, 0, 1080)}, "one design pixel"),
        ({"editor_scale": 0}, "editor_scale"),
        ({"editor_scale": 1}, "less than 1"),
        ({"editor_scale": 0.98}, "terminal width"),
        ({"editor_scale": 0.01}, "content space"),
        ({"terminal_size": float("nan")}, "finite"),
        ({"code_size": -1}, "code_size"),
        ({"shrink_duration": 0}, "shrink_duration"),
        ({"restore_duration": -1}, "restore_duration"),
        ({"terminal_entrance_duration": float("inf")}, "finite"),
        ({"terminal_exit_duration": 0}, "terminal_exit_duration"),
        ({"theme": None}, "theme"),
        ({"background": "not-a-color"}, "color"),
    ],
)
def test_invalid_design_configuration_fails_before_build(options, message):
    with pytest.raises((ValueError, TypeError), match=message):
        CodeWorkspaceDesign(**options)


def test_unknown_design_and_invalid_window_inputs_are_actionable():
    with pytest.raises(ValueError, match="use clean-flow"):
        CodeWorkspaceDesign.named("unknown")
    with pytest.raises(TypeError, match="Bounds"):
        CodeWindow((0, 0, 100, 100))
    with pytest.raises(ValueError, match="unit"):
        CodeWindow(Bounds(0, 0, 100, 100), unit=0)
    with pytest.raises(ValueError, match="below its header"):
        CodeWindow(Bounds(0, 0, 100, 20))
    with pytest.raises(TypeError, match="Components"):
        CodeWindow(Bounds(0, 0, 200, 200), children=("source",))
    outside = Rectangle(width=100, height=100, position=(500, 500))
    with pytest.raises(ValueError, match="fit inside"):
        CodeWindow(Bounds(0, 0, 200, 200), children=(outside,))
    with pytest.raises(TypeError, match="CodeWindow"):
        CodeWorkspaceDesign().editor_motion(outside, running=True)


def test_building_and_seeking_workspace_never_executes_its_source(monkeypatch):
    design = CodeWorkspaceDesign(bounds=Bounds(0, 0, 960, 540))
    source = "raise RuntimeError('must never execute')"
    box = design.code_bounds
    content = CodingChamp(
        source,
        width=box.width,
        height=box.height,
        font_size=18,
        chrome=False,
        position=(box.left, box.top),
        anchor="top_left",
    )
    editor = design.window(design.editor_full, "example.py", fullscreen=True, children=(content,))

    def no_process(*args, **kwargs):
        pytest.fail("Workspace construction or seeking attempted to start a process")

    monkeypatch.setattr(subprocess, "Popen", no_process)
    scene = Scene(Canvas(960, 540))
    scene.play(design.editor_motion(editor, running=True), run_time=design.shrink_duration)
    scene.build()
    assert scene.bounds_at(content, design.shrink_duration).width == pytest.approx(content.bounds.width * 0.64)
    assert content.code == source
