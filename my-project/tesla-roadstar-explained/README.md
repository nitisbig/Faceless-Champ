# Roadster: the mathematics behind the maneuver

## V2 — current version

[Open the v2 review player](output/v2/index.html) for the cinematic opening,
pressure motion excerpt, and selected graph/matrix frames. V2 adds a dimensional
C-road and camera orbit, larger mathematical typography, staged diagrams,
an isometric pressure chamber, curved nozzle streamlines, and redesigned matrices.
The original black/red/blue direction and narration clock are preserved.

```bash
../../.venv/bin/python render_v2.py --range 0 6.76 --quality low --fps 15
../../.venv/bin/python render_v2.py --preview 8 --quality low --fps 10
../../.venv/bin/python render_v2.py --full --quality 4k --fps 30
```

V2 has its own renderer and `output/v2/` directory. Only key scenes have been
rendered and inspected; the complete film and 4K export remain unverified.
See [V2-DESIGN.md](V2-DESIGN.md) for the research, visual decisions, and controls.

## V1 — retained red/blue version

The revised 12:18.300 film uses a true black stage, neon red trajectory lines
and blue outlines. Larger engineering visuals share a consistent composition
with centered mathematical results, a restrained supporting derivation, aligned
matrix cells and clearer graph legends. Titles, chapter headings, prose callouts
and footer text remain absent.

The opening is now one continuous 6.76-second demonstration. The whole C-shaped
road and car are visible at frame zero; a gentle camera move preserves the full
apparatus while the car approaches, climbs, inverts and releases. The red wake
and moving road pulses communicate motion. There are no cropped opening shots.
The original narration and analytical source clock are preserved.

## Render from this project directory

```bash
# Fast review of the opening
../../.venv/bin/python render.py --range 0 6.76 --fps 10 --quality low --overwrite

# A narrated chapter excerpt
../../.venv/bin/python render.py --preview --chapter 7 --fps 15 --quality low --overwrite

# A single frame at the requested resolution
../../.venv/bin/python render.py --frame 553 --quality high --overwrite

# Complete export when ready
../../.venv/bin/python render.py --full --fps 30 --quality 4k
```

`--fps` accepts **10, 15 or 30**. `--quality` accepts **low** (960×540, CRF 23,
fast encoder), **high** (1920×1080, CRF 17) or **4k** (3840×2160, CRF 17).
The old `1080p` spelling remains an alias for `high`. Frame rate defaults to 30.
Previews and ranges default to low; full films and still frames default to 4K.
`--output PATH` selects the destination. Files include the selected quality and
frame rate in their names. Existing outputs require `--overwrite`.

Times are absolute source seconds. `--preview` without a chapter renders all ten
excerpts; use `--chapter` for a bounded review. The original narration remains at
master zero and is trimmed together with the requested visual range.

## V1 review

[Red/blue revision player and key frames](output/revision-red-blue/index.html) contains
the small review requested for this edit. [verification.md](verification.md)
separates current sampled evidence from the previous design's verification.
Earlier files in `output/revision-neon`, `output/previews`, `output/storyboard`
and `output/frames` show previous designs. The complete revised film has not been rendered or audited.

## Authoring

`main.py` exposes `build_master()` and `RoadsterRenderer`. The master is a core
`Scene` with one narration clip at zero. The project renderer uses ArchChamp for
3D geometry and cameras, and the existing streaming exporter for source-clock
ranges and audio. Project-local compositions supply analytical plots and motion.

Equations use the existing offline MathText engine with STIX math fonts:
fractions, bold vectors, integrals, subscripts, derivatives and aligned matrix
cells. Matrix brackets and glow are drawn at output resolution. No TeX system,
fonts, meshes or images are downloaded. No shared library package is modified.

## Source clock and scientific assumptions

The four supplied source files are unchanged. `source-fingerprints.json` detects
later changes. The word SRT contains 1,975 cues ending at 738.120 s, including the
five intentional 1 ms overlaps. The normal SRT supplies context. Decoded audio is
738.272666667 s; the last image holds to the frame-aligned 738.300 s endpoint.

