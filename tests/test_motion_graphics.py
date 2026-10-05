import pytest

from faceless_champ import (
    Animation,
    Canvas,
    Checkmark,
    CircleMask,
    Countdown,
    Gauge,
    Group,
    LoadingDots,
    PillowRenderer,
    ProgressBar,
    ProgressRing,
    Rectangle,
    RectangleMask,
    Repeat,
    Scene,
    ShapeMask,
    Stagger,
    Succession,
    Text,
    Wipe,
    linear,
)
from faceless_champ.motion import matrix, multiply, point


def render(scene, t):
    return PillowRenderer(1).frame(scene, t, (200, 160))


def test_visual_interpolation_and_cache_invalidation():
    c = Rectangle(width=40, height=20, fill="#ff000080", stroke=None, position=(100, 80))
    s = Scene(Canvas(200, 160, "#00000000")).add(c)
    s.play(
        c.animate.fill_to("#0000ff00")
        .stroke_to("white")
        .width_to(100)
        .height_to(60)
        .stroke_width_to(8)
        .corner_radius_to(25),
        run_time=2,
        rate_func=linear,
    )
    middle = s.entries[0].state_at(1)
    assert middle["fill"] == (127.5, 0, 127.5, 64)
    assert middle["width"] == 70
    r = PillowRenderer(1)
    images = [r.frame(s, t, (200, 160)) for t in (0, 1, 2, 1)]
    assert images[1].tobytes() == images[3].tobytes()
    assert images[0].tobytes() != images[1].tobytes()
    for i in range(60):
        r.frame(s, i / 30, (200, 160))
    assert len(r._sprites) <= 1
    assert c.width == 40
    assert images[2].getpixel((100, 80))[3] == 0


def test_text_color_and_transparent_none():
    c = Text("Test", font_size=30, position=(100, 80))
    s = Scene(Canvas(200, 160, "#00000000"))
    s.play(c.animate.color_to(None), rate_func=linear)
    assert s.entries[0].state_at(0.5)["color"] == (127.5, 127.5, 127.5, 127.5)
    assert render(s, 1).getbbox() is None


@pytest.mark.parametrize(
    "build",
    [
        lambda c: c.animate.scale_xy_to(0, 1),
        lambda c: c.animate.fill_to((0, 0, 0, 999)),
        lambda c: c.animate.width_to(-1),
        lambda c: c.animate.mask_to(width=2),
        lambda c: c.animate.progress_to(1),
    ],
)
def test_builder_validation(build):
    with pytest.raises(ValueError):
        build(Rectangle())


def test_nested_timing_and_absolute_cursor():
    a, b = Rectangle(), Rectangle()
    s = Scene().wait(10)
    with s.at(2):
        s.play(
            Stagger(
                Succession(a.animate.move_to(10, 0), a.animate.move_to(20, 0), duration=1),
                b.animate.opacity_to(0),
                lag=0.5,
                duration=1,
            )
        )
    assert s.time == 10
    assert s._objects[a].state_at(3.5)["position"] == (15, 0)
    assert s._objects[b].tracks[0].start == 2.5


def test_nested_interleaving_chronological_tracks():
    c = Rectangle()
    s = Scene()
    s.play(
        Stagger(
            Succession(c.animate.move_to(1, 0), c.animate.move_to(3, 0), duration=1, delay=2),
            c.animate.move_to(-1, 0),
            lag=0,
        )
    )
    assert [t.start for t in s.entries[0].tracks] == [0, 2, 3]


@pytest.mark.parametrize("ping_pong, expected", [(False, 10), (True, 0)])
def test_repeat_boundaries_and_final_state(ping_pong, expected):
    c = Rectangle()
    s = Scene()
    schedule = Repeat(c.animate.move_to(10, 0), cycles=2, ping_pong=ping_pong)
    s.play(schedule, rate_func=linear)
    e = s.entries[0]
    assert s.time == 2
    assert e.state_at(1)["position"] == ((10, 0) if ping_pong else (0, 0))
    assert e.state_at(2)["position"] == (expected, 0)
    assert e.state_at(0.5)["position"] == (5, 0)
    assert e.state_at(1.5)["position"] == (5, 0)


def test_nested_repeat_and_runtime():
    c = Rectangle()
    s = Scene()
    s.play(Repeat(Repeat(c.animate.opacity_to(0), cycles=2, ping_pong=True), cycles=2, ping_pong=True), run_time=8)
    assert s.time == 8
    assert s.entries[0].state_at(8)["opacity"] == 1


def test_schedule_conflict_is_atomic_with_existing_group():
    c = Rectangle()
    group = Group(c)
    s = Scene().add(group)
    entry = s._objects[c]
    with pytest.raises(ValueError):
        s.play(Stagger(c.animate.opacity_to(0), c.animate.opacity_to(0.5), lag=0.2))
    assert s.time == 0
    assert s._objects[c] is entry
    assert not entry.tracks
    assert len(s.entries) == 2


