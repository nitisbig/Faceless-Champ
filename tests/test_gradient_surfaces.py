"""Surface integration: legacy pixels, alpha, transforms, clocks and resource ownership."""

import gc
import inspect
import json
import random
import weakref
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from pathlib import Path

import PIL
import pytest
from PIL import Image as PI

from facelesschamp_kit.charts import BarChart, ChartStyle
from faceless_champ import (
    Bounds,
    Canvas,
    ColorScheme,
    GradientStop,
    Group,
    Image,
    LinearGradient,
    PillowRenderer,
    RadialGradient,
    RectangleMask,
    Scene,
    ShadowStyle,
    Spring,
    card_content_bounds,
    card_surface,
    gradient_surface,
    smooth,
)
from faceless_champ._surface_raster import _allocation, _paint
from facelesschamp_kit.web import HtmlClip, WebCapture


def paint(color="red", second="blue", angle=0):
    return LinearGradient((GradientStop(0, color), GradientStop(1, second)), angle=angle)


def pixels(component):
    with PI.open(BytesIO(component.source_bytes)) as image:
        return image.convert("RGBA")


def rgba_pixels(image):
    data = iter(image.tobytes())
    return zip(data, data, data, data)


@pytest.mark.parametrize("width,height", [(100.3, 80), (100, 80.3), (100.3, 80.3), (100.2, 80.2), (100.75, 80.75)])
@pytest.mark.parametrize("gradient", [paint("red", "red"), paint(), RadialGradient(paint().stops)])
def test_fractional_rectangular_backdrop_fills_rounded_allocation(width, height, gradient):
    backdrop = gradient_surface(Bounds(0, 0, width, height), fill=gradient)
    with pixels(backdrop) as source, source.getchannel("A") as alpha:
        assert source.size == (round(width * 2), round(height * 2))
        assert alpha.getextrema() == (255, 255)
        if isinstance(gradient, LinearGradient):
            assert source.getpixel((0, source.height // 2)) == gradient.stops[0]._rgba
            assert source.getpixel((source.width - 1, source.height // 2)) == gradient.stops[-1]._rgba


@pytest.mark.parametrize("radius", [0, 12])
def test_fractional_card_face_remains_centered_inside_shadow_clearance(radius):
    card = card_surface(
        Bounds(0, 0, 100.3, 80.3),
        fill=paint(),
        radius=radius,
        shadow=ShadowStyle(color="#00000000", blur=2, offset=(0, 0)),
    )
    with (
        pixels(card) as source,
        source.getchannel("A") as alpha,
        alpha.transpose(PI.Transpose.FLIP_LEFT_RIGHT) as horizontal,
        alpha.transpose(PI.Transpose.FLIP_TOP_BOTTOM) as vertical,
    ):
        assert alpha.tobytes() == horizontal.tobytes() == vertical.tobytes()


@pytest.mark.parametrize("kind", ["linear", "radial"])
@pytest.mark.parametrize("shadow", [None, ShadowStyle(), ShadowStyle(color="#E1452980", blur=5, offset=(-4.25, 3.5))])
def test_gradient_card_keeps_allocation_coverage_and_content_bounds(kind, shadow):
    bounds = Bounds(13.25, 17.5, 413.75, 318.25)
    gradient = paint() if kind == "linear" else RadialGradient(paint().stops)
    card = card_surface(bounds, fill=gradient, radius=30, shadow=shadow, opacity=0.7, z_index=-2)
    legacy = card_surface(bounds, fill="white", radius=30, shadow=shadow)
    assert isinstance(card, Image) and card.bounds == legacy.bounds
    assert card.position == bounds.center and (card.width, card.height) == (bounds.width, bounds.height)
    assert card.path is None and not card.trim and card.opacity == 0.7 and card.z_index == -2
    inset = 28 if shadow is None else (88 if shadow.blur == 16 else 48)
    assert card_content_bounds(bounds, shadow=shadow) == Bounds(
        bounds.left + inset, bounds.top + inset, bounds.right - inset, bounds.bottom - inset
    )
    with pixels(card) as source:
        assert source.size == (801, 602)
        assert source.getpixel((400, 300))[3] == 255
        assert source.getpixel((0, 0)) == (0, 0, 0, 0)


def test_alpha_only_shadow_does_not_darken_colored_fringe_or_show_through_face():
    shadow = ShadowStyle(color="#E1452980", blur=6, offset=(0, 4))
    card = card_surface(Bounds(0, 0, 240, 180), fill=paint("#0000FF00", "#FF000000"), shadow=shadow, radius=24)
    with pixels(card) as source:
        assert source.getpixel((240, 180)) == (0, 0, 0, 0)  # clear face replaces shadow
        translucent = [rgba for rgba in rgba_pixels(source) if 0 < rgba[3] < 128]
        assert translucent
        assert all(rgba[:3] == (225, 69, 41) for rgba in translucent)
        assert all(rgba == (0, 0, 0, 0) for rgba in rgba_pixels(source) if rgba[3] == 0)


def test_paint_domain_is_face_not_padded_viewport():
    card = card_surface(Bounds(0, 0, 240, 180), fill=paint(), radius=0, shadow=ShadowStyle(blur=6, offset=(0, 4)))
    # Padding is ceil(18 + 4) = 22 design pixels, 44 source pixels per side.
    with pixels(card) as source:
        # Coverage is antialiased at the geometric border; test paint two samples inside.
        assert source.getpixel((46, 180)) == (254, 0, 1, 255)
        assert source.getpixel((433, 180)) == (1, 0, 254, 255)
    content = card_content_bounds(Bounds(0, 0, 240, 180), shadow=ShadowStyle(blur=6, offset=(0, 4)), padding=4)
    chart = BarChart(
        ("A", "B"),
        {"Count": (2, 4)},
        width=content.width,
        height=content.height,
        position=content.center,
        style=ChartStyle(
            scheme=replace(ColorScheme.named("clean-flow"), surface="#00000000"), grid=False, font_size=9, legend=False
        ),
    )
    scene = Scene(Canvas(240, 180, "#E8E6E2")).add(card, chart).wait(1)
    with PillowRenderer(1) as renderer:
        frame = renderer.frame(scene, 0, (240, 180))
    assert chart.bounds == content
    # Sample blank padding inside the chart viewport, allowing normal resampling quantization.
    r, g, b, a = frame.getpixel((120, 30))
    assert g <= 2 and r > 100 and b > 100 and a == 255


@pytest.mark.parametrize("aa", [1, 2, 4])
@pytest.mark.parametrize("size", [(240, 180), (480, 360)])
def test_transparent_gradient_resampling_has_no_black_or_hidden_blue_fringe(aa, size):
    card = card_surface(
        Bounds(30, 30, 210, 150), fill=paint("red", "#0000FF00"), radius=24, rotation=8, scale_x=0.85, scale_y=1.05
    )
    scene = Scene(Canvas(240, 180, "#00000000")).add(card).wait(1)
    with PillowRenderer(aa) as renderer:
        frame = renderer.frame(scene, 0.5, size)
        # Unpremultiplication in Pillow's 8-bit transforms may quantize very low coverage.
        visible = [p for p in rgba_pixels(frame) if p[3] > 16]
        assert visible and all(p[0] >= 250 and p[1] == p[2] == 0 for p in visible)
        assert frame.getpixel((0, 0))[3] == 0


def test_nested_masks_opacity_and_local_sibling_stacking():
    bounds = Bounds(20, 20, 140, 100)
    red = gradient_surface(bounds, fill=paint("red", "red"), z_index=100)
    blue = gradient_surface(bounds, fill=paint("blue", "blue"), z_index=200)
    inner = Group(red, blue, opacity=0.5, mask=RectangleMask(60, 50))
    outer = Group(inner, mask=RectangleMask(80, 60))
    scene = Scene(Canvas(160, 120, "#00000000")).add(outer).wait(1)
    with PillowRenderer(1) as renderer:
        frame = renderer.frame(scene, 0, (160, 120))
        assert frame.getpixel((80, 60)) == (85, 0, 170, 192)
        assert frame.getpixel((20, 20))[3] == 0
    cover = gradient_surface(bounds, fill=paint("lime", "lime"), z_index=1)
    scene = Scene(Canvas(160, 120)).add(cover, outer).wait(1)
    with PillowRenderer(1) as renderer:
        assert renderer.frame(scene, 0, (160, 120)).getpixel((80, 60)) == (0, 255, 0, 255)


@pytest.mark.parametrize("frame_cache_mb", [0, 64])
@pytest.mark.parametrize("masked", [False, True])
def test_arbitrary_time_spring_seek_and_fps_workloads_never_rasterize_again(monkeypatch, frame_cache_mb, masked):
    card = card_surface(
        Bounds(20, 20, 220, 160),
        fill=LinearGradient(paint().stops, 125),
        radius=12,
        shadow=ShadowStyle(blur=3, offset=(0, 2)),
    )
    source = card.source_bytes
    group = Group(card, **({"mask": RectangleMask(190, 130), "scale_x": 1.05, "scale_y": 0.85} if masked else {}))
    scene = Scene(Canvas(260, 180, "#00000000")).add(group)
    scene.play(group.animate.move_to(135, 85).scale_to(0.95).rotate_to(7), run_time=2, rate_func=Spring(100, 10, 1))
    with scene.at(0):
        scene.play(group.animate.opacity_to(0.6), run_time=2, rate_func=smooth)
    scene.wait_until(2.2)

    def fail(*args, **kwargs):
        raise AssertionError("Surface generation occurred during frame replay")

    monkeypatch.setattr("faceless_champ._surface_raster._paint", fail)
    monkeypatch.setattr("faceless_champ._surface_raster.ImageFilter.GaussianBlur", fail)
    times = [0, 0.1, 0.37, 0.77, 1, 2]
    shuffled = times.copy()
    random.Random(2026).shuffle(shuffled)
    with PillowRenderer(1, frame_cache_mb=frame_cache_mb) as renderer:
        expected = {t: renderer.frame(scene, t, (130, 90)).tobytes() for t in times}
        for order in (times[::-1], shuffled, times * 2):
            for t in order:
                assert renderer.frame(scene, t, (130, 90)).tobytes() == expected[t]
        for fps in (24, 30, 60):
            for index in range(0, fps * 2, fps // 6):
                renderer.frame(scene, index / fps, (130, 90))
            for t in times:
                assert renderer.frame(scene, t, (130, 90)).tobytes() == expected[t]
        assert len(renderer._images) == len(renderer._sprites) == 1
    assert card.source_bytes == source and card.rotation == 0 and card.opacity == 1


def test_gradient_backdrop_does_not_freeze_gif_or_prepared_html_clocks(tmp_path):
    red, blue = PI.new("RGB", (20, 20), "red"), PI.new("RGB", (20, 20), "blue")
    buffer = BytesIO()
    red.save(buffer, format="GIF", save_all=True, append_images=[blue], duration=[100, 300], loop=0)
    red.save(tmp_path / "00000000.png")
    blue.save(tmp_path / "00000001.png")
    metadata = {"geometry": {}, "cursor": [0, 0], "clicks": []}
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {"schema": 1, "fps": 2, "duration": 1, "viewport": [20, 20], "frames": {"0": metadata, "1": metadata}}
        )
    )
    scene = Scene(Canvas(160, 120)).add(gradient_surface(Bounds(0, 0, 160, 120), fill=paint()))
    gif = Image.from_source(buffer.getvalue(), width=30, height=30, position=(40, 60))
    html = HtmlClip(WebCapture(tmp_path), width=30, height=30, position=(120, 60))
    with scene.at(0.25):
        scene.add(Group(gif, html))
    scene.wait_until(2)
    with PillowRenderer(1) as renderer:
        for t, gif_rgb, html_rgb in [
            (0.3, (255, 0, 0), (255, 0, 0)),
            (0.45, (0, 0, 255), (255, 0, 0)),
            (0.85, (0, 0, 255), (0, 0, 255)),
            (0.3, (255, 0, 0), (255, 0, 0)),
        ]:
            frame = renderer.frame(scene, t, (160, 120))
            assert frame.getpixel((40, 60))[:3] == gif_rgb
            assert frame.getpixel((120, 60))[:3] == html_rgb


def test_source_snapshot_invalidation_and_lifecycle_without_global_retention():
    references = []
    for _ in range(20):
        gradient = paint()
        image = gradient_surface(Bounds(0, 0, 32, 24), fill=gradient)
        scene = Scene(Canvas(32, 24)).add(image).wait(1)
        renderer = PillowRenderer(1)
        renderer.frame(scene, 0, (32, 24))
        renderer.close()
        assert not renderer._images and not renderer._sprites and not renderer._scene_frames
        references.extend(weakref.ref(v) for v in (gradient, image, scene, renderer))
        del gradient, image, scene, renderer
    gc.collect()
    assert all(ref() is None for ref in references)
    first = gradient_surface(Bounds(0, 0, 32, 24), fill=paint())
    second = gradient_surface(Bounds(0, 0, 32, 24), fill=paint("lime", "white"))
    assert first.source_bytes != second.source_bytes


def test_native_resources_close_when_construction_fails(monkeypatch):
    allocated = []
    original = PI.new

    def track(*args, **kwargs):
        image = original(*args, **kwargs)
        if inspect.currentframe().f_back.f_code.co_filename.endswith("_surface_raster.py"):
            allocated.append(image)
        return image

    def fail(*args, **kwargs):
        raise RuntimeError("injected paint failure")

    monkeypatch.setattr("faceless_champ._surface_raster.Image.new", track)
    monkeypatch.setattr("faceless_champ._surface_raster._paint", fail)
    with pytest.raises(RuntimeError, match="injected"):
        card_surface(Bounds(0, 0, 200, 140), fill=paint(), shadow=ShadowStyle(blur=3, offset=(0, 2)))
    assert allocated
    for image in allocated:
        with pytest.raises(ValueError, match="closed"):
            image.getbbox()


def test_small_face_huge_shadow_and_thin_raster_limits():
    with pytest.raises(ValueError, match="raster sample"):
        card_surface(Bounds(0, 0, 120.1, 140), fill=paint(), shadow=ShadowStyle())
    with pytest.raises(ValueError, match="budget"):
        card_surface(Bounds(0, 0, 200, 140), fill=paint(), shadow=ShadowStyle(blur=1e308))
    assert _allocation(1920, 1080) == (3840, 2160)
    for gradient in (LinearGradient(paint().stops, 125), RadialGradient(paint().stops, radius=1e-6)):
        with _paint(gradient, 0.5, 4, (1, 8)) as image:
            assert image.size == (1, 8)


def test_legacy_string_cards_retain_prechange_rgba_and_png():
    fixture = json.loads((Path(__file__).parent / "fixtures/premium-surfaces-legacy.json").read_text())
    for case in fixture["cases"]:
        shadow = ShadowStyle(**case["shadow"]) if case["shadow"] else None
        card = card_surface(Bounds(1.25, 2.5, 401.75, 302.75), fill=case["fill"], radius=29.5, shadow=shadow)
        with pixels(card) as source:
            assert sha256(source.tobytes()).hexdigest() == case["rgba"]
        if PIL.__version__ == fixture["pillow"]:
            assert sha256(card.source_bytes).hexdigest() == case["png"]


def test_fractional_coverage_replacement_uses_premultiplied_color():
    from faceless_champ._surface_raster import _coverage_replace

    source = PI.new("RGBA", (4, 1), (0, 0, 240, 64))
    face = PI.new("RGBA", (4, 1), (200, 100, 0, 128))
    coverage = PI.frombytes("L", (4, 1), bytes((0, 64, 128, 255)))
    _coverage_replace(source, face, (0, 0), coverage)
    assert list(rgba_pixels(source)) == [(0, 0, 240, 64), (80, 40, 144, 80), (134, 67, 80, 96), (200, 100, 0, 128)]
