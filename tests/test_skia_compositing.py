"""Blend modes, Trim Paths/dashes, path booleans, SVG, SkSL shaders, displacement, lighting,
morphology, Typst math."""

import pytest

from faceless_champ import (
    SVG,
    Canvas,
    Circle,
    DisplacementMap,
    Draw,
    EffectStack,
    Equation,
    Group,
    Lighting,
    Line,
    Morphology,
    PathData,
    PillowRenderer,
    Rectangle,
    Scene,
    ShaderEffect,
    ShaderFill,
    SkiaRenderer,
    Trace,
    VectorPath,
)

skia = pytest.importorskip("skia")

BACKENDS = [lambda: SkiaRenderer(1), lambda: PillowRenderer(1)]
IDS = ["skia", "pillow"]


def frame(make, scene, t=0, size=None):
    size = size or (scene.canvas.width, scene.canvas.height)
    with make() as renderer:
        renderer.validate(scene)
        return renderer.frame(scene, t, size)


def close(a, b, tol=6):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


# ----- blend modes ---------------------------------------------------------------


@pytest.mark.parametrize("make", BACKENDS, ids=IDS)
def test_multiply_and_screen_blend(make):
    s = Scene(Canvas(100, 50, bg="#FFFF00"))
    s.add(Rectangle(width=40, height=40, fill="#FF0000", stroke=None, position=(25, 25), blend="multiply"))
    s.add(Rectangle(width=40, height=40, fill="#0000FF", stroke=None, position=(75, 25), blend="screen"))
    s.wait(1)
    image = frame(make, s)
    assert close(image.getpixel((25, 25))[:3], (255, 0, 0))  # yellow x red
    assert close(image.getpixel((75, 25))[:3], (255, 255, 255))  # yellow screen blue
    assert close(image.getpixel((50, 5))[:3], (255, 255, 0))


@pytest.mark.parametrize("make", BACKENDS, ids=IDS)
def test_group_isolates_child_blends(make):
    """Children blend with their group only (pre-comp), not with the scene beneath."""
    s = Scene(Canvas(60, 60, bg="#0000FF"))
    s.add(
        Group(
            Rectangle(width=20, height=60, fill="#FFFF00", stroke=None, position=(10, 30)),
            Rectangle(width=60, height=20, fill="#FF0000", stroke=None, position=(30, 30), blend="multiply"),
        )
    )
    s.wait(1)
    image = frame(make, s)
    assert close(image.getpixel((10, 30))[:3], (255, 0, 0))  # yellow x red inside the group
    assert close(image.getpixel((45, 30))[:3], (255, 0, 0))  # over nothing in the group: plain red
    assert close(image.getpixel((45, 5))[:3], (0, 0, 255))


@pytest.mark.parametrize("make", BACKENDS, ids=IDS)
def test_stencil_acts_as_track_matte(make):
    s = Scene(Canvas(80, 80, bg="#000000"))
    s.add(
        Group(
            Rectangle(width=80, height=80, fill="#FF0000", stroke=None, position=(40, 40)),
            Circle(20, fill="#FFFFFF", stroke=None, position=(40, 40), blend="stencil"),
        )
    )
    s.wait(1)
    image = frame(make, s)
    assert close(image.getpixel((40, 40))[:3], (255, 0, 0))
    assert close(image.getpixel((5, 5))[:3], (0, 0, 0))


def test_blend_validation_and_moderngl_preflight():
    from faceless_champ._rendering.support import preflight, requirements

    with pytest.raises(ValueError, match="blend must be"):
        Rectangle(blend="burn-it")
    s = Scene(Canvas(10, 10)).add(Rectangle(width=4, height=4, blend="screen")).wait(1)
    assert "blend_modes" in requirements(s)
    with pytest.raises(ValueError, match="Blend modes"):
        preflight(s, "moderngl")
    preflight(s, "pillow")
    preflight(s, "skia")


# ----- trim paths and dashes -------------------------------------------------------


@pytest.mark.parametrize("make", BACKENDS, ids=IDS)
def test_trim_start_hides_the_beginning(make):
    s = Scene(Canvas(200, 40, bg="#000000"))
    s.add(Line(160, stroke="#FFFFFF", stroke_width=6, position=(100, 20), trim_start=0.5))
    s.wait(1)
    image = frame(make, s)
    assert image.getpixel((50, 20))[0] < 30
    assert image.getpixel((150, 20))[0] > 200