def test_existing_entry_identity_and_group_removal():
    c = Rectangle()
    s = Scene().add(Group(c))
    entry = s._objects[c]
    s.play(Repeat(c.animate.opacity_to(0), cycles=2))
    assert entry is s._objects[c]
    assert len(entry.tracks) == 2
    s.remove(next(c for c in s._objects if isinstance(c, Group)))
    assert entry.end == 2


@pytest.mark.parametrize(
    "mask", [RectangleMask(40, 40), CircleMask(20), ShapeMask(((0, 1), (0.5, 0), (1, 1)), width=40, height=40)]
)
def test_masks_clip_complete_group_and_preserve_transparency(mask):
    a = Rectangle(width=100, height=100, fill="red", stroke=None, position=(100, 80))
    b = Rectangle(width=80, height=80, fill="blue", stroke=None, position=(100, 80))
    g = Group(a, b, mask=mask)
    s = Scene(Canvas(200, 160, "#00000000")).add(g).wait(1)
    im = render(s, 0.5)
    assert im.getpixel((100, 85)) == (0, 0, 255, 255)
    assert im.getpixel((60, 80))[3] == 0


def test_animated_mask_and_wipe_sampling():
    c = Rectangle(width=100, height=100, fill="red", stroke=None, position=(100, 80), mask=RectangleMask(100, 100))
    s = Scene(Canvas(200, 160, "#00000000"))
    s.play(Wipe(c), c.animate.mask_to(position=(20, 0), width=40, height=80), rate_func=linear)
    r = PillowRenderer(1)
    middle = r.frame(s, 0.5, (200, 160)).tobytes()
    assert r.frame(s, 0, (200, 160)).getbbox() is None
    assert r.frame(s, 1, (200, 160)).getpixel((120, 80))[3] == 255
    assert r.frame(s, 0.5, (200, 160)).tobytes() == middle


@pytest.mark.parametrize(
    "direction, visible, hidden",
    [
        ("right", (70, 80), (130, 80)),
        ("left", (130, 80), (70, 80)),
        ("down", (100, 50), (100, 110)),
        ("up", (100, 110), (100, 50)),
    ],
)
def test_wipe_directions(direction, visible, hidden):
    c = Rectangle(width=100, height=100, fill="white", stroke=None, position=(100, 80))
    s = Scene(Canvas(200, 160, "#00000000"))
    s.play(Wipe(c, direction=direction))
    im = render(s, 0.5)
    assert im.getpixel(visible)[3] == 255
    assert im.getpixel(hidden)[3] == 0


def test_affine_nested_rotation_nonuniform_scaling():
    c = Rectangle(width=16, height=10, fill="white", stroke=None, position=(30, 20), rotation=30)
    inner = Group(c, rotation=40, scale_x=2, scale_y=0.7)
    outer = Group(inner, position=(100, 80), rotation=-20, scale_x=0.8, scale_y=1.3)
    s = Scene(Canvas(200, 160, "#00000000")).add(outer).wait(1)
    m = multiply(
        matrix(outer.state(), outer._origin), multiply(matrix(inner.state(), inner._origin), matrix(c.state()))
    )
    center = point(m, 0, 0)
    im = render(s, 0.5)
    assert im.getpixel(tuple(round(v) for v in center))[3] == 255
    # Affine-transformed raster bounds and public layout bounds should agree.
    box = im.getbbox()
    expected = outer.bounds
    assert expected.left <= box[0] < box[2] <= expected.right
    inside = point(m, 5, 2)
    assert im.getpixel(tuple(round(v) for v in inside))[3] > 200


@pytest.mark.parametrize("factory", [ProgressBar, ProgressRing, Gauge, LoadingDots, Checkmark])
def test_indicators_progress_endpoints_group_and_determinism(factory):
    c = factory(position=(100, 80), width=90, height=60)
    g = Group(c, rotation=10)
    s = Scene(Canvas(200, 160, "#00000000")).add(g)
    s.play(c.animate.progress_to(1), rate_func=linear)
    assert s._objects[c].state_at(0.5)["progress"] == 0.5
    r = PillowRenderer(1)
    before = r.frame(s, 0.25, (200, 160)).tobytes()
    r.frame(s, 1, (200, 160))
    assert r.frame(s, 0.25, (200, 160)).tobytes() == before
    assert not r._sprites
    with pytest.raises(ValueError):
        c.animate.progress_to(1.01)


def test_countdown_endpoints_and_validation():
    c = Countdown(3)
    s = Scene()
    s.play(c.animate.value_to(0), run_time=3, rate_func=linear)
    assert c.format(s.entries[0].state_at(0.1)["value"]) == "3"
    assert c.format(s.entries[0].state_at(3)["value"]) == "0"
    with pytest.raises(ValueError):
        c.animate.value_to(-1)
    with pytest.raises(ValueError):
        Repeat(c.animate.value_to(0), cycles=0)


