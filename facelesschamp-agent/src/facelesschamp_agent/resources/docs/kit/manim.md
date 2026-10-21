# Prepared mathematical scenes

Kit owns mathematical presets and layout; Core owns optional native preparation
and prepared-frame playback. Agent discovers structured requirements and guidance.
The MVP does not add a JSON math recipe or an automatic math router.

```python
from faceless_champ.integrations.manim import ManimRenderOptions
from facelesschamp_kit import EquationTransform, Video
from facelesschamp_kit.blocks import ManimCanvas

def build(ctx):
    preset = EquationTransform(
        (r"{{x}}^2+2{{x}}+1", r"({{x}}+1)^2"),
        transform_time=2, hold_time=1.5, color=ctx.theme.foreground,
    )
    source = ctx.manim(preset.scene_spec(),
                       options=ManimRenderOptions(width=640, height=360, fps=15))
    video = Video(ctx)
    segment = video.segment("algebra", duration=source.duration)
    segment.add(ManimCanvas(source), id="equation", enter=None, exit=None)
    return video
```

`EquationTransform` builds a data-only scene specification. Its shipped worker
uses `MathTex` and `TransformMatchingTex`; `{{token}}` isolation is preserved.
Equations are supplied by the author, not solved or proved. All expressions share
a fixed fit; timing phases resolve to absolute source-frame boundaries. Positive
phases shorter than one frame fail rather than silently disappearing.

`ManimCanvas(prepared, source_start=0)` fits the prepared source into allocated
bounds and exposes the `animation` child for ordinary Kit transforms. It contains
no Manim objects. Other mathematical scenes can use `ManimSceneSpec` directly;
calculus, linear algebra, graphs and geometry need no additional Core backend.

Only `Project.prepare()` or `fc-kit prepare` executes `ctx.manim` requests. Normal
build/validate/frame/export loads matching assets and raises `MANIM_UNPREPARED`
when preparation is needed. Runtime changes are adopted on explicit preparation;
normal builds never probe an engine. Reports include prepared content identity and
provenance, so refreshed pixels participate in existing Agent evidence fingerprints.
Cache files live under `.fc-kit/manim`. An explicit options seed wins; omitted
options inherit the project seed. `python=` selects a separate Manim environment.

The runnable POC is `examples/mathematics/manim_transform/`. From the checkout:

```bash
export FC_MANIM_PYTHON=/path/to/manim-env/bin/python
fc-kit --project examples/mathematics/manim_transform prepare
fc-kit --project examples/mathematics/manim_transform frame --time 3.5 -o output/manim/midpoint.png
fc-kit --project examples/mathematics/manim_transform preview -o output/manim/equation-preview.mp4
```

The POC writes for one second, holds 1.5 seconds, transforms for two seconds and
holds another 1.5 seconds: six seconds / 90 frames at 640×360, 15 FPS. The prepared
alpha is composited over the FacelessChamp background. Use `fc-kit prepare
--refresh` after intentionally changing undeclared toolchain inputs.

Install `facelesschamp-kit[manim]` only when preparing in the Kit interpreter.
Prepared playback requires no Manim/TeX installation. Read the
[Core guide](../core/manim.md) for dependencies, cache integrity, subprocess
limits, supported platforms and optional Docker preparation. Agent capability
records distinguish preparation requirements from Pillow-only playback. Prefer
Core `Equation`/`Write` or existing charts when those express the intended scene.