@pytest.mark.parametrize("make", BACKENDS, ids=IDS)
def test_trim_offset_and_animation(make):
    s = Scene(Canvas(200, 40, bg="#000000"))
    line = Line(160, stroke="#FFFFFF", stroke_width=6, position=(100, 20))
    s.add(line)
    s.play(Trace(line, length=0.25), run_time=1, rate_func="linear")
    early, late = frame(make, s, 0.01), frame(make, s, 0.99)
    assert early.getpixel((30, 20))[0] > 200 and early.getpixel((170, 20))[0] < 30
    assert late.getpixel((30, 20))[0] < 30 and late.getpixel((170, 20))[0] > 200


@pytest.mark.parametrize("make", BACKENDS, ids=IDS)
def test_dashes_alternate_and_slide(make):
    s = Scene(Canvas(220, 40, bg="#000000"))
    line = Line(200, stroke="#FFFFFF", stroke_width=6, position=(110, 20), dash=(20, 20))
    s.add(line)
    s.play(line.animate.dash_offset_to(20), run_time=1, rate_func="linear")
    a, b = frame(make, s, 0), frame(make, s, 1)
    # Dash 0 covers x 10..30, gap 30..50; sliding by one dash swaps them.
    assert a.getpixel((20, 20))[0] > 200 and a.getpixel((40, 20))[0] < 30
    assert b.getpixel((20, 20))[0] < 30 and b.getpixel((40, 20))[0] > 200


def test_trim_and_dash_validation():
    with pytest.raises(ValueError):
        Line(10, trim_start=2)
    with pytest.raises(ValueError):
        Line(10, dash=(5,))
    with pytest.raises(ValueError):
        Line(10).animate.trim_to(start=1.5)
    animation = Circle(10).animate.trim_to(start=0.1, end=0.9, offset=0.25)
    assert animation.targets == {"trim_start": 0.1, "draw": 0.9, "trim_offset": 0.25}


def test_partial_draw_spans_every_contour():
    """Regression: skia-python getSegment resets its destination path."""
    path = PathData.rect(0, 0, 40, 40).union(PathData.rect(100, 0, 40, 40))
    s = Scene(Canvas(160, 60, bg="#000000"))
    shape = VectorPath(path, fill=None, stroke="#FFFFFF", stroke_width=4, position=(80, 30))
    s.add(shape)
    s.play(shape.animate.trim_to(end=0.75), run_time=1, rate_func="linear")
    image = frame(BACKENDS[0], s, 1)
    assert image.getpixel((20, 10))[0] > 200  # first square's top edge
    assert image.getpixel((110, 10))[0] > 200  # second square's top edge is drawn too


# ----- paths -------------------------------------------------------------------------


def test_path_booleans():
    a, b = PathData.rect(0, 0, 100, 100), PathData.rect(50, 0, 100, 100)
    assert (a | b).bounds.width == pytest.approx(150, abs=0.01)
    assert (a & b).bounds.width == pytest.approx(50, abs=0.01)
    assert (a - b).bounds.right == pytest.approx(50, abs=0.01)
    ring = PathData.ellipse(0, 0, 50) - PathData.ellipse(0, 0, 25)
    assert sum(c[0] == "M" for c in ring.commands) == 2
    assert (a ^ b).bounds.width == pytest.approx(150, abs=0.01)


def test_svg_path_parser():
    p = PathData.from_svg(
        "M10 10 h 30 v 20 H 10 Z m 50 0 l 10 10 a 10 10 0 0 1 20 0 Q 90 0 100 10 T 120 10 C 130 0 140 0 150 10 S 170 20 180 10"
    )
    box = p.bounds
    assert box.left == 10 and box.right == pytest.approx(180)
    again = PathData.from_svg(p.to_svg())
    assert len(again.commands) == len(p.commands)
    with pytest.raises(ValueError):
        PathData.from_svg("M 10")


def test_shape_helpers_and_text_outlines():
    star = PathData.star(0, 0, 50, 20, points=5)
    assert len(star.commands) == 11
    assert PathData.rect(0, 0, 10, 10, radius=3).bounds.width == pytest.approx(10)
    text = PathData.from_text("Hi", font_size=80)
    assert text.bounds.height > 40 and text.bounds.bottom <= 1


