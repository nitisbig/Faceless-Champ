import pytest
from PIL import Image as PILImage

from faceless_champ import (
    Canvas,
    Draw,
    ExportSettings,
    FadeIn,
    FadeOut,
    Grid,
    Image,
    PillowRenderer,
    Rectangle,
    Scene,
    Sequence,
    Square,
    Text,
    Typewriter,
    linear,
)


def solid(color, duration=1, width=160, height=90):
    scene = Scene(Canvas(width, height, color))
    scene.wait(duration)
    return scene


def test_animation_concurrency_boundaries_and_snapshot():
    scene = Scene(Canvas(160, 90))
    component = Square(10, position=(10, 20))
    scene.play(component.animate.move_to(110, 20), FadeIn(component), run_time=2, rate_func=linear)
    scene.play(FadeOut(component), run_time=1, rate_func=linear)
    assert scene.duration == 3
    entry = scene.entries[0]
    assert entry.state_at(0)["opacity"] == 0
    assert entry.state_at(1)["position"] == (60, 20)
    assert entry.state_at(1)["opacity"] == 0.5
    assert entry.state_at(2)["opacity"] == 1
    assert entry.state_at(3)["opacity"] == 0
    component.move_to(999, 999)
    assert entry.state_at(0)["position"] == (10, 20)
    assert entry.state_at(1) == entry.state_at(1)


def test_conflict_rejected_without_partial_changes():
    scene, component = Scene(), Square()
    with pytest.raises(ValueError, match="Overlapping"):
        scene.play(FadeIn(component), FadeOut(component))
    assert not scene.entries
    assert scene.duration == 0


def test_construct_once_and_out_of_order_frames():
    class Demo(Scene):
        def construct(self):
            self.play(Typewriter(Text("hello", font_size=30, position=(80, 45))), run_time=1)

    scene = Demo(Canvas(160, 90))
    renderer = PillowRenderer()
    renderer.validate(scene)
    first = renderer.frame(scene, 0.2, (160, 90)).tobytes()
    renderer.frame(scene, 0.8, (160, 90))
    assert renderer.frame(scene, 0.2, (160, 90)).tobytes() == first
    assert len(scene.entries) == 1


def test_grid_clips_and_holds_last_state():
    left = solid("red", 0.5, 100, 100)
    left.add(Rectangle(width=500, height=500, fill="lime", stroke=None, position=(50, 50)))
    right = solid("blue", 2, 100, 100)
    grid = Grid(left, right, rows=1, columns=2, canvas=Canvas(200, 100))
    renderer = PillowRenderer(1)
    renderer.validate(grid)
    frame = renderer.frame(grid, 1.5, (200, 100))
    assert frame.getpixel((99, 50))[:3] == (0, 255, 0)
    assert frame.getpixel((100, 50))[:3] == (0, 0, 255)
    assert grid.duration == 2


def test_sequence_timing_crossfade_and_nested_grid():
    left, right = solid("red", 2), solid("blue", 2)
    sequence = Sequence(left, right, crossfade=1)
    assert sequence.starts == [0, 1]
    assert sequence.duration == 3
    frame = PillowRenderer(1).frame(sequence, 1.5, (160, 90))
    assert frame.getpixel((80, 45))[:3] == (127, 0, 127)
    left.wait(1)
    assert sequence.starts == [0, 2]
    nested = Sequence(Grid(left, right, rows=1, columns=2), solid("black"))
    assert nested.duration == 4
    with pytest.raises(ValueError, match="triple"):
        _ = Sequence(solid("red"), solid("green"), solid("blue"), crossfade=0.6).duration


def test_gif_frame_duration_loop_and_transparency(tmp_path):
    path = tmp_path / "two.gif"
    a, b = PILImage.new("RGB", (20, 20), "red"), PILImage.new("RGB", (20, 20), "blue")
    a.save(path, save_all=True, append_images=[b], duration=[100, 300], loop=0)
    scene = solid("black")
    # Add from zero on a fresh scene.
    scene = Scene(Canvas(160, 90))
    scene.add(Image(path, width=20, height=20, position=(80, 45))).wait(1)
    renderer = PillowRenderer(1)
    renderer.validate(scene)
    for time, color in [(0.05, (255, 0, 0)), (0.2, (0, 0, 255)), (0.45, (255, 0, 0))]:
        assert renderer.frame(scene, time, (160, 90)).getpixel((80, 45))[:3] == color
    png = tmp_path / "alpha.png"
    PILImage.new("RGBA", (20, 20), (255, 0, 0, 128)).save(png)
    scene = Scene(Canvas(160, 90, "blue"))
    scene.add(Image(png, width=20, height=20, position=(80, 45))).wait(1)
    renderer.validate(scene)
    assert renderer.frame(scene, 0, (160, 90)).getpixel((80, 45))[:3] == (128, 0, 127)