All calculations use SI units, a right-handed X-forward/Y-left/Z-up body frame,
and world Z up. Imported Y coordinates and face winding are converted once. The
shared center of mass is an assumption, not a measured Tesla value.

The independent constant-mass examples use 1700 kg, g=9.81 m/s², effective μ=1,
2 m² suction area, 2mg suction, 12 m curvature radius, 12 m/s speed, 800 kg·m² roll
inertia, 1.6 s half-roll and 1.5 m thruster separation. They reset between examples;
the gas budget is not cumulatively applied to the separate landing experiment.

The nominal replay uses a 4 m/s² approach, constant-speed circular contact,
tangent release, the prescribed torque couple, and 2mg vertical braking after
half the available drop. It stops the playback clock at touchdown; horizontal
momentum is retained. The final stationary hero is a separate presentation view.

Gravity remains world-down. Suction vanishes at separation. At the loop apex the
road reaction points inward/down and suction points outward/up. Available friction
is a capacity, not an extra applied force. The 20 m landing reaches zero speed
from its equations; it is not eased toward a hand-placed endpoint. The uncontrolled
case uses an ideal inelastic impact and retains incoming impact speed separately.

The airflow/pressure field is illustrative, not a CFD solution. Fan ratings,
nozzle counts and stored-gas quantities from the narration are tagged as reported.
Hidden hardware is schematic, not Tesla CAD. The allocation diagram is a generic
architecture, and the attitude-target demonstration is an illustrative single-axis
response, not a reconstructed Tesla controller or validated coupled 6-DOF solver.

Primary reference pointers: [Tesla's event](https://www.youtube.com/live/qt5p-_tE8d0),
[Hagerty's engineering interview](https://www.hagerty.com/media/videos/the-flying-tesla-roadster-explained-by-the-man-who-engineered-it/),
and [NASA's nozzle thrust equation](https://www.grc.nasa.gov/www/k-12/BGP/rktthsum.html).
These links are reference pointers; the rendered reconstruction does not claim
independently measured prototype geometry or telemetry.

## Assets, typography and offline operation

Five illustration plates from the earlier design remain archived in
`assets/13_Generated` with their prompts and hashes. The current black-stage
composition uses procedural 3D views throughout, including the closing shot.
HD/4K geometry, graphs and typography render at the selected output resolution.

Space Grotesk and DM Sans come from the repository's local font assets and retain
their existing OFL licenses. Greek annotation text uses the bundled DejaVu Sans
fallback; equations use STIX. No fonts, meshes or images are downloaded at render
time. Supplied source assets are retained in their original directories; refined
VTP geometry is exported separately to `assets/12_Refined_Models`.

Closed, manifold surfaces are required only for parts receiving capped sections.
Decorative rim spokes are multi-piece geometry and are not passed to the capper.
To bound rendering cost, opaque exterior views hide internal hardware, renderer
sessions have a fixed limit, and a bounded fan-cycle cache reuses the repeating
illustrative rotor motion. Physical car transforms and graph cursors retain their
analytical source-time states.

Python 3.12+, FFmpeg/ffprobe and the dependencies in `requirements.txt` are needed.
The existing repository environment already supplies them. The entrypoint uses a
writable Matplotlib cache under `/tmp`; headless VTK may print an X-server warning
even when its offscreen renders succeed.

## Optional checks from this project directory

```bash
MPLCONFIGDIR=/tmp/tesla-mpl ../../.venv/bin/python -m pytest -q tests
../../.venv/bin/ruff check --no-cache scene tests render.py main.py
```

Checks cover cue preservation, force balance, friction capacity, release
continuity, torque reversal, stopped roll rate, continued descent at hover thrust,
calculated landing contact, cap-ready geometry and arbitrary-time seeking.
`--verify` can decode recorded chapter previews and compare their source audio
windows. The current edit uses only the bounded review described above; see
`verification.md` for its actual evidence.