def test_raw_invalid_color_is_atomic():
    s = Scene()
    with pytest.raises(ValueError):
        s.play(Animation(Rectangle(), {"fill": "red"}))
    assert s.entries == []


def test_evaluated_bounds_include_dynamic_geometry_and_ancestors():
    c = Rectangle(width=20, height=10, stroke_width=0)
    g = Group(c, scale_x=2, position=(100, 80))
    s = Scene().add(g)
    s.play(c.animate.width_to(60), rate_func=linear)
    assert s.bounds_at(c, 1).width == pytest.approx(124)
    assert s.bounds_at(c, 0).width == pytest.approx(44)
    assert c.width == 20


def test_masked_gif_clock_lifetimes_and_out_of_order():
    from io import BytesIO

    from PIL import Image as PILImage

    from faceless_champ import Image

    buffer = BytesIO()
    frames = [PILImage.new("RGBA", (10, 10), color) for color in ("red", "blue")]
    frames[0].save(buffer, format="GIF", save_all=True, append_images=frames[1:], duration=100, loop=0)
    c = Image.from_source(buffer.getvalue(), width=80, height=80, position=(100, 80))
    s = Scene(Canvas(200, 160, "#00000000")).wait(1)
    g = Group(c, mask=CircleMask(30))
    s.add(g).wait(1).remove(g)
    assert render(s, 1.05).getpixel((100, 80))[:3] == (255, 0, 0)
    assert render(s, 1.15).getpixel((100, 80))[:3] == (0, 0, 255)
    assert render(s, 2).getbbox() is None
    assert render(s, 1.05).getpixel((100, 80))[:3] == (255, 0, 0)


def test_masked_caption_clock():
    from faceless_champ import Captions, SubtitleCue, SubtitleTrack

    track = SubtitleTrack([SubtitleCue(1, 0, 0.5, "ONE"), SubtitleCue(2, 0.5, 1, "TWO")])
    c = Captions(track, width=180, font_size=24, position=(100, 80))
    s = Scene(Canvas(200, 160, "#00000000")).wait(1)
    s.add(Group(c, mask=RectangleMask(180, 100))).wait(1)
    r = PillowRenderer(1)
    first = r.frame(s, 1.2, (200, 160)).tobytes()
    assert first != r.frame(s, 1.7, (200, 160)).tobytes()
    assert first == r.frame(s, 1.2, (200, 160)).tobytes()


def test_ping_pong_reverses_easing_and_keyframes():
    from faceless_champ import ease_in

    c = Rectangle()
    a = Animation(c, {"rotation": 20}, keyframes={"rotation": ((0, 0), (0.25, 10), (1, 20))}, rate_func=ease_in)
    s = Scene().play(Repeat(a, cycles=2, ping_pong=True))
    e = s.entries[0]
    for t in (0.1, 0.3, 0.7, 0.9):
        assert e.state_at(t)["rotation"] == pytest.approx(e.state_at(2 - t)["rotation"])


def test_schedule_bad_lifetime_and_finite_count_are_atomic():
    c = Rectangle()
    s = Scene().add(c).wait(1).remove(c)
    with pytest.raises(ValueError):
        s.play(Repeat(c.animate.opacity_to(0), cycles=2))
    assert s.time == 1
    for cycles in (True, 0, 1.5, float("inf")):
        with pytest.raises(ValueError):
            Repeat(c.animate.opacity_to(0), cycles=cycles)


def test_masked_group_opacity_preserves_member_multiplication():
    a = Rectangle(width=100, height=100, fill="red", stroke=None, position=(100, 80))
    b = Rectangle(width=100, height=100, fill="blue", stroke=None, position=(100, 80))
    s = Scene(Canvas(200, 160, "#00000000")).add(Group(a, b, opacity=0.5, mask=RectangleMask(60, 60)))
    assert render(s, 0).getpixel((100, 80))[3] == 192


def test_bounds_and_group_wipe_with_interpolated_color():
    c = Rectangle(width=60, height=40, fill="red", position=(100, 80))
    g = Group(c)
    s = Scene(Canvas(200, 160)).add(g)
    s.play(Wipe(g), c.animate.fill_to("blue").width_to(100), rate_func=linear)
    assert s.bounds_at(c, 0.5).width == 88
    assert render(s, 0.5).getbbox() is not None


def test_countdown_rejects_negative_keyframes():
    c = Countdown(2)
    s = Scene()
    with pytest.raises(ValueError):
        s.play(Animation(c, {"value": 0}, keyframes={"value": ((0, 2), (0.5, -1), (1, 0))}))
    assert s.entries == []
