"""Real EGL contract checks, with explicit skips on hosts without optional GL."""

import subprocess
import sys

import pytest
from PIL import Image as PI

from faceless_champ import (
    Bloom,
    Canvas,
    ChromaticAberration,
    CircleMask,
    DirectionalWipe,
    Distortion,
    EffectStack,
    GaussianBlur,
    GPUOptions,
    Grid,
    Group,
    Image,
    Layer,
    LightSweep,
    LuminanceWipe,
    ModernGLRenderer,
    OuterGlow,
    ParticleField,
    PathData,
    PathMask,
    PillowRenderer,
    ProceduralBackground,
    Rectangle,
    Scene,
    Sequence,
    ShadowStyle,
    ZoomBlurTransition,
    create_renderer,
    linear,
    renderer_capabilities,
    rendering_identity,
)


@pytest.fixture
def gpu():
    pytest.importorskip("moderngl")
    try:
        renderer = ModernGLRenderer(1)
    except RuntimeError as exc:
        pytest.skip(str(exc))
    with renderer:
        yield renderer


def solid(color, duration=1):
    return Scene(Canvas(80, 60, color)).wait(duration)


def test_imports_and_capabilities_do_not_load_native_engines():
    code = "\nimport builtins,sys\noriginal=builtins.__import__\ndef block(name,*a,**k):\n    if name in {'moderngl','glcontext','numpy','skia'}:raise ImportError('blocked optional dependency')\n    return original(name,*a,**k)\nbuiltins.__import__=block\nfrom faceless_champ import renderer_capabilities, create_renderer\nassert not renderer_capabilities()['probed']\nwith create_renderer('pillow'):pass\nassert 'moderngl' not in sys.modules\ntry:create_renderer('moderngl')\nexcept RuntimeError as e:assert 'faceless-champ[gpu]' in str(e)\nelse:raise AssertionError('must fail explicitly')\n"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_rgba_orientation_and_transparent_rgb(gpu):
    pixels = PI.new("RGBA", (8, 8), (0, 0, 0, 0))
    pixels.paste((255, 0, 0, 128), (0, 0, 8, 4))
    pixels.paste((0, 0, 255, 255), (0, 4, 8, 8))
    scene = Scene(Canvas(8, 8, "#00000000")).add(Image.from_source(pixels, width=8, height=8, position=(4, 4))).wait(1)
    frame = gpu.frame(scene, 0, (8, 8))
    assert frame.getpixel((4, 1)) == (255, 0, 0, 128)
    assert frame.getpixel((4, 6)) == (0, 0, 255, 255)


def test_group_member_opacity_and_mask(gpu):
    a = Rectangle(width=50, height=40, fill="red", stroke=None, position=(40, 30))
    b = Rectangle(width=50, height=40, fill="blue", stroke=None, position=(40, 30))
    scene = Scene(Canvas(80, 60, "#00000000")).add(Group(a, b, opacity=0.5, mask=CircleMask(15))).wait(1)
    frame = gpu.frame(scene, 0, (80, 60))
    assert frame.getpixel((40, 30))[3] == 192
    assert frame.getpixel((0, 0)) == (0, 0, 0, 0)


def test_nested_composition_has_only_final_readback(gpu):
    seq = Sequence(solid("red", 2), solid("blue", 2), crossfade=1)
    grid = Grid(seq, solid("green", 3), rows=1, columns=2, canvas=Canvas(160, 60))
    image = gpu.frame(Layer(grid), 1.5, (160, 60))
    assert image.getpixel((40, 30))[:3] == (127, 0, 127)
    assert image.getpixel((120, 30))[:3] == (0, 128, 0)
    assert gpu.stats["readbacks"] == 1


@pytest.mark.parametrize(
    "effect",
    [
        EffectStack(blur=GaussianBlur(2)),
        EffectStack(glow=OuterGlow("#FF3300", 3, 0.8)),
        EffectStack(bloom=Bloom(2, 0.2, 0.5)),
        EffectStack(distortion=Distortion(2, 2, 1)),
        EffectStack(chromatic=ChromaticAberration(2)),
        EffectStack(light_sweep=LightSweep()),
    ],
)
def test_cpu_gpu_effect_reference(gpu, effect):
    import numpy as np

    # Image input isolates effect math from intentional primitive edge raster differences.
    source = PI.new("RGBA", (20, 16), "#FF553399")
    c = Image.from_source(source, width=20, height=16, position=(40, 30), effects=effect)
    scene = Scene(Canvas(80, 60, "#00000000")).add(c).wait(2)
    with PillowRenderer(1) as cpu:
        expected = np.asarray(cpu.frame(scene, 0.3, (80, 60))).astype(int)
    actual = np.asarray(gpu.frame(scene, 0.3, (80, 60))).astype(int)
    # Hidden RGB is canonical zero; tiny halos can magnify unpremultiplication error.
    visible = (actual[..., 3] > 8) & (expected[..., 3] > 8)
    assert abs(actual[..., 3] - expected[..., 3]).max() <= 2
    assert abs(actual[visible] - expected[visible]).max() <= 2
    assert not actual[actual[..., 3] == 0].any()


