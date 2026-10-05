import math

import pytest
from PIL import Image as PILImage

from faceless_champ import (
    Animation,
    Bounds,
    Canvas,
    Captions,
    FadeIn,
    Group,
    Image,
    PillowRenderer,
    Rectangle,
    Scene,
    SubtitleCue,
    SubtitleTrack,
    Text,
    Typewriter,
    linear,
)


def tile(color="red", position=(40, 50), **kwargs):
    return Image.from_source(PILImage.new("RGB", (10, 10), color), width=10, height=10, position=position, **kwargs)


@pytest.mark.parametrize("direction", ["right", "left", "up", "down"])
def test_next_to_uses_transformed_edges_and_cross_axis_alignment(direction):
    target = Rectangle(width=50, height=20, position=(100, 80), scale=1.5, rotation=30)
    label = Text("Measured label", font_size=18, anchor="top_left", rotation=-15)
    label.next_to(target, direction=direction, gap=13)
    a, b = label.bounds, target.bounds
    if direction == "right":
        assert a.left - b.right == pytest.approx(13)
    elif direction == "left":
        assert b.left - a.right == pytest.approx(13)
    elif direction == "down":
        assert a.top - b.bottom == pytest.approx(13)
    else:
        assert b.top - a.bottom == pytest.approx(13)
    axis = 1 if direction in {"left", "right"} else 0
    assert a.center[axis] == pytest.approx(b.center[axis])


@pytest.mark.parametrize("edge", ["left", "right", "top", "bottom", "center_x", "center_y", "center"])
def test_align_to_bounds_preserves_other_axis(edge):
    component = tile(position=(12, 34))
    before = component.bounds
    target = Bounds(60, 70, 100, 120)
    assert component.align_to(target, edge=edge) is component
    after = component.bounds
    if edge in {"left", "right", "top", "bottom"}:
        assert getattr(after, edge) == pytest.approx(getattr(target, edge))
        axis = 1 if edge in {"left", "right"} else 0
        assert after.center[axis] == before.center[axis]
    else:
        for axis, name in enumerate(("center_x", "center_y")):
            assert after.center[axis] == (target.center[axis] if edge in {name, "center"} else before.center[axis])


def test_top_left_measurement_and_rotation_match_rendered_box():
    component = tile(anchor="top_left", position=(20, 30), scale=2, rotation=90)
    assert component.bounds == Bounds(20, 30, 40, 50)
    group = Group(component, anchor="top_left", position=(70, 20), rotation=90)
    box = group.bounds
    assert box.center == pytest.approx((60, 30))
    scene = Scene(Canvas(120, 80)).add(group).wait(1)
    assert PillowRenderer(1).frame(scene, 0, (120, 80)).getpixel((60, 30))[:3] == (255, 0, 0)


@pytest.mark.parametrize("direction,align", [("right", "top"), ("left", "bottom"), ("down", "left"), ("up", "right")])
def test_arrange_keeps_pivot_and_equal_edge_gaps(direction, align):
    a = tile(position=(20, 30))
    b = Rectangle(width=30, height=20, position=(60, 70), rotation=20)
    c = Text("Third", font_size=15, position=(80, 50))
    group = Group(a, b, c)
    pivot = group.position
    assert group.arrange(direction=direction, gap=9, align=align) is group
    assert group.bounds.center == pytest.approx(pivot)
    for first, second in zip(group.children, group.children[1:]):
        x, y = first.bounds, second.bounds
        differences = {
            "right": y.left - x.right,
            "left": x.left - y.right,
            "down": y.top - x.bottom,
            "up": x.top - y.bottom,
        }
        assert differences[direction] == pytest.approx(9)
        assert getattr(x, align) == pytest.approx(getattr(y, align))


def test_group_layout_and_direct_transforms_do_not_move_members():
    a, b = tile(position=(40, 50)), tile("blue", (80, 50))
    group = Group(a, b).move_to(100, 60)
    group.scale, group.rotation = 2, 90
    assert group.bounds.center == pytest.approx((100, 60))
    assert group.bounds.width == pytest.approx(20)
    assert group.bounds.height == pytest.approx(100)
    assert (a.position, b.position) == ((40, 50), (80, 50))
    group.next_to(Bounds(0, 0, 20, 20), direction="right", gap=7, align="top")
    assert group.bounds.left == pytest.approx(27)
    assert group.bounds.top == pytest.approx(0)