# ----- SVG ---------------------------------------------------------------------------

TRIANGLE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 10"><path d="M0 10 L10 0 L20 10 Z" fill="#00FF00"/></svg>'
)
SPRITE = (
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="20" height="20">'
    '<defs><symbol id="sq"><rect width="10" height="10"/></symbol></defs>'
    '<use xlink:href="#sq" x="5" y="5" fill="#FF00FF"/></svg>'
)


@pytest.mark.parametrize("make", BACKENDS, ids=IDS)
def test_svg_component(make):
    icon = SVG(TRIANGLE, width=200, position=(100, 50))
    assert (icon.width, icon.height) == (200, 100)
    tinted = SVG(TRIANGLE, height=50, color="#FFFFFF", position=(250, 50))
    sprite = SVG(SPRITE, width=80, position=(350, 50))
    s = Scene(Canvas(400, 100, bg="#000000")).add(icon, tinted, sprite).wait(1)
    image = frame(make, s)
    assert close(image.getpixel((100, 80))[:3], (0, 255, 0))
    assert close(image.getpixel((250, 65))[:3], (255, 255, 255))
    assert close(image.getpixel((350, 50))[:3], (255, 0, 255))  # <use>/<symbol> expanded


# ----- SkSL ----------------------------------------------------------------------------

FILL = (
    "uniform half4 tint; uniform float iTime; half4 main(float2 xy) { return half4(tint.rgb * clamp(iTime, 0, 1), 1); }"
)
INVERT = "uniform shader content; half4 main(float2 xy) { half4 c = content.eval(xy); return half4(c.a - c.rgb, c.a); }"


@pytest.mark.parametrize("make", BACKENDS, ids=IDS)
def test_shader_fill_uniforms_and_time(make):
    s = Scene(Canvas(40, 40, bg="#000000"))
    s.add(ShaderFill(FILL, width=40, height=40, position=(20, 20), uniforms={"tint": "#FF8000"}))
    s.wait(2)
    assert close(frame(make, s, 0).getpixel((20, 20))[:3], (0, 0, 0))
    assert close(frame(make, s, 1.5).getpixel((20, 20))[:3], (255, 128, 0))


def test_shader_errors_are_reported_early():
    with pytest.raises(ValueError, match="does not compile"):
        ShaderFill("half4 main(float2 xy) { return nope; }")
    s = Scene(Canvas(10, 10)).add(ShaderFill(FILL, width=10, height=10)).wait(1)
    with SkiaRenderer(1) as r, pytest.raises(ValueError, match="tint"):
        r.validate(s)


@pytest.mark.parametrize("make", BACKENDS, ids=IDS)
def test_shader_effect_and_displacement(make):
    s = Scene(Canvas(80, 40, bg="#000000"))
    s.add(
        Rectangle(
            width=30,
            height=30,
            fill="#FF0000",
            stroke=None,
            position=(20, 20),
            effects=EffectStack(shader=ShaderEffect(INVERT)),
        )
    )
    s.add(
        Rectangle(
            width=30,
            height=30,
            fill="#FFFFFF",
            stroke=None,
            position=(60, 20),
            effects=EffectStack(displacement=DisplacementMap(amplitude=10, size=6, seed=3)),
        )
    )
    s.wait(1)
    image = frame(make, s)
    assert close(image.getpixel((20, 20))[:3], (0, 255, 255))
    # Displaced edges: some pixels just outside the original square become lit.
    lit = sum(image.getpixel((x, y))[0] > 128 for x in range(40, 80) for y in (2, 3, 37, 38))
    assert lit > 0


def test_effect_stack_static_fields():
    stack = EffectStack(shader=ShaderEffect(INVERT, mix=0.5), displacement=DisplacementMap(speed=4))
    assert "effect.shader.mix" in stack.state() and "effect.shader.sksl" not in stack.state()
    assert stack.time_dependent and stack.uses_skia
    assert stack.evaluated({"effect.shader.mix": 0.25}).shader.mix == 0.25
    assert stack.padding >= 12