@pytest.mark.parametrize("transition", [None, DirectionalWipe(), LuminanceWipe(), ZoomBlurTransition()])
def test_transition_endpoints_and_cpu_reference(gpu, transition):
    import numpy as np

    seq = Sequence(solid("#FF000080", 2), solid("#0000FFFF", 2), crossfade=1, transition=transition)
    with PillowRenderer(1) as cpu:
        for time in (0, 1, 1.5, 2, 3):
            a = np.asarray(gpu.frame(seq, time, (80, 60))).astype(int)
            b = np.asarray(cpu.frame(seq, time, (80, 60))).astype(int)
            assert abs(a - b).max() <= 2


def test_cache_seek_copies_and_dynamic_effect_clock(gpu):
    c = Image.from_source(
        PI.new("RGBA", (20, 20), "#AABBCC"),
        width=20,
        height=20,
        position=(40, 30),
        effects=EffectStack(light_sweep=LightSweep(width=0.25)),
    )
    scene = Scene(Canvas(80, 60)).add(c).wait(3)
    first = gpu.frame(scene, 0.3, (80, 60)).tobytes()
    assert gpu.frame(scene, 1.2, (80, 60)).tobytes() != first
    for t in (2, 0.2, 0.3):
        gpu.frame(scene, t, (80, 60))
    assert gpu.frame(scene, 0.3, (80, 60)).tobytes() == first
    edited = gpu.frame(scene, 0.3, (80, 60))
    edited.paste("white", (0, 0, 80, 60))
    assert gpu.frame(scene, 0.3, (80, 60)).tobytes() == first
    assert gpu.stats["texture_hits"] > 0


def test_effect_tracks_snapshots_and_ink_bounds():
    c = Rectangle(width=20, height=20, position=(40, 30), effects=EffectStack(glow=OuterGlow(radius=1)))
    scene = Scene(Canvas(80, 60)).add(c)
    scene.play(c.animate.effect_to("glow", radius=5), run_time=1, rate_func=linear)
    assert scene.entries[0].state_at(0.5)["effect.glow.radius"] == 3
    assert scene.ink_bounds_at(c, 0.5).width > scene.bounds_at(c, 0.5).width
    with pytest.raises(ValueError):
        scene.play(c.animate.effect_to("glow", radius=-1))


def test_seeded_procedural_and_instanced_particles(gpu):
    for c in (
        ProceduralBackground(width=80, height=60, position=(40, 30), seed=12),
        ParticleField(width=80, height=60, position=(40, 30), seed=12, count=100),
    ):
        scene = Scene(Canvas(80, 60, "#00000000")).add(c).wait(3)
        first = gpu.frame(scene, 0.3, (80, 60)).tobytes()
        assert gpu.frame(scene, 1.3, (80, 60)).tobytes() != first
        assert gpu.frame(scene, 0.3, (80, 60)).tobytes() == first
        assert gpu.frame(scene, 0.3, (80, 60)).getbbox() is not None


def test_auto_selection_records_actual_device(gpu):
    with create_renderer("auto", antialias=1) as auto:
        auto.validate(solid("red"))
        identity = rendering_identity("auto", renderer=auto)
        assert identity["backend"] in {"pillow", "skia", "moderngl"}
        assert identity["requested_backend"] == "auto"
        if gpu.identity["device"] == "software":
            assert identity["backend"] != "moderngl"


def test_budgets_and_close(gpu):
    with pytest.raises(ValueError):
        gpu.frame(solid("red"), 0, (20000, 100))
    gpu.frame(solid("red"), 0, (80, 60))
    gpu.close()
    gpu.close()
    assert gpu.device.working_bytes == gpu.device.texture_bytes == gpu.frames.bytes == 0
    with pytest.raises(RuntimeError, match="closed"):
        gpu.frame(solid("red"), 0, (80, 60))
    with pytest.raises(ValueError):
        GPUOptions(working_mb=-1)
    assert renderer_capabilities("moderngl")["probed"] is False