def test_nested_animation_combines_transforms_and_opacity_deterministically():
    red = tile(position=(40, 50))
    blue = tile("blue", (80, 50))
    inner = Group(red, blue)
    outer = Group(inner, opacity=0.5)
    scene = Scene(Canvas(180, 140))
    # Child first deliberately checks that play() adds the parent before its members.
    scene.play(
        red.animate.move_to(50, 50),
        outer.animate.move_to(100, 60).scale_to(2).rotate_to(90),
        run_time=2,
        rate_func=linear,
    )
    scene.wait(1)
    renderer = PillowRenderer(1)
    renderer.validate(scene)
    end = renderer.frame(scene, 2, (180, 140))
    assert end.getpixel((100, 40))[:3] == (128, 0, 0)
    assert end.getpixel((100, 100))[:3] == (0, 0, 128)
    middle = renderer.frame(scene, 1, (180, 140)).tobytes()
    renderer.frame(scene, 0, (180, 140))
    assert renderer.frame(scene, 1, (180, 140)).tobytes() == middle
    outer.move_to(999, 999)
    red.move_to(999, 999)
    assert renderer.frame(scene, 2, (180, 140)).tobytes() == end.tobytes()


def test_nested_group_and_member_transforms_compose_in_parent_order():
    red = tile(position=(30, 30))
    inner = Group(red, position=(50, 30), rotation=90, scale=2)
    outer = Group(inner, position=(90, 80), rotation=90, scale=2)
    scene = Scene(Canvas(160, 160)).add(outer).wait(1)
    # A child offset along inner X becomes +Y, then -X in the outer frame.
    scene.play(red.animate.move_to(35, 30), run_time=1)
    frame = PillowRenderer(1).frame(scene, 2, (160, 160))
    assert frame.getpixel((70, 80))[:3] == (255, 0, 0)


def test_group_opacity_and_stacking_are_inherited_with_local_child_order():
    low = tile("red", opacity=0.5, z_index=100)
    high = tile("blue", opacity=0.5, z_index=200)
    group = Group(low, high, opacity=0.5, z_index=0)
    cover = tile("lime", z_index=1)
    scene = Scene(Canvas(100, 100)).add(cover, group).wait(1)
    renderer = PillowRenderer(1)
    assert renderer.frame(scene, 0, (100, 100)).getpixel((40, 50))[:3] == (0, 255, 0)
    scene.remove(cover)
    frame = renderer.frame(scene, 1, (100, 100))
    assert frame.getpixel((40, 50))[:3] == (48, 0, 64)


def test_child_reveal_and_group_fade_can_run_together():
    label = Text("GROUP", font_size=24, position=(80, 45))
    group = Group(label)
    scene = Scene(Canvas(160, 90))
    scene.play(FadeIn(group), Typewriter(label), run_time=1, rate_func=linear)
    renderer = PillowRenderer(1)
    assert renderer.frame(scene, 0, (160, 90)).convert("RGB").getbbox() is None
    assert renderer.frame(scene, 0.5, (160, 90)).convert("RGB").getbbox() is not None
    assert scene._objects[label].state_at(0.5)["reveal"] == 0.5


def test_group_removal_checks_descendant_tracks_and_stops_captions():
    track = SubtitleTrack([SubtitleCue(1, 0, 8, "Long caption")])
    captions = Captions(track, width=140, font_size=15, position=(80, 70))
    dot = tile()
    group = Group(dot, Group(captions))
    scene = Scene(Canvas(160, 90)).add(group)
    scene.play(dot.animate.move_to(80, 50), run_time=2)
    assert scene.duration == 8
    with scene.at(1), pytest.raises(ValueError, match="animations end"):
        scene.remove(group)
    scene.remove(group)
    assert scene.duration == 2
    assert all(entry.end == 2 for entry in scene.entries)
    with pytest.raises(ValueError, match="lifetime"):
        scene.play(dot.animate.opacity_to(0))
    assert PillowRenderer(1).frame(scene, 2, (160, 90)).convert("RGB").getbbox() is None


