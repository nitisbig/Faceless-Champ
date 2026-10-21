"""Procedural surfaces keep allocated geometry, soft pixels, and ordinary motion."""

from dataclasses import replace
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image as PILImage

from faceless_champ import (
    CLEAN_FLOW_FONT,
    Bounds,
    Canvas,
    ColorScheme,
    FadeIn,
    PillowRenderer,
    Scene,
    ShadowStyle,
    Text,
    card_content_bounds,
    card_surface,
    dot_grid,
)
from facelesschamp_kit.charts import BarChart, ChartStyle
from facelesschamp_kit.coding import CodeTheme


def pixels(component):
    with PILImage.open(BytesIO(component.source_bytes)) as image:
        return image.convert("RGBA")


def test_shadow_card_retains_allocated_bounds_and_soft_edge():
    allocated = Bounds(50, 80, 650, 500)
    shadow = ShadowStyle()
    card = card_surface(allocated, shadow=shadow)
    source = pixels(card)
    assert card.bounds == allocated
    assert card.path is None and not card.trim
    assert source.size == (1200, 840)
    assert source.getpixel((600, 420)) == (255, 255, 255, 255)
    assert source.getpixel((0, 0))[3] == 0
    # Rounded face corners remain translucent; the shadow fades past the face.
    assert source.getpixel((121, 121))[3] < 255
    near, far = (source.getpixel((600, y))[3] for y in (750, 800))
    assert 0 < far < near < 38
    assert card_content_bounds(allocated, shadow=shadow) == Bounds(138, 168, 562, 412)


def test_surface_motion_replays_pixels_without_rasterizing_again(monkeypatch):
    card = card_surface(Bounds(0, 0, 400, 300), shadow=ShadowStyle(blur=6, offset=(0, 4)))
    scene = Scene(Canvas(400, 300, "#00000000"))
    scene.play(FadeIn(card), run_time=1)

    def fail(*args, **kwargs):
        raise AssertionError("Shadows must be generated during surface construction")

    monkeypatch.setattr("faceless_champ.surfaces.ImageFilter.GaussianBlur", fail)
    with PillowRenderer(1) as renderer:
        assert renderer.frame(scene, 0, (400, 300)).getbbox() is None
        half = renderer.frame(scene, 0.5, (400, 300))
        full = renderer.frame(scene, 1, (400, 300))
        assert 120 <= half.getpixel((200, 150))[3] <= 135
        assert full.getpixel((200, 150)) == (255, 255, 255, 255)
        assert len(renderer._images) == 1
        assert len(renderer._sprites) == 1


def test_dot_grid_is_transparent_deterministic_and_keeps_bounds():
    bounds = Bounds(16, 24, 216, 144)
    first, second = dot_grid(bounds), dot_grid(bounds)
    source = pixels(first)
    assert first.source_bytes == second.source_bytes
    assert first.bounds == bounds
    assert source.getpixel((28, 28)) == (183, 179, 174, 85)
    assert source.getpixel((0, 0))[3] == 0
    assert source.getpixel((40, 40))[3] == 0


def test_transparent_chart_fits_shadow_card_content():
    bounds = Bounds(0, 0, 640, 480)
    shadow = ShadowStyle()
    content = card_content_bounds(bounds, shadow=shadow)
    style = ChartStyle(scheme=replace(ColorScheme.named("clean-flow"), surface="#00000000"), grid=False)
    chart = BarChart(
        ("Compose", "Replay"),
        {"Tasks": (4, 7)},
        width=content.width,
        height=content.height,
        position=content.center,
        style=style,
    )
    assert chart.bounds == content
    scene = Scene(Canvas(640, 480, "#E8E6E2")).add(card_surface(bounds, shadow=shadow), chart)
    with PillowRenderer(1) as renderer:
        renderer.validate(scene)
        frame = renderer.frame(scene, 0, (640, 480))
    assert frame.getpixel((320, 70)) == (255, 255, 255, 255)
    assert frame.getpixel((0, 0)) == (232, 230, 226, 255)


def test_packaged_clean_flow_font_and_editor_colors():
    assert Path(CLEAN_FLOW_FONT).is_file()
    assert Path(CLEAN_FLOW_FONT).with_name("dmsans-OFL.txt").is_file()
    with PillowRenderer(1) as renderer:
        regular = renderer._font(Text("Clean flow", font=CLEAN_FLOW_FONT, font_weight=400), 48)
        bold = renderer._font(Text("Clean flow", font=CLEAN_FLOW_FONT, font_weight=700), 48)
        assert bytes(regular.getmask("Clean flow")) != bytes(bold.getmask("Clean flow"))
        assert renderer._font(Text("Clean flow", font=CLEAN_FLOW_FONT, font_weight=400), 48) is regular
    scheme = ColorScheme.named("clean-flow")
    assert (scheme.background, scheme.surface, scheme.text, scheme.primary) == (
        "#E8E6E2",
        "#FFFFFF",
        "#111111",
        "#FF5A20",
    )
    code = CodeTheme.named("clean-flow")
    assert (code.background, code.chrome, code.accent) == ("#14161A", "#1F2329", "#FF5A20")


@pytest.mark.parametrize("factory", [card_surface, dot_grid])
def test_surfaces_reject_empty_bounds_or_geometry_overrides(factory):
    with pytest.raises(ValueError, match="one design pixel"):
        factory(Bounds(0, 0, 0, 20))
    with pytest.raises(TypeError, match="Bounds"):
        factory((0, 0, 200, 100))
    with pytest.raises(TypeError, match="reserve geometry"):
        factory(Bounds(0, 0, 200, 100), trim=True)


def test_surface_styles_reject_invalid_geometry():
    for kwargs in ({"blur": -1}, {"offset": (1,)}, {"offset": (float("nan"), 0)}):
        with pytest.raises(ValueError):
            ShadowStyle(**kwargs)
    with pytest.raises(ValueError, match="too small"):
        card_surface(Bounds(0, 0, 100, 100), shadow=ShadowStyle())
    with pytest.raises(ValueError, match="too small"):
        card_content_bounds(Bounds(0, 0, 400, 300), padding=200)
    with pytest.raises(ValueError, match="dot spacing"):
        dot_grid(Bounds(0, 0, 100, 100), spacing=0)