def test_leaf_shadow_and_group_effect_preserve_opacity(gpu):
    c = Image.from_source(
        PI.new("RGBA", (20, 20), "#FF000080"),
        width=20,
        height=20,
        position=(40, 30),
        effects=EffectStack(glow=OuterGlow(radius=2, intensity=0)),
        shadow=ShadowStyle(blur=0, offset=(5, 0)),
    )
    scene = Scene(Canvas(80, 60, "#00000000")).add(c).wait(1)
    assert gpu.frame(scene, 0, (80, 60)).getpixel((40, 30))[3] >= 128
    a = Rectangle(width=20, height=20, fill="red", stroke=None, position=(40, 30))
    b = Rectangle(width=20, height=20, fill="blue", stroke=None, position=(40, 30))
    scene = (
        Scene(Canvas(80, 60, "#00000000"))
        .add(Group(a, b, opacity=0.5, effects=EffectStack(blur=GaussianBlur(0))))
        .wait(1)
    )
    assert gpu.frame(scene, 0, (80, 60)).getpixel((40, 30))[3] == 192


def test_real_export_range_audio_and_caller_ownership(gpu, tmp_path, tone):
    from faceless_champ import render
    from faceless_champ.audio import probe

    first, second = solid("red", 1), solid("blue", 1)
    second.add_audio(tone, start=0, trim_end=1)
    node = Sequence(first, second, crossfade=0.2, transition=DirectionalWipe())
    output = render(
        node,
        tmp_path / "gpu.mp4",
        renderer=gpu,
        width=80,
        height=60,
        fps=10,
        start_time=0.8,
        end_time=1.2,
        preset="ultrafast",
    )
    info = probe(output)
    assert any(s["codec_type"] == "audio" for s in info["streams"])
    assert abs(float(info["format"]["duration"]) - 0.4) < 0.1
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(output), "-f", "null", "-"], check=True, capture_output=True)
    assert not gpu._closed


def test_vtk_viewport_context_restores_for_gpu_overlay(gpu):
    import pyvista as pv
    from facelesschamp_kit.engineering.clip import ArchChamp

    from faceless_champ import Text
    from faceless_champ.integrations.pyvista.model import ArchMesh

    view = ArchChamp(ArchMesh.from_data(pv.Cube()), width=80, height=80, position=(40, 50))
    label = Text("GPU", font_size=18, position=(125, 50), color="white")
    node = Scene(Canvas(160, 100, "black")).add(view, label).wait(1)
    frame = gpu.frame(node, 0.3, (160, 100))
    assert frame.crop((90, 20, 160, 80)).convert("RGB").getbbox() is not None
    owned = next(iter(gpu.raster.painter._sources.sessions.values()))[1]
    worker = owned.worker.process
    assert worker.poll() is None
    owned.close()
    assert gpu.frame(solid("red"), 0, (80, 60)).getpixel((40, 30)) == (255, 0, 0, 255)
    gpu.close()
    assert worker.poll() == 0


def test_composited_effects_structural_similarity(gpu):
    import numpy as np

    ramp = np.zeros((48, 64, 4), dtype="uint8")
    ramp[..., 0] = 220
    ramp[..., 1] = np.arange(64, dtype="uint8")[None, :] * 3
    ramp[..., 2] = 90
    ramp[..., 3] = np.arange(64, dtype="uint8")[None, :] * 4
    c = Image.from_source(
        PI.fromarray(ramp),
        width=64,
        height=48,
        position=(80, 60),
        effects=EffectStack(blur=GaussianBlur(1.5), glow=OuterGlow(radius=4), bloom=Bloom(3, 0.2, 0.4)),
    )
    scene = Scene(Canvas(160, 120, "#162137")).add(c).wait(1)
    with PillowRenderer(1) as cpu:
        a = np.asarray(cpu.frame(scene, 0.2, (160, 120)), dtype=float)[..., :3] / 255
    b = np.asarray(gpu.frame(scene, 0.2, (160, 120)), dtype=float)[..., :3] / 255
    # Nonoverlapping 8x8 RGB windows measure structure after alpha composition.
    a = a.reshape(15, 8, 20, 8, 3).transpose(0, 2, 4, 1, 3).reshape(-1, 64)
    b = b.reshape(15, 8, 20, 8, 3).transpose(0, 2, 4, 1, 3).reshape(-1, 64)
    ma, mb = a.mean(axis=1), b.mean(axis=1)
    va, vb = a.var(axis=1), b.var(axis=1)
    cov = ((a - ma[:, None]) * (b - mb[:, None])).mean(axis=1)
    ssim = ((2 * ma * mb + 0.01**2) * (2 * cov + 0.03**2)) / ((ma * ma + mb * mb + 0.01**2) * (va + vb + 0.03**2))
    assert ssim.mean() >= 0.995


def test_working_guard_and_no_cache_reference(gpu):
    with ModernGLRenderer(1, gpu=GPUOptions(working_mb=1)) as tiny, pytest.raises(ValueError, match="working_mb"):
        tiny.frame(solid("red"), 0, (400, 300))
    with ModernGLRenderer(1, gpu=GPUOptions(frame_cache_mb=0, texture_cache_mb=0)) as uncached:
        scene = solid("red")
        first = uncached.frame(scene, 0, (80, 60)).tobytes()
        uncached.frame(scene, 0.8, (80, 60))
        assert uncached.frame(scene, 0, (80, 60)).tobytes() == first
        assert uncached.frames.bytes == uncached.device.texture_bytes == 0


