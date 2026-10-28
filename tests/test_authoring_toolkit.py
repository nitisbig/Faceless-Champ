"""Theme tokens, layout helpers, easing, motion helpers, primitives, runner and audit."""

import json
import pickle
from copy import deepcopy

import pytest

from faceless_champ import (
    THEMES,
    Arc,
    Badge,
    Bounds,
    Callout,
    Canvas,
    Circle,
    Divider,
    Dot,
    GlassCard,
    IconText,
    Pill,
    Rectangle,
    Scene,
    Stat,
    Text,
    Theme,
    contrast_ratio,
    cubic_bezier,
    design_audit,
    readable_color,
    run,
)
from faceless_champ.easing import EASINGS, easing
from faceless_champ.theme import active_theme, current_theme

# -- easing ---------------------------------------------------------------


@pytest.mark.parametrize("name", list(EASINGS))
def test_easing_presets_hit_endpoints(name):
    curve = EASINGS[name]
    assert curve(0) == pytest.approx(0, abs=1e-6)
    assert curve(1) == pytest.approx(1, abs=1e-6)


def test_cubic_bezier_is_monotonic_picklable_and_named_in_play():
    curve = cubic_bezier(0.2, 0, 0, 1)
    values = [curve(i / 50) for i in range(51)]
    assert values == sorted(values)
    assert pickle.loads(pickle.dumps(curve)) == curve
    assert easing("emphasized") is EASINGS["emphasized"]
    with pytest.raises(ValueError, match="Unknown easing"):
        easing("bouncy")
    with pytest.raises(ValueError, match="x control"):
        cubic_bezier(1.5, 0, 0, 1)
    dot = Circle(10, position=(0, 0))
    scene = Scene(Canvas(320, 180)).add(dot)
    scene.play(dot.animate.move_to(100, 0), run_time=1, rate_func="snappy")
    x = scene.entries[0].state_at(0.5)["position"][0]
    assert x > 90  # expo-out is far ahead of linear at the midpoint
    deepcopy(scene)


def test_through_visits_values_and_colors():
    box = Rectangle(width=40, height=40, fill="#000000", position=(0, 0))
    scene = Scene(Canvas(320, 180)).add(box)
    scene.play(box.animate.through("opacity", [0, 1, 0.5]), run_time=2, rate_func="linear")
    entry = scene.entries[0]
    assert entry.state_at(0)["opacity"] == 0
    assert entry.state_at(1)["opacity"] == pytest.approx(1)
    assert entry.state_at(2)["opacity"] == pytest.approx(0.5)
    scene.play(box.animate.through("fill", ["#000000", "#FF0000"], times=[0, 1]))
    assert entry.state_at(3)["fill"] == (255, 0, 0, 255)
    with pytest.raises(ValueError, match="one time per value"):
        box.animate.through("opacity", [0, 1], times=[0])


# -- motion helpers ------------------------------------------------------------


def test_play_at_and_reveal_keep_cursor_but_extend_duration():
    a, b = Text("A", position=(50, 50)), Text("B", position=(100, 50))
    scene = Scene(Canvas(320, 180))
    scene.reveal(a, b, stagger=0.2, duration=0.5, until=3)
    assert scene.time == 0
    assert scene.duration == pytest.approx(3)
    first, second = scene._objects[a], scene._objects[b]
    assert second.start == pytest.approx(0.2)
    assert first.end == pytest.approx(3) and second.end == pytest.approx(3)
    assert first.state_at(0)["opacity"] == 0
    assert first.state_at(1)["opacity"] == pytest.approx(1)
    pulse = Circle(5, position=(10, 10))
    scene.add(pulse)
    scene.play_at(4, pulse.animate.scale_to(2), run_time=1)
    assert scene.time == 0 and scene.duration == pytest.approx(5)
    with pytest.raises(ValueError, match="until leaves no time"):
        Scene(Canvas(320, 180)).reveal(Text("x"), until=0.5)
    with pytest.raises(ValueError, match="style"):
        Scene(Canvas(320, 180)).reveal(Text("x"), style="explode")


# -- theme --------------------------------------------------------------------


def test_theme_activation_sets_component_defaults_only_inside_block():
    assert active_theme() is None
    assert Text("plain").color == "white"
    neon = Theme.named("neon")
    with neon.use():
        assert current_theme() is neon
        title = Text("Title", role="title")
        assert title.color == neon.colors.text and "SpaceGrotesk" in title.font
        assert Text("x", role="label").color == neon.colors.primary
        assert Text("x", color="muted").color == neon.colors.muted
        assert neon.text("x", role="caption").color == neon.colors.muted
    assert active_theme() is None
    for name, theme in THEMES.items():
        assert theme.name == name
        assert contrast_ratio(theme.colors.text, theme.colors.background) >= 7, name
        assert contrast_ratio(theme.colors.text, theme.colors.surface) >= 4.5, name
    scaled = THEMES["midnight"].for_canvas(Canvas(3840, 2160))
    assert scaled.type_scale.title.font_size == pytest.approx(168) and scaled.margin == 128
    assert THEMES["paper"].canvas().bg == THEMES["paper"].colors.background
    assert THEMES["midnight"].space(6) == 64
    with pytest.raises(ValueError, match="Unknown theme"):
        Theme.named("rainbow")


def test_readable_color_and_contrast():
    assert contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21)
    assert readable_color("#FFFFFF") == "#111111"
    assert readable_color("#0B1020") == "#FFFFFF"


