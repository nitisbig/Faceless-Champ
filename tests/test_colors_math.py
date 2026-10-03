"""Color roles, glyph layout, font weight isolation, and smooth curve caps."""

from dataclasses import replace
from pathlib import Path

import pytest

from faceless_champ import (
    COLOR_SCHEMES,
    Canvas,
    ColorScheme,
    Equation,
    PillowRenderer,
    Polyline,
    Scene,
    Text,
    Write,
    with_alpha,
)


def test_named_schemes_custom_roles_and_series():
    for name, scheme in COLOR_SCHEMES.items():
        assert ColorScheme.named(name) is scheme
        assert scheme.color("primary") == scheme.series(0)
        assert len({scheme.series(i) for i in range(4)}) == 4
        assert scheme.series(4) == scheme.primary
    custom = replace(ColorScheme.named("paper"), name="brand", primary="#123456")
    assert custom.color("primary") == "#123456"
    with pytest.raises(ValueError, match="Unknown color scheme"):
        ColorScheme.named("missing")
    with pytest.raises(ValueError, match="Unknown color role"):
        custom.color("name")
    with pytest.raises(ValueError, match="Invalid primary"):
        ColorScheme(primary="not-a-color")
    with pytest.raises(ValueError, match="nonnegative"):
        custom.series(-1)


def test_alpha_preserves_existing_transparency():
    assert with_alpha("red", 0.5) == "#ff000080"
    assert with_alpha("#33669980", 0.5) == "#33669940"
    assert with_alpha("blue", 0) == "#0000ff00"
    assert with_alpha("blue", 1) == "#0000ffff"
    for value in (-1, 1.1, float("nan")):
        with pytest.raises(ValueError):
            with_alpha("red", value)


@pytest.mark.parametrize("key", ["word", "$", "", " ", r"\frac{x}{y}", "\n"])
def test_equation_rejects_ambiguous_color_keys(key):
    with pytest.raises(ValueError, match="color_map keys"):
        Equation("x", color_map={key: "red"})


def test_symbol_colors_preserve_whole_formula_geometry_and_write(tmp_path, monkeypatch):
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    pytest.importorskip("matplotlib")
    source = r"x=\frac{a^2+\mu}{b}"
    options = {"font_size": 64, "position": (200, 90), "max_width": 180}
    first = Equation(source, color_map={"x": "red", "a": "blue", r"\mu": "lime"}, **options)
    second = Equation(source, color_map={"x": "cyan", "a": "yellow", r"\mu": "magenta"}, **options)
    renderer = PillowRenderer(2)
    a = renderer.frame(Scene(Canvas(400, 180, "#00000000")).add(first), 0, (400, 180))
    b = renderer.frame(Scene(Canvas(400, 180, "#00000000")).add(second), 0, (400, 180))
    assert a.getchannel("A").tobytes() == b.getchannel("A").tobytes()
    assert a.tobytes() != b.tobytes()
    # Inspect the original glyph sprite: colored variables plus neutral operators.
    sprite = renderer._equation(first, 2)
    pixels = sprite.tobytes()
    colors = {tuple(pixels[i : i + 3]) for i in range(0, len(pixels), 4) if pixels[i + 3] == 255}
    assert {(255, 0, 0), (0, 0, 255), (0, 255, 0), (255, 255, 255)} <= colors
    scene = Scene(Canvas(400, 180, "#00000000"))
    scene.play(Write(first), run_time=1)
    partial = renderer.frame(scene, 0.5, (400, 180))
    visible = partial.getchannel("A").point(lambda alpha: 255 if alpha >= 128 else 0)
    assert visible.getbbox()[2] <= 201
    assert renderer.frame(scene, 0, (400, 180)).getbbox() is None
    assert renderer.frame(scene, 1, (400, 180)).tobytes() == a.tobytes()
    assert renderer.frame(scene, 0.5, (400, 180)).tobytes() == partial.tobytes()


def test_color_map_alias_conflicts_and_invalid_colors_fail_validation(tmp_path, monkeypatch):
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    pytest.importorskip("matplotlib")
    with pytest.raises(ValueError, match="conflicting aliases"):
        PillowRenderer().validate(Scene().add(Equation(r"\mu", color_map={r"\mu": "red", "μ": "blue"})))
    with pytest.raises(ValueError):
        PillowRenderer().validate(Scene().add(Equation("x", color_map={"x": "not-a-color"})))
    with pytest.raises(ValueError, match="Invalid Equation"):
        PillowRenderer().validate(Scene().add(Equation("x", color_map={r"\notacommand": "red"})))