def test_particle_clock_is_independent_of_background_speed(gpu):
    field = ParticleField(width=80, height=60, position=(40, 30), count=20, speed=0)
    scene = Scene(Canvas(80, 60)).add(field).wait(2)
    assert gpu.frame(scene, 0.2, (80, 60)).tobytes() != gpu.frame(scene, 0.7, (80, 60)).tobytes()
    assert field.frame_key(0.2) != field.frame_key(0.7)


@pytest.mark.parametrize("isolation", ["leaf", "group", "nested_group"])
@pytest.mark.parametrize("scale", [0.5, 1, 2])
def test_particle_overhang_survives_noop_isolation(gpu, isolation, scale):
    import numpy as np

    def scene(isolated):
        field = ParticleField(width=20, height=20, radius=25, count=10, position=(80, 80))
        if isolation == "leaf":
            field.effects = EffectStack() if isolated else None
            field.scale = scale
            root = field
        else:
            root = Group(field, scale=scale, effects=EffectStack() if isolated else None)
            if isolation == "nested_group":
                root = Group(root, effects=EffectStack() if isolated else None)
        return Scene(Canvas(160, 160, "#00000000")).add(root).wait(1)

    expected = np.asarray(gpu.frame(scene(False), 0.3, (160, 160)), dtype=int)
    actual = np.asarray(gpu.frame(scene(True), 0.3, (160, 160)), dtype=int)
    assert expected[..., 3].sum() > 0
    assert abs(actual[..., 3] - expected[..., 3]).max() <= 1


def test_particle_buffer_growth_reclaims_idle_targets(gpu):
    scene = (
        Scene(Canvas(80, 60, "#00000000"))
        .add(ParticleField(width=80, height=60, position=(40, 30), count=10_000))
        .wait(1)
    )
    options = GPUOptions(working_mb=1, frame_cache_mb=0)
    with ModernGLRenderer(1, gpu=options) as fresh:
        expected = fresh.frame(scene, 0.3, (80, 60)).tobytes()
    with ModernGLRenderer(1, gpu=options) as reused:
        reused.frame(Scene(Canvas(400, 200)).wait(1), 0, (400, 200))
        assert reused.frame(scene, 0.3, (80, 60)).tobytes() == expected
        assert reused.device.working_bytes + reused.device.particle_bytes <= 1024**2
        assert reused.device.active_bytes == 0

        # Live targets cannot be reclaimed to accommodate an oversized buffer.
        too_large = (
            Scene(Canvas(80, 60)).add(ParticleField(width=80, height=60, count=100_000, position=(40, 30))).wait(1)
        )
        with pytest.raises(ValueError, match="Particle buffer exceeds working_mb"):
            reused.frame(too_large, 0.3, (80, 60))
        assert reused.device.active_bytes == 0
        assert reused.frame(scene, 0.3, (80, 60)).tobytes() == expected


@pytest.mark.parametrize("component", [ProceduralBackground, ParticleField])
def test_procedural_masks_are_checked_during_preflight(component, monkeypatch):
    from faceless_champ.backends import _native

    path = PathData().move_to(0, 0).line_to(1, 0).line_to(0.5, 1).close()
    scene = Scene(Canvas(80, 60)).add(component(mask=PathMask(path, width=60, height=40))).wait(1)
    with PillowRenderer(1) as renderer:
        renderer.validate(scene, backend="structural")
        with pytest.raises(ValueError, match="PathMask"):
            renderer.validate(scene)

        def unavailable():
            raise RuntimeError("native mask dependency unavailable")

        monkeypatch.setattr(_native, "load_skia", unavailable)
        with pytest.raises(RuntimeError, match="native mask dependency unavailable"):
            renderer.validate(scene, backend="skia")


def test_descriptors_store_validated_numeric_values():
    from dataclasses import FrozenInstanceError

    effect = GaussianBlur("2")
    assert effect.radius == 2 and EffectStack(blur=effect).padding == 6
    assert DirectionalWipe("0.2").softness == 0.2
    assert ZoomBlurTransition("0.3").strength == 0.3
    with pytest.raises(FrozenInstanceError):
        effect.radius = 3
    for invalid in (float("nan"), float("inf"), -1, 4097):
        with pytest.raises(ValueError):
            GaussianBlur(invalid)
    for invalid in (float("nan"), float("inf"), -1, 1.01):
        with pytest.raises(ValueError):
            DirectionalWipe(invalid)