def test_group_gif_preserves_introduction_clock_and_cache_invalidation(tmp_path):
    path = tmp_path / "two.gif"
    a, b = PILImage.new("RGB", (10, 10), "red"), PILImage.new("RGB", (10, 10), "blue")
    a.save(path, save_all=True, append_images=[b], duration=[100, 300], loop=0)
    group = Group(Image(path, width=10, height=10, position=(40, 50)))
    scene = Scene(Canvas(100, 100)).wait(2).add(group).wait(1)
    renderer = PillowRenderer(1)
    for time, color in [(1.9, (0, 0, 0)), (2.05, (255, 0, 0)), (2.2, (0, 0, 255)), (2.45, (255, 0, 0))]:
        assert renderer.frame(scene, time, (100, 100)).getpixel((40, 50))[:3] == color


def test_invalid_membership_and_add_or_play_are_atomic():
    shared = tile()
    with pytest.raises(ValueError):
        Group()
    with pytest.raises(TypeError):
        Group("bad")
    with pytest.raises(ValueError, match="once"):
        Group(Group(shared), shared)
    scene = Scene().add(shared)
    group = Group(tile("blue"), shared)
    with pytest.raises(ValueError, match="reparented"):
        scene.play(group.animate.move_to(100, 100))
    assert len(scene.entries) == 1 and not scene.entries[0].tracks and scene.time == 0
    first, second = Group(shared), Group(shared)
    fresh = Scene()
    with pytest.raises(ValueError, match="multiple groups"):
        fresh.add(first, second)
    assert not fresh.entries
    with pytest.raises(TypeError):
        fresh.add(tile(), "bad")
    assert not fresh.entries
    with pytest.raises(ValueError, match="Groups support"):
        fresh.play(Animation(first, {"draw": 0}))
    assert not fresh.entries


def test_existing_child_add_is_noop_and_layout_changes_are_snapshotted():
    child = tile()
    group = Group(child)
    scene = Scene(Canvas(100, 100)).add(child, group, group).wait(1)
    assert len(scene.entries) == 2
    scene.add(child, group)
    assert len(scene.entries) == 2
    group.arrange().move_to(90, 90)
    child.shift(100, 100)
    assert PillowRenderer(1).frame(scene, 0, (100, 100)).getpixel((40, 50))[:3] == (255, 0, 0)


def test_invalid_layout_arguments_do_not_mutate_positions():
    a, b = tile(), tile("blue", (80, 50))
    group = Group(a, b)
    original = (a.position, b.position, group.position)
    for kwargs in ({"direction": "diagonal"}, {"gap": -1}, {"gap": math.nan}, {"align": "left"}):
        with pytest.raises(ValueError):
            group.arrange(**kwargs)
        assert (a.position, b.position, group.position) == original
    with pytest.raises(ValueError):
        a.align_to(b, edge="baseline")
    with pytest.raises(TypeError):
        a.next_to("bad")
    with pytest.raises(ValueError):
        Bounds(2, 0, 1, 3)
    assert (a.position, b.position, group.position) == original


def test_layout_of_missing_images_uses_reserved_dimensions(tmp_path):
    image = Image(tmp_path / "later.png", width=80, height=40, anchor="top_left", position=(10, 20))
    assert image.bounds == Bounds(10, 20, 90, 60)
    assert Group(image).bounds == image.bounds


@pytest.mark.parametrize("size", [(100, 100), (150, 150), (200, 200)])
def test_identity_group_matches_standalone_rendering_at_multiple_resolutions(size):
    def members():
        return [
            Image.from_source(
                PILImage.new("RGB", (13, 9), "red"),
                width=13,
                height=9,
                position=(25.5, 40.5),
                anchor="top_left",
                scale=0.7,
                rotation=25,
            ),
            Text("Text", font_size=16, position=(70, 65)),
        ]

    standalone = Scene(Canvas(100, 100)).add(*members()).wait(1)
    grouped = Scene(Canvas(100, 100)).add(Group(*members())).wait(1)
    renderer = PillowRenderer(2)
    assert renderer.frame(grouped, 0, size).tobytes() == renderer.frame(standalone, 0, size).tobytes()