def test_font_weight_requires_variable_font():
    with pytest.raises(ValueError, match="variable font"):
        PillowRenderer().validate(Scene().add(Text("Hello", font_weight=600)))


def test_variable_font_weight_cache_does_not_leak_between_texts():
    path = Path(__file__).resolve().parents[1] / "assets/fonts/SpaceGrotesk[wght].ttf"
    if not path.is_file():
        pytest.skip("Optional example variable font is not present")
    renderer = PillowRenderer(1)
    regular = Text("Readable equations", font=path, font_weight=400)
    strong = Text("Readable equations", font=path, font_weight=600)
    font = renderer._font(regular, 32)
    before = bytes(font.getmask(regular.text))
    assert renderer._font(strong, 32) is not font
    assert bytes(renderer._font(regular, 32).getmask(regular.text)) == before
    with pytest.raises(ValueError, match="Weight axis"):
        renderer._font(Text("x", font=path, font_weight=900), 32)


def test_round_caps_extend_open_curve_endpoints_only():
    points = [(15, 40), (85, 40)]
    renderer = PillowRenderer(1)
    butt = renderer.frame(Scene(Canvas(100, 80, "#00000000")).add(Polyline(points, stroke_width=6)), 0, (100, 80))
    rounded = renderer.frame(
        Scene(Canvas(100, 80, "#00000000")).add(Polyline(points, stroke_width=6, line_cap="round")), 0, (100, 80)
    )
    assert rounded.getbbox()[0] < butt.getbbox()[0]
    assert rounded.getbbox()[2] > butt.getbbox()[2]
    with pytest.raises(ValueError, match="line_cap"):
        Polyline(points, line_cap="invalid")


def test_held_scene_cache_reuses_pixels_and_invalidates_for_new_visuals(monkeypatch):
    scene = Scene(Canvas(100, 80, "#00000000")).add(Text("a", position=(50, 40), font_size=24))
    renderer = PillowRenderer(2)
    sprite = renderer._sprite
    calls = []

    def record(*args):
        calls.append(args)
        return sprite(*args)

    monkeypatch.setattr(renderer, "_sprite", record)
    first = renderer.frame(scene, 0, (100, 80))
    assert renderer.frame(scene, 2, (100, 80)).tobytes() == first.tobytes()
    assert len(calls) == 1
    first.paste("red", (0, 0, 100, 80))
    assert renderer.frame(scene, 3, (100, 80)).getpixel((0, 0))[3] == 0
    added = Text("b", position=(15, 15), font_size=24)
    scene.add(added)
    assert renderer.frame(scene, 3, (100, 80)).getbbox()[0] < 40
    assert len(calls) == 3
    scene.remove(added)
    assert renderer.frame(scene, 3, (100, 80)).getbbox()[0] >= 40
    renderer.frame(scene, 3, (200, 160))
    assert len(calls) == 5


def test_held_scene_cache_preserves_animation_sampling_and_canvas_changes():
    scene = Scene(Canvas(100, 80, "#00000000"))
    path = Polyline([(15, 40), (85, 40)], stroke_width=4)
    scene.play(path.animate.opacity_to(0), run_time=1)
    renderer = PillowRenderer(2)
    start = renderer.frame(scene, 0, (100, 80))
    middle = renderer.frame(scene, 0.5, (100, 80))
    assert start.tobytes() != middle.tobytes()
    assert renderer.frame(scene, 2, (100, 80)).getbbox() is None
    assert renderer.frame(scene, 0.5, (100, 80)).tobytes() == middle.tobytes()
    scene.canvas = Canvas(100, 80, "blue")
    assert renderer.frame(scene, 2, (100, 80)).getpixel((0, 0)) == (0, 0, 255, 255)


def test_scene_frame_cache_respects_memory_budget_and_can_be_disabled():
    first, second = Scene(Canvas(100, 80, "red")), Scene(Canvas(100, 80, "blue"))
    renderer = PillowRenderer(1, frame_cache_mb=0.04)
    renderer.frame(first, 0, (100, 80))
    renderer.frame(second, 0, (100, 80))
    assert first not in renderer._scene_frames
    assert len(renderer._scene_frames) == 1
    assert renderer._frame_cache_bytes <= renderer._frame_cache_limit
    assert renderer.frame(first, 1, (100, 80)).getpixel((0, 0)) == (255, 0, 0, 255)
    assert second not in renderer._scene_frames
    disabled = PillowRenderer(1, frame_cache_mb=0)
    disabled.frame(first, 0, (100, 80))
    assert not disabled._scene_frames
    with pytest.raises(ValueError, match="frame_cache_mb"):
        PillowRenderer(frame_cache_mb=-1)