@pytest.mark.parametrize("make", BACKENDS, ids=IDS)
def test_morphology_dilates_and_erodes(make):
    s = Scene(Canvas(80, 40, bg="#000000"))
    s.add(
        Rectangle(
            width=20,
            height=20,
            fill="#FFFFFF",
            stroke=None,
            position=(20, 20),
            effects=EffectStack(morphology=Morphology(radius=4)),
        )
    )
    s.add(
        Rectangle(
            width=20,
            height=20,
            fill="#FFFFFF",
            stroke=None,
            position=(60, 20),
            effects=EffectStack(morphology=Morphology(radius=4, mode="erode")),
        )
    )
    s.wait(1)
    image = frame(make, s)
    assert image.getpixel((8, 20))[0] > 200  # grown past the left edge (x=10)
    assert image.getpixel((52, 20))[0] < 50  # shrunk inside the left edge (x=50)
    assert image.getpixel((60, 20))[0] > 200


@pytest.mark.parametrize("make", BACKENDS, ids=IDS)
def test_lighting_bevels_toward_the_light(make):
    s = Scene(Canvas(80, 80, bg="#000000"))
    s.add(
        Rectangle(
            width=60,
            height=60,
            fill="#808080",
            stroke=None,
            position=(40, 40),
            effects=EffectStack(lighting=Lighting(azimuth=180, elevation=30, specular=0)),
        )
    )
    s.wait(1)
    image = frame(make, s)
    lit, shaded, flat = image.getpixel((12, 40)), image.getpixel((68, 40)), image.getpixel((40, 40))
    assert lit[0] > flat[0] + 10 and shaded[0] < flat[0] - 10  # light from the left
    assert close(flat[:3], (128, 128, 128), tol=12)  # flat areas keep their color
    assert image.getpixel((5, 5))[:3] == (0, 0, 0)  # nothing lit outside the shape


@pytest.mark.parametrize("light", ["point", "spot"])
def test_point_and_spot_lighting_render(light):
    s = Scene(Canvas(60, 60, bg="#000000"))
    s.add(
        Circle(
            25,
            fill="#4060C0",
            stroke=None,
            position=(30, 30),
            effects=EffectStack(lighting=Lighting(light=light, x=0.2, y=0.2, height=40)),
        )
    )
    s.wait(1)
    image = frame(lambda: SkiaRenderer(1), s)
    assert image.getpixel((30, 30))[3] == 255 and image.getpixel((2, 2))[:3] == (0, 0, 0)


def test_lighting_and_morphology_validation_and_animation():
    with pytest.raises(ValueError, match="mode"):
        Morphology(mode="open")
    with pytest.raises(ValueError, match="light"):
        Lighting(light="area")
    with pytest.raises(ValueError, match="elevation"):
        Lighting(elevation=120)
    stack = EffectStack(lighting=Lighting(), morphology=Morphology(radius=6))
    assert stack.uses_skia and not stack.time_dependent and stack.padding >= 6
    state = stack.state()
    assert "effect.lighting.azimuth" in state and "effect.lighting.light" not in state
    assert "effect.morphology.mode" not in state
    assert stack.evaluated({"effect.lighting.azimuth": 315}).lighting.azimuth == 315
    r = Rectangle(width=10, height=10, effects=stack)
    r.animate.effect_to("lighting", azimuth=-45, depth=-3)
    with pytest.raises(ValueError, match="exceeds"):
        r.animate.effect_to("lighting", elevation=95)


# ----- Typst math -------------------------------------------------------------------------


def _has_typst():
    try:
        from faceless_champ.typst_math import compiler

        compiler()
        return True
    except RuntimeError:
        return False


@pytest.mark.skipif(not _has_typst(), reason="Typst compiler not installed")
def test_typst_equation_renders_matrices(tmp_path, monkeypatch):
    monkeypatch.setenv("FC_CACHE_DIR", str(tmp_path))
    eq = Equation("A = mat(1, 2; 3, 4)", engine="typst", font_size=48, color="#FFFFFF", position=(200, 100))
    s = Scene(Canvas(400, 200, bg="#000000")).add(eq).wait(1)
    for make in BACKENDS:
        image = frame(make, s)
        box = image.convert("L").point(lambda v: 255 if v > 128 else 0).getbbox()
        assert box is not None and box[3] - box[1] > 60  # two matrix rows tall
    assert list(tmp_path.glob("typst/*.svg"))  # disk cache populated
    with pytest.raises(ValueError, match="Invalid Typst equation"):
        frame(BACKENDS[0], Scene(Canvas(50, 50)).add(Equation("mat(1, 2", engine="typst")).wait(1))


