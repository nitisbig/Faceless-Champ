"""Independent fixtures for animated gradient lifetime and alpha-edge regressions."""

from faceless_champ import (
    Bounds,
    Canvas,
    GradientStop,
    Group,
    LinearGradient,
    PillowRenderer,
    Scene,
    ShadowStyle,
    Spring,
    card_surface,
    smooth,
)


def gradient_scene():
    scene = Scene(Canvas(960, 540, "#EFF2F7"))
    surface = card_surface(
        Bounds(330, 54, 630, 254),
        fill=LinearGradient(
            (GradientStop(0, "#FFFFFF"), GradientStop(0.55, "#DCE8FF"), GradientStop(1, "#99B6F2")), angle=125
        ),
        radius=26,
        shadow=ShadowStyle(color="#304C7138", blur=7, offset=(0, 6)),
    )
    group = Group(surface, position=(480, 172), scale=0.94, opacity=0)
    scene.add(group)
    with scene.at(0.24):
        scene.play(group.animate.move_to(480, 154).scale_to(1), run_time=1.4, rate_func=Spring(100, 20, 1))
    with scene.at(0.24):
        scene.play(group.animate.opacity_to(1), run_time=0.35, rate_func=smooth)
    with scene.at(3):
        scene.play(group.animate.rotate_to(4).scale_to(1.03), run_time=0.9, rate_func=Spring(100, 20, 1))
    scene.wait_until(4)
    return scene


def test_gradient_entrance_lifetime_and_out_of_order_sampling():
    scene = gradient_scene()
    assert all(entry.start == 0 for entry in scene.entries)
    with PillowRenderer(1) as renderer:
        entrance = renderer.frame(scene, 0.4, (240, 135))
        settled = renderer.frame(scene, 2.5, (240, 135))
        transformed = renderer.frame(scene, 3.5, (240, 135))
        assert entrance.tobytes() != settled.tobytes() != transformed.tobytes()
        assert renderer.frame(scene, 2.5, (240, 135)).tobytes() == settled.tobytes()


def test_rotated_pale_gradient_edge_does_not_ring_white():
    with PillowRenderer(1) as renderer:
        frame = renderer.frame(gradient_scene(), 3.5, (960, 540))
    assert not any(min(frame.getpixel((x, y))[:3]) >= 250 for y in range(215, 243) for x in range(365, 595))
