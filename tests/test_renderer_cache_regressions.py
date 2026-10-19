"""Rendering regressions across lifetime, text and retained-sprite changes."""

import pytest

from faceless_champ import (
    Canvas,
    Captions,
    GradientStop,
    Group,
    LinearGradient,
    PillowRenderer,
    Rectangle,
    Scene,
    SkiaRenderer,
    SubtitleCue,
    SubtitleTrack,
    Text,
    linear,
)


@pytest.fixture
def native():
    pytest.importorskip("skia")
    with SkiaRenderer(1) as renderer:
        yield renderer


@pytest.mark.parametrize("grouped", [False, True])
def test_native_frame_cache_tracks_static_component_lifetimes(native, grouped):
    shape = Rectangle(width=30, height=20, fill="red", stroke=None, position=(40, 30))
    component = Group(shape) if grouped else shape
    scene = Scene(Canvas(80, 60, "#00000000")).wait(1).add(component).wait(1).remove(component).wait(1)
    for time in (0, 0.5, 1, 1.5, 2, 2.5, 1.5, 0.5, 2, 1):
        before = native.stats["frame_cache_hits"]
        frame = native.frame(scene, time, (80, 60))
        assert frame.getpixel((40, 30)) == ((255, 0, 0, 255) if 1 <= time < 2 else (0, 0, 0, 0))
        assert native.frame(scene, time, (80, 60)).tobytes() == frame.tobytes()
        assert native.stats["frame_cache_hits"] > before


@pytest.mark.parametrize("anchor", ["center", "top_left"])
def test_native_captions_measure_current_phrase_at_component_age(native, anchor):
    track = SubtitleTrack([SubtitleCue(1, 1, 2, "Short."), SubtitleCue(2, 3, 4, "A longer phrase that wraps.")])
    captions = Captions(track, width=180, font_size=24, position=(160, 100), anchor=anchor)
    scene = Scene(Canvas(480, 300, "#00000000")).wait(2).add(captions).wait(5)
    with PillowRenderer(1) as pillow:
        boxes = {}
        for time in (2.5, 3.5, 4.5, 5.5, 3.5, 6):
            frame = native.frame(scene, time, (480, 300))
            actual = frame.getchannel("A").getbbox()
            expected = pillow.frame(scene, time, (480, 300)).getchannel("A").getbbox()
            if expected is None:
                assert actual is None
            else:
                assert actual is not None
                assert actual == pytest.approx(expected, abs=2)
                boxes[time] = actual
        assert boxes[5.5][3] - boxes[5.5][1] > boxes[3.5][3] - boxes[3.5][1]


def test_native_text_rounds_interpolated_rgba_channels(native):
    import numpy as np

    text = Text("Animated", font_size=36, color="#FF000080", text_engine="skia", position=(120, 50))
    scene = Scene(Canvas(240, 100, "#00000000")).add(text)
    scene.play(text.animate.color_to("#0000FFFF"), run_time=1, rate_func=linear)
    for time, expected in (
        (0, (255, 0, 0, 128)),
        (0.5, (128, 0, 128, 192)),
        (1, (0, 0, 255, 255)),
        (0.5, (128, 0, 128, 192)),
    ):
        frame = native.frame(scene, time, (240, 100))
        pixels = np.asarray(frame).reshape(-1, 4)
        pixel = tuple(pixels[pixels[:, 3].argmax()])
        assert pixel == pytest.approx(expected, abs=1)


def test_pillow_gradient_rectangle_cache_tracks_corner_radius():
    gradient = LinearGradient((GradientStop(0, "red"), GradientStop(1, "blue")))
    shape = Rectangle(width=80, height=80, fill=gradient, stroke=None, position=(60, 60))
    scene = Scene(Canvas(120, 120, "#00000000")).add(shape)
    scene.play(shape.animate.corner_radius_to(30), run_time=1, rate_func=linear)
    with PillowRenderer(1) as cached:
        square = cached.frame(scene, 0, (120, 120))
        rounded = cached.frame(scene, 1, (120, 120))
        assert square.getpixel((22, 22))[3] == 255
        assert rounded.getpixel((22, 22))[3] == 0
        assert square.tobytes() != rounded.tobytes()
        for time in (0.5, 1, 0, 0.5):
            with PillowRenderer(1) as fresh:
                assert cached.frame(scene, time, (120, 120)).tobytes() == fresh.frame(scene, time, (120, 120)).tobytes()
