"""faceless_champ.draw: immediate-mode Skia frames, theme palettes, timing and the 3D/math helpers."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

from faceless_champ import Theme
from faceless_champ.draw import CueClock, Palette, chroma_kick, default_palette, env, lin, pulse, set_default_palette

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _reset_palette():
    yield
    set_default_palette(None)


def _has_typst():
    try:
        from faceless_champ.typst_math import compiler

        compiler()
        return True
    except RuntimeError:
        return False


# ----- timing ------------------------------------------------------------------------------


def test_envelopes():
    assert lin(0.5, 1.0, 2.0) == 0.0 and lin(1.5, 1.0, 2.0) == 0.5 and lin(3.0, 1.0, 2.0) == 1.0
    assert lin(1.0, 2.0, 2.0) == 0.0 and lin(2.0, 2.0, 2.0) == 1.0
    assert env(0.9, 1.0, 3.0) == 0.0 and env(2.0, 1.0, 3.0) == 1.0 and env(3.1, 1.0, 3.0) == 0.0
    assert pulse(1.25, 1.0, 0.5) == pytest.approx(1.0) and pulse(0.9, 1.0) == 0.0
    assert chroma_kick(1.0, 1.0, 6.0) == pytest.approx(6.0) and chroma_kick(2.0, 1.0) == 0.0


def test_cue_clock(tmp_path):
    srt = tmp_path / "cues.srt"
    srt.write_text(
        "1\n00:00:01,000 --> 00:00:01,400\nSo\n\n2\n00:00:01,400 --> 00:00:02,000\nwhy?\n\n"
        "3\n00:00:02,500 --> 00:00:03,000\nso\n"
    )
    clock = CueClock(srt, lead=0.2)
    assert clock.cue(2) == pytest.approx(1.4)
    assert clock.beat(2) == pytest.approx(1.2) and clock.beat(1, lead=5.0) == 0.0
    assert clock.word("Why") == pytest.approx(1.4)
    assert clock.word("so", after=1.5) == pytest.approx(2.5)
    with pytest.raises(KeyError, match="nope"):
        clock.word("nope")


# ----- palette -----------------------------------------------------------------------------


def test_palette_from_theme_roles_aliases_and_overrides():
    theme = Theme.named("paper")
    p = Palette.from_theme(theme, ball="#5FB6FF", ink="#111111")
    assert p.hex("background") == p.hex("bg") == theme.colors.background
    assert p.hex("line") == theme.colors.border and p.hex("primary") == theme.colors.primary
    assert p.hex("glass") == theme.colors.surface and p.hex("floor") == theme.colors.axis
    assert p.hex("ball") == "#5FB6FF" and p.hex("ink") == "#111111"
    assert p.hex("#abcdef") == "#abcdef"
    assert p.mix("#000000", "#ffffff", 0.5) == "#808080" and p.mix("#000000", "#ffffff", 7) == "#ffffff"
    with pytest.raises(KeyError, match="unknown color token 'nope'"):
        p.hex("nope")
    with pytest.raises(ValueError, match="hex"):
        Palette({"bad": "red"})
    assert p == Palette.from_theme(theme, ink="#111111", ball="#5FB6FF") and hash(p) == hash(p.with_tokens())
    assert p.with_tokens(ball="#000000").hex("ball") == "#000000" and p.hex("ball") == "#5FB6FF"


def test_default_palette_follows_theme_until_set():
    with Theme.named("ocean").use():
        assert default_palette().hex("bg") == Theme.named("ocean").colors.background
    custom = Palette.from_theme(Theme.named("midnight"), bg="#010203")
    set_default_palette(custom)
    assert default_palette() is custom
    with pytest.raises(TypeError):
        set_default_palette({"bg": "#000000"})


def test_timing_and_palette_import_without_skia():
    code = (
        "import sys; sys.modules['skia'] = None\n"
        "from faceless_champ.draw import lin, Palette, CueClock\n"
        "assert Palette.from_theme().hex('ink')\n"
        "try:\n    from faceless_champ.draw import Frame\nexcept ImportError:\n    pass\n"
        "else:\n    raise SystemExit('Frame imported without skia')\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


# ----- frame -------------------------------------------------------------------------------


def _palette():
    return Palette.from_theme(Theme.named("midnight"), bg="#000000", ball="#ffffff")


def test_frame_scales_design_pixels_to_output():
    pytest.importorskip("skia")
    from faceless_champ.draw import Frame

    fr = Frame((480, 270), palette=_palette())
    fr.circle(1440, 270, 60, "ball", fill=True)  # design (1440, 270) -> output (360, 67.5)
    out = fr.finish()
    assert out.shape == (270, 480, 4) and out.dtype.name == "uint8"
    assert (out[..., 3] == 255).all()
    assert out[67, 360, :3].min() > 240 and out[67, 120, :3].max() == 0


def test_glow_blooms_beyond_the_crisp_shape():
    pytest.importorskip("skia")
    from faceless_champ.draw import Frame

    def ring(glow):
        fr = Frame((480, 270), palette=_palette())
        fr.circle(960, 540, 200, "ball", 4.0, glow=glow)
        return fr.finish()

    plain, glowing = ring(0.0), ring(1.0)
    # Just outside the ring (radius 50 output px), only the glow lights pixels.
    assert plain[135, 240 + 56, :3].max() == 0 and glowing[135, 240 + 56, :3].max() > 10


def test_frame_finish_effects_and_glow_styles():
    pytest.importorskip("skia")
    from faceless_champ.draw import Frame, GlowStyle

    fr = Frame((320, 180), palette=_palette(), glow="soft")
    assert fr.gw == 80
    fr.rrect(400, 300, 1120, 480, 40, fill="ball")
    fr.letterbox(1.0)
    fr.chroma(6.0)
    fr.zoom_blur(0.2)
    out = fr.finish()
    assert out[2, 160, :3].max() == 0  # letterbox bar
    assert out[90, 160, :3].min() > 200
    with pytest.raises(ValueError, match="glow style"):
        GlowStyle.named("huge")


def test_motion_blur_averages_subframes(monkeypatch):
    np = pytest.importorskip("numpy")
    from faceless_champ.draw import motion_blur

    def draw(t, size):
        return np.full((2, 2, 4), 200 if t >= 1.0 else 0, np.uint8)

    monkeypatch.setenv("FC_MOTION_BLUR", "1")
    assert motion_blur(draw, 1.0, (2, 2))[0, 0, 0] == 200
    blurred = motion_blur(draw, 1.0, (2, 2), samples=4, shutter=0.3)
    assert blurred[0, 0, 0] == 50  # only the last of four subframes has reached t = 1.0


def test_offscreen_pen_draws_cards():
    pytest.importorskip("skia")
    from faceless_champ.draw import offscreen

    surf, pen = offscreen(100, 50, 2.0, palette=_palette())
    pen.rrect(0, 0, 100, 50, 8, fill="ball", glow=1.0)  # glow is ignored offscreen
    img = surf.makeImageSnapshot()
    assert (img.width(), img.height()) == (200, 100)


def test_space_camera_projects_and_draws_boxes():
    pytest.importorskip("skia")
    from faceless_champ.draw import Frame, hud
    from faceless_champ.draw.space import Camera, draw_box, orbit_path

    cam = Camera((0, 0, -10), (0, 0, 0), focal=1000)
    xs, ys, z = cam.project([(0, 0, 0), (1, 1, 0)])
    assert (xs[0], ys[0], z[0]) == (960, 540, 10) and xs[1] == pytest.approx(1060) and ys[1] == pytest.approx(440)
    path = orbit_path([(0, (0, 0, 0), 10, 0.0, 0.0), (2, (0, 0, 0), 10, 0.0, 1.0)])
    assert path(-1).eye == pytest.approx(path(0).eye) and path(1).eye[0] > 0
    fr = Frame((480, 270), palette=_palette())
    draw_box(fr, cam, (0, 0, 0), (1, 1, 1), "ball", "ink")
    hud.dot_grid(fr, cam, height=-1.0)
    hud.axis3d(fr, cam, (0, 0, 0), (2, 0, 0), "x", "primary")
    assert fr.finish()[135, 240, :3].max() > 0


def test_draw_scene_renders_through_the_normal_pipeline(tmp_path):
    pytest.importorskip("skia")
    from PIL import Image

    from faceless_champ import save_frame
    from faceless_champ.draw import Frame, draw_scene

    def draw(t, size):
        fr = Frame(size, palette=_palette())
        fr.circle(960, 540, 300 * t, "ball", fill=True)
        return fr.finish()

    scene = draw_scene(draw, 2.0, theme=Theme.named("midnight"))
    assert scene.duration == pytest.approx(2.0)
    out = tmp_path / "f.png"
    save_frame(scene, 1.0, out, size=(320, 180), backend="skia")
    assert Image.open(out).convert("RGB").getpixel((160, 90))[0] > 240


@pytest.mark.skipif(not _has_typst(), reason="Typst compiler not installed")
def test_mathtype_draws_morphs_and_numbers():
    pytest.importorskip("skia")
    from faceless_champ.draw import Frame, hud, mathtype

    p = _palette()
    assert mathtype.tc("ball", "x", p) == '#text(fill: rgb("#ffffff"))[$x$]'
    w, h = mathtype.size_of("e^(-x^2)", 96)
    assert w > h > 0

    def frame(fn):
        fr = Frame((480, 270), palette=p)
        fn(fr)
        return fr.finish()

    a = frame(lambda fr: mathtype.draw(fr, "sqrt(4)", 960, 540, 120))
    assert (frame(lambda fr: mathtype.morph(fr, "sqrt(4)", "2", 0.0, 960, 540, 120)) == a).all()
    assert not (frame(lambda fr: mathtype.morph(fr, "sqrt(4)", "2", 0.5, 960, 540, 120)) == a).all()
    assert frame(lambda fr: mathtype.number(fr, "-3.14", 960, 540, 120))[..., :3].max() > 200
    assert frame(lambda fr: hud.readout(fr, 960, 540, "σ", "1.25"))[..., :3].max() > 200


def test_mesh3d_render_is_camera_matched():
    pytest.importorskip("skia")
    pv = pytest.importorskip("pyvista")
    np = pytest.importorskip("numpy")
    from faceless_champ.draw import mesh3d
    from faceless_champ.draw.space import orbit

    cam = orbit((0, 0, 0), 8.0, 0.3, 0.6, focal=1000.0, center=(1200.0, 500.0))
    centre = np.array([0.6, 0.2, -0.4])
    style = mesh3d.gloss("#ffffff", _palette(), ambient=1.0)
    rgba = mesh3d.render([(pv.Sphere(radius=0.3, center=centre), style)], cam, (480, 270), cache=None)
    ys, xs = np.nonzero(rgba[..., 3] > 128)
    px, py, _ = cam.project(centre)
    assert xs.mean() * 4 == pytest.approx(px[0], abs=8) and ys.mean() * 4 == pytest.approx(py[0], abs=8)


def test_draw_guide_example_runs():
    pytest.importorskip("skia")
    from faceless_champ import PillowRenderer

    code = re.search(r"```python\n(.*?)```", (ROOT / "docs" / "draw.md").read_text(), re.DOTALL).group(1)
    namespace = {"__name__": "draw_guide"}
    exec(compile(code, "docs/draw.md", "exec"), namespace)  # noqa: S102 - tested docs
    scene = namespace["scene"]
    with PillowRenderer(1) as renderer:
        renderer.validate(scene)
        renderer.frame(scene, 1.5, (320, 180))