def test_draw_progress_and_image_cover(tmp_path):
    scene = Scene(Canvas(100, 100))
    scene.play(Draw(Square(50, position=(50, 50), stroke="white", stroke_width=2)), rate_func=linear)
    renderer = PillowRenderer(1)
    renderer.validate(scene)
    counts = [
        sum(p > 100 for p in renderer.frame(scene, t, (100, 100)).convert("RGB").tobytes()[::3]) for t in (0, 0.5, 1)
    ]
    assert counts[0] == 0 < counts[1] < counts[2]
    path = tmp_path / "wide.png"
    PILImage.new("RGB", (80, 20), "red").save(path)
    cover = Scene(Canvas(100, 100))
    cover.add(Image(path, width=50, height=50, fit="cover", position=(50, 50))).wait(1)
    assert renderer.frame(cover, 0, (100, 100)).getpixel((30, 30))[:3] == (255, 0, 0)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"fps": 0},
        {"fps": float("nan")},
        {"width": 101, "height": 100},
        {"width": 100},
        {"quality": "bad"},
        {"crf": 60},
        {"preset": "bad"},
    ],
)
def test_invalid_export(kwargs):
    with pytest.raises(ValueError):
        ExportSettings(**kwargs).dimensions(Canvas())


def test_presets_portrait_and_custom():
    assert ExportSettings(quality="ql").dimensions(Canvas()) == (1280, 720)
    assert ExportSettings(quality="qk").dimensions(Canvas()) == (3840, 2160)
    assert ExportSettings(quality="ql").dimensions(Canvas(1080, 1920)) == (720, 1280)
    assert ExportSettings(width=320, height=180).dimensions(Canvas()) == (320, 180)
    with pytest.raises(ValueError, match="aspect"):
        ExportSettings(width=100, height=100).dimensions(Canvas())


def test_asset_and_timing_validation(tmp_path, tone):
    with pytest.raises(ValueError):
        Scene().wait(-1)
    scene = Scene()
    scene.add(Image(tmp_path / "missing.png")).wait(1)
    with pytest.raises(FileNotFoundError):
        PillowRenderer().validate(scene)
    scene = Scene()
    scene.add(Text("hello", font=tmp_path / "missing.ttf")).wait(1)
    with pytest.raises(ValueError, match="font"):
        PillowRenderer().validate(scene)
    with pytest.raises(ValueError, match="trim"):
        Scene().add_audio(tone, trim_start=1.5, trim_end=1)
    with pytest.raises(ValueError, match="fades"):
        Scene().add_audio(tone, fade_in=3)
    scene = Scene().add_audio(tone, start=0.5, trim_start=0.5, trim_end=1.5)
    assert scene.duration == 1.5


@pytest.mark.parametrize("suffix", ["jpg", "jpeg", "webp"])
def test_additional_image_formats(tmp_path, suffix):
    path = tmp_path / f"image.{suffix}"
    PILImage.new("RGB", (40, 20), (220, 50, 30)).save(path)
    scene = Scene(Canvas(160, 90))
    scene.add(Image(path, width=80, height=40, position=(80, 45))).wait(1)
    renderer = PillowRenderer(1)
    renderer.validate(scene)
    pixel = renderer.frame(scene, 0.5, (160, 90)).getpixel((80, 45))
    assert pixel[0] > 200 and pixel[1] < 70 and pixel[2] < 50


def test_custom_animation_validation():
    from faceless_champ import Animation

    component = Square()
    for targets in [{"scale": -1}, {"position": (1,)}, {"opacity": 2}, {"unknown": 1}]:
        scene = Scene()
        with pytest.raises(ValueError):
            scene.play(Animation(component, targets))
        assert scene.duration == 0
        assert not scene.entries
