# Burj Khalifa — engineering through geometry

A complete 182.200-second narrated training composition for ArchChamp and
FacelessChamp Kit. The supplied audio and all 436 word cues are preserved.
There are seven chapters, original procedural geometry, concise labels and no
subtitle or chapter-title overlays. [outline.md](outline.md) records the visual
proofs, timing boundaries, engineering sources and modeling limits.

## Run

From the repository root (the wrapper selects the repository environment):

```bash
python3 "training project/burj khalifa/render.py"
python3 "training project/burj khalifa/render.py" --list-scenes
python3 "training project/burj khalifa/render.py" --check
python3 "training project/burj khalifa/render.py" --frame 45.5 --quality high
python3 "training project/burj khalifa/render.py" --storyboard
python3 "training project/burj khalifa/render.py" --range 114 117
python3 "training project/burj khalifa/render.py" --scene aerodynamics
```

No options export only 0–12 seconds at 960×540/15 FPS. Both profiles use 2×
supersampling. `--quality high` selects 1920×1080/30 FPS; quality alone retains
the short range. `--fps 15|30`, `--output PATH` and `--overwrite` are available.
Existing outputs are protected unless `--overwrite` is supplied.

The complete film is an explicit, potentially expensive command:

```bash
python3 "training project/burj khalifa/render.py" --full --quality high
```

The complete/full-HD export is **intentionally unrun**. See
[verification.md](verification.md) and [verification.json](verification.json)
for the actual evidence and `full_export_verified: false`.

## Training feature map

| Public API | What this composition teaches |
|---|---|
| `ArchMesh`, `ArchPart`, `ArchStyle` | Immutable shared geometry, named assemblies, solid/wireframe/transparent presentation, batched repetition. |
| `ArchCanvas`, `Video`, segments | Fitted 3D viewports inside ordinary kit compositions with a single narration clock. |
| `ArchScript.camera_to`, `orbit` | Metre-based framing, top-down plans, below-grade tracking, held explanatory cameras and smooth easing. |
| `explode`, `move`, `highlight`, `opacity`, `show` | Structural separation/reassembly, sequential emphasis, pumping packets and reveal tracks. |
| `section(cap=True, contour=True)` | Closed soil cutaway revealing independently modeled foundations. |
| `ArchLabel`, `ArchDimension` | World/part anchors and actual model-coordinate measurements. |
| Core `Arrow`, `Polyline`, `Group`, `Text` | A flower diagram, daylight/view directions and sparse explanatory notes. |
| Core component opacity animation | Camera-aligned wireframe/solid viewport crossfade. |
| `Project`, `layout_at`, `diagnostics_at` | Dependency reporting, geometry hashes, annotation and safe-margin inspection. |
| Preview/export APIs | Source-time stills, storyboard, excerpt export, bounded renderer ownership and full export opt-in. |

`main:build(ctx)` is the kit entry point. `scene/model.py` owns content-specific
geometry; `scene/story.py` owns narration-specific composition. Reusable playback
and rendering stay in core/kit. The only new library interface is
`ArchScript` action `easing="smooth"`; old actions default to `"linear"` and
their serialized shape stays compatible. `show`/`hide` remain immediate switches.

## Geometry, audio and portability

- Coordinates are metres, world Z is vertical, the spire ends at 828 m, the raft
  is 3.7 m thick and 192 closed pile cylinders are generated before batching.
- Member sizing, setback heights, pile layout and the floor plan are simplified
  teaching geometry. The model is not a surveyed CAD reproduction.
- Repeated façade modules represent nearly 26,000 real panels. Wind, force,
  pumping and heat graphics are schematic; no CFD/FEA solver or measured field
  data is claimed. The original brief's engineering simulations are explained
  through these labeled illustrations.
- Source MP3, both SRTs, `voicover.md` and the design brief are untouched. FFmpeg
  decodes the MP3 to ignored `output/narration.wav`: 8,745,600 mono PCM samples at
  48 kHz, without stretching. Source checksum changes invalidate the cache.
- Preserve the intentional 1 ms overlap between cues 231/232. The final cue ends
  at 181.880; the last 0.320 seconds hold without new motion.
- No network/model download occurs during builds. `pyproject.toml` declares the
  existing core/kit/PyVista/NumPy requirements. Inter is selected when installed;
  the normal kit font remains the portable fallback.
- Use this checkout or core/kit wheels built from it: the example exercises the
  new easing option implemented alongside these scenes.
- PyVista/VTK needs working offscreen OpenGL/EGL. `FC_INSTALLED_ONLY=1` disables
  source-path/interpreter selection for installed-package validation.

## Repeat QA

```bash
python3 "training project/burj khalifa/verify.py"
python3 "training project/burj khalifa/verify.py" --render-excerpts
python3 "training project/burj khalifa/verify.py" --media
.venv/bin/python -m pytest "training project/burj khalifa/test_burj.py" -q
```

The default verifier checks the entire source timeline without opening rendering
resources. `--render-excerpts` overwrites only seven known three-second preview
files, then checks frame counts, full decode, audio correlation and sample lag.
`--media` rechecks those existing files. Neither flag exports the full film.
Storyboard and encoded-frame editorial review are recorded separately in the
verification notes; automatic checks do not claim visual editorial approval.