# -- layout --------------------------------------------------------------------


def test_bounds_helpers():
    canvas = Canvas(1920, 1080)
    safe = canvas.safe_area()
    assert safe == Bounds(64, 64, 1856, 1016)
    left, right = safe.columns((2, 1), gap=32)
    assert left.width == pytest.approx(2 * right.width) and right.left - left.right == pytest.approx(32)
    rows = safe.rows(3, gap=10)
    assert rows[0].top == 64 and rows[-1].bottom == pytest.approx(1016)
    cells = safe.grid(2, 3, gap=24)
    assert len(cells) == 6 and cells[1].left > cells[0].right
    assert safe.inset(10, top=0) == Bounds(74, 64, 1846, 1006)
    assert safe.point("bottom_right") == (1856, 1016)
    assert safe.fit(800, 450, align="top_left") == Bounds(64, 64, 864, 514)
    box = safe.aspect(16 / 9)
    assert box.width / box.height == pytest.approx(16 / 9)
    assert safe.contains(Bounds(100, 100, 200, 200)) and not safe.contains((0, 0))
    assert Bounds.from_center((10, 10), 4, 2) == Bounds(8, 9, 12, 11)
    assert Canvas(1080, 1920).is_portrait
    with pytest.raises(ValueError, match="gaps exceed"):
        Bounds(0, 0, 10, 10).columns(3, gap=10)
    with pytest.raises(ValueError, match="Unknown anchor"):
        safe.point("middle")


# -- primitives ------------------------------------------------------------


def test_primitives_build_measure_and_render():
    from faceless_champ import PillowRenderer

    with Theme.named("paper").use():
        scene = Scene(current_theme().canvas(640, 360))
        card = GlassCard(Bounds(340, 40, 620, 320))
        stat = Stat(42, "projects", (480, 180), suffix="%")
        pill = Pill("LIVE", (120, 40))
        badge = Badge("NEW", (480, 70))
        call = Callout("Peak", target=(150, 200), offset=(60, -40))
        arc = Arc((150, 200), 80, sweep=270)
        rule = Divider(Bounds(360, 280, 600, 280))
        item = IconText(Dot(radius=6), "Fast", (480, 300), role="caption")
        assert stat.value.text == "42%" and badge.background.fill == current_theme().colors.primary
        assert call.label.bounds.left > call.dot.bounds.right
        assert pill.text.bounds.width < pill.background.width
        with pytest.raises(AttributeError, match="no attribute or part"):
            _ = pill.nonexistent
        scene.add(card, arc, rule).reveal(stat, pill, badge, call, item, stagger=0.05)
        scene.wait(1)
    with PillowRenderer(1) as renderer:
        renderer.validate(scene)
        assert renderer.frame(scene, 0.9, (320, 180)).size == (320, 180)
    with pytest.raises(ValueError, match="sweep"):
        Arc((0, 0), 10, sweep=0)


# -- runner -------------------------------------------------------------------


def _scene():
    scene = Scene(Canvas(320, 180, "#101522"))
    scene.reveal(Text("Hello", role="heading", position=(160, 90)))
    return scene.wait(1)


def test_runner_frames_storyboard_audit_and_errors(tmp_path, capsys):
    code = run(_scene, argv=["--frame", "0.5", "--quality", "low"], name="demo", output_dir=tmp_path)
    result = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert code == 0 and result["ok"] and len(result["frames"]) == 1
    assert run(_scene, argv=["--storyboard", "2"], name="demo", output_dir=tmp_path) == 0
    result = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert result["storyboard"].endswith("storyboard.png")
    assert run(_scene, argv=["--audit"], output_dir=tmp_path) == 0
    assert json.loads(capsys.readouterr().out.strip().splitlines()[-1])["audit"]["ok"]
    assert run(_scene, argv=["--frame", "99"], output_dir=tmp_path) == 1
    assert run(lambda: 42, argv=["--frame", "0"], output_dir=tmp_path) == 1


def test_runner_preview_writes_video(tmp_path, capsys):
    code = run(_scene, argv=["--preview", "0.5", "--fps", "6"], name="demo", output_dir=tmp_path)
    result = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert code == 0 and (tmp_path / "demo_preview.mp4").stat().st_size > 0
    assert result["end"] == pytest.approx(0.5)


# -- audit ----------------------------------------------------------------------


def test_design_audit_flags_real_problems_and_passes_clean_scene():
    scene = Scene(Canvas(1920, 1080, "#0B1020"))
    scene.add(Rectangle(width=900, height=500, fill="#F4F4F4", stroke=None, position=(960, 540)))
    scene.add(Text("grey on white", font_size=30, color="#BBBBBB", position=(960, 500)))
    scene.add(Text("footnote", font_size=14, position=(300, 900)))
    scene.add(Text("edge", font_size=60, position=(1900, 60)))
    scene.wait(1)
    codes = {f.code for f in design_audit(scene, samples=1).findings}
    assert {"LOW_CONTRAST", "TEXT_TOO_SMALL", "OUTSIDE_FRAME"} <= codes
    with Theme.named("midnight").use():
        clean = Scene(current_theme().canvas())
        clean.add(Text("Readable title", role="title", position=(960, 400)))
        clean.add(Text("A short supporting line", role="body", position=(960, 560)))
        clean.wait(1)
    report = design_audit(clean, samples=2)
    assert report.ok and not report.findings, str(report)
