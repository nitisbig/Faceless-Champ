"""Backend contracts and the portable/native vector boundary."""

import subprocess
import sys

import pytest
from PIL import Image as PI

from faceless_champ import (
    Bounds,
    Canvas,
    CircleMask,
    Draw,
    ExportSettings,
    GradientStop,
    Group,
    Layer,
    LinearGradient,
    Number,
    PathData,
    PathMask,
    PillowRenderer,
    Rectangle,
    Scene,
    Sequence,
    ShadowStyle,
    SkiaRenderer,
    Surface,
    VectorPath,
    card_surface,
    fit_text,
    gradient_surface,
    linear,
    render,
    save_frame,
)


@pytest.fixture
def native():
    pytest.importorskip("skia")
    with SkiaRenderer(1) as renderer:
        yield renderer


def test_optional_backend_is_lazy_and_explicit_failure():
    code = """
import builtins, sys
original = builtins.__import__
def blocked(name, *args, **kwargs):
    if name == 'skia':
        raise ImportError('intentionally absent')
    return original(name, *args, **kwargs)
builtins.__import__ = blocked
from faceless_champ import Canvas, Scene, Rectangle, create_renderer
assert 'skia' not in sys.modules
s = Scene(Canvas(10,10)).add(Rectangle(width=4,height=4,fill='red',stroke=None,position=(5,5))).wait(1)
with create_renderer() as r:
    assert r.frame(s,0,(10,10)).getpixel((5,5))[0] > 240
try:
    create_renderer('skia')
except RuntimeError as e:
    assert 'faceless-champ[skia]' in str(e)
else:
    raise AssertionError('Skia must not fall back silently')
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    with pytest.raises(ValueError, match="backend"):
        ExportSettings(backend="unknown").dimensions(Canvas())


def test_native_alpha_group_masks_and_member_opacity(native):
    a = Rectangle(width=70, height=70, fill="red", stroke=None, position=(50, 50))
    b = Rectangle(width=70, height=70, fill="blue", stroke=None, position=(50, 50))
    node = Scene(Canvas(100, 100, "#00000000")).add(Group(a, b, opacity=0.5, mask=CircleMask(30))).wait(1)
    frame = native.frame(node, 0.5, (100, 100))
    assert frame.getpixel((50, 50))[3] == 192
    assert frame.getpixel((10, 10)) == (0, 0, 0, 0)
    node = Scene(Canvas(100, 100, "#00000000")).add(a).wait(1)
    node.play(a.animate.opacity_to(0.5), run_time=1, rate_func=linear)
    assert native.frame(node, 2, (100, 100)).getpixel((50, 50)) == (255, 0, 0, 128)


def test_cache_random_seek_and_frame_copy(native):
    c = Rectangle(width=20, height=15, fill="red", position=(30, 25))
    scene = Scene(Canvas(100, 60)).add(Group(c, scale_x=1.2, rotation=14)).wait(0.2)
    scene.play(c.animate.move_to(60, 30).fill_to("blue"), run_time=1, rate_func=linear)
    first = native.frame(scene, 0.4, (100, 60)).tobytes()
    for t in (0.8, 0.1, 1.1, 0.4):
        native.frame(scene, t, (100, 60))
    assert native.frame(scene, 0.4, (100, 60)).tobytes() == first
    edited = native.frame(scene, 0.4, (100, 60))
    edited.paste("white", (0, 0, 100, 60))
    assert native.frame(scene, 0.4, (100, 60)).tobytes() == first
    native.close()
    assert native.images.bytes == native.frames.bytes == native.working_bytes == 0


def test_capped_arch_viewport_preserves_following_native_overlay(native):
    import math

    import numpy as np
    import pyvista as pv
    from facelesschamp_kit.engineering.clip import ArchChamp
    from facelesschamp_kit.engineering.script import ArchScript

    from faceless_champ import Circle, Text
    from faceless_champ.integrations.pyvista.camera import ArchCamera
    from faceless_champ.integrations.pyvista.model import ArchMesh

    # A closed tube cut on y=0 exercises VTK's capped clipping and its tiny
    # trigonometric coordinates. Its raster must not affect later native ink.
    count = 72
    points = [
        (x, r * math.cos(a), r * math.sin(a))
        for x, r in ((-48, 12), (-48, 26), (48, 26), (48, 12))
        for a in np.linspace(0, math.tau, count, endpoint=False)
    ]
    faces = [
        v
        for j in range(4)
        for k in range(count)
        for v in (
            4,
            j * count + k,
            j * count + (k + 1) % count,
            ((j + 1) % 4) * count + (k + 1) % count,
            ((j + 1) % 4) * count + k,
        )
    ]
    mesh = pv.PolyData(points, faces).triangulate().compute_normals(auto_orient_normals=True)
    view = ArchChamp(
        ArchMesh.from_data(mesh),
        ArchScript().section("model", (0, 0, 0), normal=(0, -1, 0), cap=True),
        camera=ArchCamera(position=(210, -310, 205)),
        width=140,
        height=140,
        position=(70, 80),
    )
    circle = Circle(34, position=(245, 64), fill=None, stroke="#75D9ED", stroke_width=2)
    label = Text("Ø24", position=(245, 120), font_size=20, color="#75D9ED", text_engine="skia")
    canvas = Canvas(320, 160, "#000000")
    actual = native.frame(Scene(canvas).add(view, circle, label).wait(2), 1, (320, 160))
    # Check the first draw: pre-rendering the overlay can hide the host defect
    # by warming Skia's native path/text machinery before VTK runs.
    circle_ink = np.asarray(actual.crop((200, 20, 290, 108)))
    label_ink = np.asarray(actual.crop((210, 108, 280, 140)))
    assert np.count_nonzero((circle_ink[:, :, 1] > 140) & (circle_ink[:, :, 2] > 140)) > 250
    assert np.count_nonzero((label_ink[:, :, 1] > 140) & (label_ink[:, :, 2] > 140)) > 50


@pytest.mark.parametrize("fail", [False, True])
def test_arch_float_environment_restores_after_raster(native, monkeypatch, fail):
    import ctypes
    import platform

    from facelesschamp_kit.engineering.clip import ArchChamp

    from faceless_champ.integrations.pyvista._environment import _fenv_api
    from faceless_champ.integrations.pyvista.model import ArchMesh

    if sys.platform != "linux" or platform.machine() != "x86_64" or _fenv_api() is None:
        pytest.skip("C99 x86 floating-point rounding constants required")
    process = ctypes.CDLL(None)
    original = process.fegetround()
    downward = 0x400

    def sprite(*args):
        assert process.fesetround(downward) == 0
        if fail:
            raise RuntimeError("raster failure")
        return PI.new("RGBA", (round(view.width), round(view.height)))

    view = ArchChamp(ArchMesh.from_arrays([(-1, 0, 0), (1, 0, 0), (0, 1, 0)], faces=[[0, 1, 2]]))
    from faceless_champ.integrations.pyvista import rendering

    class Session:
        def __init__(self, *args):
            pass

        def frame(self, age):
            return sprite(age)

        def close(self):
            pass

    monkeypatch.setattr(rendering, "ArchSession", Session)
    try:
        if fail:
            with pytest.raises(RuntimeError, match="raster failure"):
                native.raster.sprite(view, view.state(), 1, 0)
        else:
            assert native.raster.sprite(view, view.state(), 1, 0).size == (round(view.width), round(view.height))
        assert process.fegetround() == original
    finally:
        process.fesetround(original)


def test_native_style_tracks_can_start_transparent_and_gif_uses_introduction_clock(native):
    from io import BytesIO

    from faceless_champ import Image

    shape = Rectangle(width=30, height=30, fill=None, stroke=None, position=(30, 30))
    scene = Scene(Canvas(60, 60, "#00000000")).add(shape)
    scene.play(shape.animate.fill_to("red").stroke_to("blue"), run_time=1, rate_func=linear)
    assert native.frame(scene, 0, (60, 60)).getbbox() is None
    assert native.frame(scene, 1, (60, 60)).getpixel((30, 30)) == (255, 0, 0, 255)
    buf = BytesIO()
    PI.new("RGB", (8, 8), "red").save(
        buf, format="GIF", save_all=True, append_images=[PI.new("RGB", (8, 8), "blue")], duration=[100, 100], loop=0
    )
    clip = Image.from_source(buf.getvalue(), width=20, height=20, position=(30, 30))
    scene = Scene(Canvas(60, 60)).wait(2).add(Group(clip, mask=CircleMask(20))).wait(1)
    for t, expected in ((2.05, (255, 0, 0)), (2.15, (0, 0, 255)), (2.05, (255, 0, 0))):
        assert native.frame(scene, t, (60, 60)).getpixel((30, 30))[:3] == expected


def test_composition_crossfade_and_layer_keep_legacy_rules(native):
    def solid(color):
        return Scene(Canvas(40, 40, color)).wait(2)

    nodes = [Sequence(solid("red"), solid("blue"), crossfade=1), Layer(solid("red"), solid("#0000FF80"))]
    with PillowRenderer(1) as pillow:
        for node in nodes:
            assert native.frame(node, 1.5, (40, 40)).tobytes() == pillow.frame(node, 1.5, (40, 40)).tobytes()


def test_curve_extrema_immutable_commands_and_portable_draw(native):
    path = PathData().move_to(0, 0).quad_to(50, 100, 100, 0)
    assert path.bounds == Bounds(0, 0, 100, 50)
    assert path.commands[0] == ("M", 0, 0)
    shape = VectorPath(path, stroke="red", stroke_width=3, position=(70, 40))
    scene = Scene(Canvas(140, 90, "#00000000"))
    scene.play(Draw(shape), run_time=1, rate_func=linear)
    with PillowRenderer(1) as pillow:
        for renderer in (native, pillow):
            assert renderer.frame(scene, 0, (140, 90)).getbbox() is None
            assert renderer.frame(scene, 0.5, (140, 90)).getbbox() is not None
            assert renderer.frame(scene, 1, (140, 90)).getbbox()[2] > 110
    with pytest.raises(ValueError, match="start"):
        PathData((("L", 1, 2),))


def test_compound_paths_path_masks_and_early_capability_errors(native):
    path = PathData().move_to(0, 0).line_to(1, 0).quad_to(0.5, 1, 0, 0).close()
    c = Rectangle(width=60, height=60, fill="red", position=(40, 40), mask=PathMask(path, width=60, height=60))
    scene = Scene(Canvas(80, 80, "#00000000")).add(c).wait(1)
    native.validate(scene)
    assert native.frame(scene, 0.5, (80, 80)).getpixel((40, 18))[3] == 255
    with PillowRenderer(1) as pillow, pytest.raises(ValueError, match="PathMask"):
        pillow.validate(scene)
    compound = path.transformed(sx=30, sy=30)
    shape = VectorPath(PathData(compound.commands + compound.transformed(dx=50).commands), fill_rule="even_odd")
    assert Group(shape).bounds.width > 60
    with PillowRenderer(1) as pillow, pytest.raises(ValueError, match="Compound"):
        pillow.validate(Scene().add(shape).wait(1))


def test_retained_surfaces_gradient_alpha_and_shadow(native):
    gradient = LinearGradient((GradientStop(0, "#FF0000FF"), GradientStop(1, "#0000FF00")))
    surface = gradient_surface(Bounds(0, 0, 100, 60), fill=gradient, render_mode="vector")
    assert isinstance(surface, Surface)
    for renderer in (native, PillowRenderer(1)):
        frame = renderer.frame(Scene(Canvas(100, 60, "#00000000")).add(surface).wait(1), 0, (100, 60))
        r, g, b, a = frame.getpixel((50, 30))
        assert r == 255 and g == b == 0 and 120 <= a <= 135
    card = card_surface(
        Bounds(0, 0, 160, 120),
        fill="#00000000",
        radius=12,
        shadow=ShadowStyle("#FF000080", 4, (0, 3)),
        render_mode="vector",
    )
    frame = native.frame(Scene(Canvas(160, 120, "#00000000")).add(card).wait(1), 0, (160, 120))
    assert frame.getpixel((80, 60)) == (0, 0, 0, 0)
    assert any(r > 240 and 0 < a < 128 for r, g, b, a in frame.getdata())


def test_native_text_metrics_fit_variable_font_and_number(native):
    from faceless_champ import CLEAN_FLOW_FONT

    text = fit_text(
        "AV office\nMeasured type",
        Bounds(10, 10, 180, 110),
        font=CLEAN_FLOW_FONT,
        font_weight=700,
        font_size=30,
        min_font_size=16,
        text_engine="skia",
    )
    assert text.bounds.width <= 170 and text.bounds.height <= 100
    scene = Scene(Canvas(200, 140)).add(text).wait(1)
    native.validate(scene)
    assert native.frame(scene, 0, (200, 140)).getbbox()
    with PillowRenderer(1) as pillow, pytest.raises(ValueError, match="typography"):
        pillow.validate(scene)
    number = Number(12, width=90, font_size=20, text_engine="skia", position=(70, 40))
    scene = Scene(Canvas(140, 80)).add(number)
    scene.play(number.animate.value_to(98), run_time=1, rate_func=linear)
    assert scene.bounds_at(number, 0.2).width == scene.bounds_at(number, 0.8).width
    native.frame(scene, 0.5, (140, 80))


def test_leaf_shadow_ink_bounds_and_budget(native):
    c = Rectangle(
        width=30, height=20, fill="white", stroke=None, position=(50, 50), shadow=ShadowStyle("#FF000080", 4, (0, 8))
    )
    scene = Scene(Canvas(100, 100, "#00000000")).add(Group(c, rotation=20)).wait(1)
    assert scene.ink_bounds_at(c, 0).height > scene.bounds_at(c, 0).height
    assert native.frame(scene, 0, (100, 100)).getchannel("A").getbbox()
    with SkiaRenderer(1, working_mb=1) as small, pytest.raises(ValueError, match="working_mb"):
        small.frame(Scene(Canvas(1024, 1024)).wait(1), 0, (1024, 1024))
    assert small.working_bytes == 0


def test_mask_allocations_follow_small_local_coverage_and_nested_transforms():
    shape = Rectangle(width=1200, height=1200, fill="red", stroke=None, position=(80, 80), mask=CircleMask(15))
    root = Group(Group(shape, scale_x=1.3, rotation=10), mask=CircleMask(25), opacity=0.5)
    scene = Scene(Canvas(160, 160, "#00000000")).add(root).wait(1)
    # A full-canvas-per-leaf allocation at authored size would exceed this budget.
    with SkiaRenderer(1, working_mb=1) as renderer:
        frame = renderer.frame(scene, 0, (160, 160))
        assert frame.getpixel((80, 80)) == (255, 0, 0, 128)
        assert frame.getpixel((120, 120)) == (0, 0, 0, 0)
        assert renderer.working_bytes == 0


@pytest.mark.parametrize("feature", ["effects", "procedural", "transition"])
def test_delegated_composition_preserves_working_budget(native, feature):
    from faceless_champ import DirectionalWipe, EffectStack, ProceduralBackground

    def scene(size):
        w, h = size
        if feature == "procedural":
            component = ProceduralBackground(width=w, height=h, position=(w / 2, h / 2))
        else:
            component = Rectangle(
                width=20,
                height=20,
                position=(w / 2, h / 2),
                effects=EffectStack() if feature == "effects" else None,
            )
        node = Scene(Canvas(w, h)).add(component).wait(1)
        if feature == "transition":
            node = Sequence(node, Scene(Canvas(w, h)).wait(1), crossfade=0.5, transition=DirectionalWipe())
        return node

    with SkiaRenderer(1, working_mb=1) as renderer:
        for node in (Scene(Canvas(800, 600)).wait(1), scene((800, 600))):
            with pytest.raises(ValueError, match="working_mb"):
                renderer.frame(node, 0.75, (800, 600))
        assert renderer.working_bytes == 0
        # Reuse after failure still renders frames that fit the configured limit.
        assert renderer.frame(scene((80, 60)), 0.75, (80, 60)).size == (80, 60)
        assert renderer._effect_compositor.device.bytes == 0


def test_specialist_viewports_reuse_resolution_through_animated_scale(native, monkeypatch):
    from faceless_champ import Component

    class PreparedViewport(Component):
        width = height = 20

        def frame_key(self, age):
            return 0

    viewport = PreparedViewport(position=(50, 50))
    scene = Scene(Canvas(100, 100)).add(viewport)
    scene.play(viewport.animate.scale_to(1.4), run_time=1, rate_func=linear)
    factors = []

    def sprite(component, state, factor, age):
        factors.append(factor)
        return PI.new("RGBA", (round(20 * factor), round(20 * factor)), "red")

    monkeypatch.setattr(native.raster, "sprite", sprite)
    for t in (0.1, 0.5, 0.9):
        native.frame(scene, t, (100, 100))
    assert factors == [1]


def test_export_settings_and_preview_backend_cleanup(tmp_path, native, monkeypatch):
    closed = []
    original = SkiaRenderer.close
    monkeypatch.setattr(SkiaRenderer, "close", lambda r: (closed.append(r), original(r))[-1])
    scene = Scene(Canvas(80, 60, "white")).wait(0.2)
    save_frame(scene, 0, tmp_path / "frame.png", size=(80, 60), backend="skia")
    assert len(closed) == 1
    render(scene, tmp_path / "sample.mp4", backend="skia", antialias=1, width=80, height=60, fps=5)
    assert len(closed) == 2
    save_frame(scene, 0, tmp_path / "caller.png", size=(80, 60), renderer=native)
    assert len(closed) == 2
    assert PI.open(tmp_path / "frame.png").size == (80, 60)
