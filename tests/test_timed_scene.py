import pytest
from PIL import Image as PILImage

from faceless_champ import Arrow, Canvas, Draw, FadeIn, FadeOut, Icon, PillowRenderer, Scene, Square, linear


def test_absolute_blocks_do_not_accumulate_drift_and_allow_independent_objects():
    scene = Scene(Canvas(160, 90))
    later, earlier = Square(10, position=(100, 45)), Square(10, position=(30, 45))
    with scene.at(5):
        scene.play(FadeIn(later), run_time=0.3)
    with scene.at(1):
        scene.play(FadeIn(earlier), run_time=0.2)
    assert scene.time == pytest.approx(5.3)
    assert [e.start for e in scene.entries] == [5, 1]
    scene.wait_until(6)
    assert scene.duration == 6
    with pytest.raises(ValueError, match="backward"):
        scene.wait_until(2)
    for time in (-1, float("nan")):
        with pytest.raises(ValueError), scene.at(time):
            pass
    assert scene.time == 6


def test_lifetime_end_and_temporal_overlap_validation():
    scene = Scene(Canvas(160, 90))
    square = Square(20, fill="red", stroke=None, position=(80, 45))
    with scene.at(1):
        scene.play(FadeIn(square), run_time=1, rate_func=linear)
    count = len(scene.entries[0].tracks)
    for time in (0, 1.5):
        with scene.at(time), pytest.raises(ValueError):
            scene.play(FadeOut(square))
    assert len(scene.entries[0].tracks) == count
    with scene.at(1.5), pytest.raises(ValueError, match="animations end"):
        scene.remove(square)
    with scene.at(2):
        scene.remove(square)
    renderer = PillowRenderer(1)
    assert renderer.frame(scene, 1.9, (160, 90)).getpixel((80, 45))[0] > 200
    assert renderer.frame(scene, 2, (160, 90)).getpixel((80, 45))[:3] == (0, 0, 0)
    with pytest.raises(ValueError, match="re-added"):
        scene.add(square)
    with pytest.raises(ValueError, match="lifetime"):
        scene.play(FadeOut(square))


def test_icon_tint_preserves_alpha_and_original_image(tmp_path):
    path = tmp_path / "icon.png"
    original = PILImage.new("RGBA", (20, 20), (10, 20, 30, 128))
    original.save(path)
    scene = Scene(Canvas(60, 40))
    scene.add(Icon(path, size=20, color="red", position=(15, 20)), Icon(path, size=20, color="lime", position=(45, 20)))
    renderer = PillowRenderer(1)
    renderer.validate(scene)
    frame = renderer.frame(scene, 0, (60, 40))
    assert frame.getpixel((15, 20))[:3] == (128, 0, 0)
    assert frame.getpixel((45, 20))[:3] == (0, 128, 0)
    assert PILImage.open(path).tobytes() == original.tobytes()


def test_arrow_endpoints_draw_and_rotation():
    scene = Scene(Canvas(160, 100))
    arrow = Arrow((20, 50), (140, 50), tip_size=16, stroke_width=2)
    scene.play(Draw(arrow), rate_func=linear)
    renderer = PillowRenderer(1)
    frames = [renderer.frame(scene, t, (160, 100)).convert("RGB") for t in (0, 0.5, 1)]
    assert frames[0].getbbox() is None
    assert frames[1].getbbox()[2] < 85
    assert frames[2].getpixel((130, 46)) == (255, 255, 255)
    assert frames[2].getpixel((130, 54)) == (255, 255, 255)
    vertical = Arrow((80, 20), (80, 80), stroke_width=2)
    assert vertical.position == (80, 50)
    assert vertical.rotation == 90
    for start, end in [((0, 0), (0, 0)), ((0,), (1, 1))]:
        with pytest.raises(ValueError):
            Arrow(start, end)