def test_typst_engine_validation():
    with pytest.raises(ValueError, match="engine"):
        Equation("x", engine="katex")
    with pytest.raises(ValueError, match="color_map"):
        Equation("x", engine="typst", color_map={"x": "red"})


@pytest.mark.parametrize("make", BACKENDS, ids=IDS)
def test_draw_still_reveals_shapes(make):
    """The plain Draw contract is unchanged when no trim/dash is used."""
    s = Scene(Canvas(200, 40, bg="#000000"))
    line = Line(160, stroke="#FFFFFF", stroke_width=6, position=(100, 20))
    s.add(line)
    s.play(Draw(line), run_time=1, rate_func="linear")
    half = frame(make, s, 0.5)
    assert half.getpixel((40, 20))[0] > 200 and half.getpixel((160, 20))[0] < 30


# ----- path effects, perspective, per-symbol Typst ------------------------------------------


def test_path_effects_render_on_skia_and_are_rejected_on_pillow():
    from faceless_champ._rendering.support import preflight

    plain = Rectangle(width=80, height=80, fill="#FFFFFF", stroke=None, position=(50, 50))
    rounded = Rectangle(width=80, height=80, fill="#FFFFFF", stroke=None, position=(150, 50), round_corners=30)
    s = Scene(Canvas(200, 100, bg="#000000")).add(plain, rounded).wait(1)
    image = frame(BACKENDS[0], s)
    assert image.getpixel((12, 12))[0] > 200  # sharp corner
    assert image.getpixel((112, 12))[0] < 60  # rounded away
    with pytest.raises(ValueError, match="round_corners"):
        preflight(s, "pillow")
    with pytest.raises(ValueError):
        Rectangle(jitter=(4,))


def test_perspective_tilt_projects_and_animates():
    card = Rectangle(width=200, height=100, fill="#FFFFFF", stroke=None, position=(150, 75), tilt_y=60)
    assert card.perspective == 1400 and card.state()["tilt_y"] == 60
    s = Scene(Canvas(300, 150, bg="#000000")).add(card)
    s.play(card.animate.tilt_to(y=0), run_time=1)
    for make in BACKENDS:  # native Skia matrix and the CPU compositor warp agree
        tilted, flat = frame(make, s, 0), frame(make, s, 1)
        assert tilted.getpixel((60, 75))[0] < 30  # foreshortened: the left edge moved in
        assert tilted.getpixel((150, 75))[0] > 200
        assert flat.getpixel((60, 75))[0] > 200
    with pytest.raises(ValueError):
        Rectangle(tilt_x=95)
    with pytest.raises(ValueError):
        Rectangle().animate.tilt_to(x=10)  # no perspective configured


@pytest.mark.skipif(not _has_typst(), reason="Typst compiler not installed")
def test_math_glyphs_are_individual_vector_paths():
    from faceless_champ import MathGlyphs

    eq = MathGlyphs("x^2 + y^2 = r^2", font_size=60, position=(200, 60), outline=True)
    assert len(eq.glyphs) >= 8
    assert all(isinstance(g, VectorPath) for g in eq.glyphs)
    assert eq.bounds.center == pytest.approx((200, 60), abs=1)
    lefts = [g.bounds.left for g in eq.glyphs]
    assert lefts == sorted(lefts)  # left to right
    s = Scene(Canvas(400, 120, bg="#000000")).add(eq)
    s.play(*[Draw(g) for g in eq.glyphs], run_time=1)
    assert frame(BACKENDS[0], s, 1).convert("L").getbbox() is not None


def test_shader_fill_low_resolution_matches_full():
    full = ShaderFill(FILL, width=40, height=40, position=(20, 20), uniforms={"tint": "#FF8000"})
    low = ShaderFill(FILL, width=40, height=40, position=(20, 20), uniforms={"tint": "#FF8000"}, resolution=0.25)
    a = full.render_raster(full.state(), 1, 2.0, None)
    b = low.render_raster(low.state(), 1, 2.0, None)
    assert a.size == b.size == (40, 40)
    assert close(a.getpixel((20, 20)), b.getpixel((20, 20)))
    with pytest.raises(ValueError):
        ShaderFill(FILL, resolution=2)
