# Dependency and import analysis

Status: audit plus proposed installation model. Baseline:
`22f3beaccb5a56990bd0974666b7c639a0667a68`, 2026-10-20.
See [performance measurements](performance-baseline.md),
[backend contracts](backend-integration.md), and [migration](migration-plan.md).

The manifests and measurements below describe the frozen audit baseline. For the
subsequently implemented Pillow-only base and explicit 3D extras, see
[the M1 implementation record](m1-implementation.md). Coordinated V2 versions,
production ownership and distribution lanes are recorded in [M5](m5-implementation.md).

## Current package requirements

Source manifests are authoritative: [Core](../../pyproject.toml),
[Kit](../../facelesschamp-kit/pyproject.toml),
[Agent](../../facelesschamp-agent/pyproject.toml). Python is `>=3.12`.

| Distribution | Source version | Mandatory dependencies | Build backend / CLI |
| --- | --- | --- | --- |
| `faceless-champ` | 0.1.6 | `Pillow>=10.4,<13`, `pyvista>=0.49.1` | uv_build / `faceless-champ` |
| `facelesschamp-kit` | 0.1.0rc7 | `faceless-champ>=0.1.6,<0.2.0`, `packaging>=24` | setuptools / `fc-kit` |
| `facelesschamp-agent` | 0.1.0rc2 | `facelesschamp-kit>=0.1.0rc7,<0.2.0`, `pydantic>=2,<3` | setuptools / `fc-agent` |

Only Core has a tracked `uv.lock`; Kit and Agent are separate distributions rather
than a declared uv workspace. Current editable Kit metadata still records a Core
minimum of 0.1.5, while its source manifest requires 0.1.6. Source code was imported
from the checkout during tests. This environment drift is not proof that a newly
built Kit wheel has the old requirement; clean-wheel validation must inspect the
wheel metadata rather than reuse the editable environment.

| Core extra | Declared additional packages |
| --- | --- |
| `cad` | build123d >=0.13,<0.14, Python <3.15 |
| `geometry` | Trimesh >=5.1.1,<6; SciPy >=1.16,<2; NetworkX >=3,<4 |
| `geometry-advanced` | geometry packages; manifold3d >=3.5.4,<4; fast-simplification >=0.2,<0.3 |
| `gpu` | ModernGL >=5.13,<6; glcontext >=3.1,<4; NumPy >=1.26,<3 |
| `effects`, `maps` | NumPy >=1.26,<3 |
| `skia` | skia-python >=144.0.post2,<145; NumPy >=1.26,<3 |
| `chess` | chess >=1.11.2,<2 |
| `coding` | Pygments >=2.18,<3 |
| `playground` | Pygments >=2.18,<3; Playwright >=1.58,<2 |
| `web` | Playwright >=1.58,<2 |
| `equations` | Matplotlib >=3.9,<4 |

Kit forwards GPU/effects/Skia/coding/playground/chess/web/maps/equations extras to
Core, but not CAD/geometry. Agent forwards only GPU/effects/Skia to Kit. This is
an inconsistent one-command installation surface for domain production workflows.
Dependency forwarding must follow ownership after extraction, not merely repeat
the old Core-extra list.

## Transitive cost and avoidable dependencies

The marker-aware installed Linux base closure contains 32 distributions including
Core. An unfiltered lock traversal gives 34 because it includes two macOS PyObjC
packages. Do not describe 34 as the Linux installation count.

```text
attrs certifi charset-normalizer contourpy cycler cyclopts docstring-parser
faceless-champ fonttools idna kiwisolver markdown-it-py matplotlib mdurl numpy
packaging pillow platformdirs pooch pygments pyparsing python-dateutil pyvista
pyvista-validation requests rich rich-rst scooby six typing-extensions urllib3 vtk
```

PyVista requires VTK, NumPy, Matplotlib and supporting CLI/data/download packages;
VTK also declares Matplotlib. Thus equations' and maps' nominal optional dependencies
are already pulled into the current base transitively. These libraries are useful
when their features are selected; they are unnecessary for the basic 2D path.

| Installed distribution | Version | Accounted installed MiB |
| --- | --- | ---: |
| Pillow | 12.3.0 | 18.76 |
| PyVista | 0.49.1 | 7.33 |
| VTK | 9.7.1 | 562.23 |
| NumPy | 2.5.3 | 53.75 |
| Matplotlib | 3.11.2 | 23.86 |
| Skia | 144.0.post2 | 32.27 |
| ModernGL / glcontext | 5.13.0 / 3.1.0 | 1.04 / 0.11 |
| Trimesh / NetworkX | 5.1.1 / 3.7 | 1.97 / 6.96 |
| SciPy | 1.18.1 | 106.75 |
| build123d | 0.13.0 | 1.41 |
| manifold3d / fast-simplification | 3.5.4 / 0.2.0 | 3.97 / 0.67 |
| Playwright | 1.63.0 | 136.06 |
| Pygments / Pydantic / packaging | 2.21.0 / 2.14.1 / 26.3 | 4.41 / 1.87 / 0.48 |

Method: sum regular file sizes listed in each installed distribution's metadata.
These values exclude its dependency closure, external browser downloads, Python
itself and runtime RSS. The small editable package metadata sizes are not valid
measurements of Core/Kit/Agent code and assets. VTK's recorded Linux wheel size in
the lock is about 133.19 MiB compressed; that differs from its installed footprint.

build123d's closure includes the OCCT provider, SciPy, scikit-learn, SymPy, IPython,
font/export helpers and other utilities. Keep that entire stack optional rather
than trying to remove dependencies required by upstream. Preserve the existing
conflict rejection when `cadquery-ocp` and `cadquery-ocp-novtk` coexist.

Trimesh itself is comparatively light and documents soft dependencies; choose
operation-specific helpers rather than its broad `all`/`easy` bundles. Current
FacelessChamp inspection/repair/simplification code explicitly uses SciPy,
NetworkX, Manifold and fast-simplification in different operations, so removing
them from advertised functionality without corresponding changes would break it.
See [Trimesh installation](https://trimesh.org/install.html).

Playwright is unnecessary for Python-only checkpoint preparation and for prepared
browser playback. Keep browser capture optional and explicit. Pydantic is needed
by Agent's typed contracts; packaging is used by Kit's requirement inspector.
Neither belongs in the Core base. Keep dev/test/build packages outside runtime.

## System dependencies

FFmpeg and ffprobe are external executable requirements for probing/export, not
Python dependencies. Current export uses libx264 and AAC. Base scene construction
and still rendering must work without those executables; requesting audio probing
or MP4 export must produce the current actionable missing-tool error.

Native extras have separate system requirements: working EGL/OpenGL for ModernGL
and PyVista rendering, font/native libraries for Skia, and a matching browser
revision for Playwright preparation. Presence of a Python distribution is not a
successful native probe. Never install drivers or download browsers during imports,
validation, ordinary playback or capability listing.

## Proposed installation model

Keep exactly three primary distributions. Use focused modules plus extras, not a
new wheel for each domain. The following are V2 requirements, not available commands
implemented by this proposal.

| Capability | Core requirements | Kit / Agent forwarding and behavior |
| --- | --- | --- |
| Base | Pillow only | Kit adds packaging; Agent adds Pydantic through Kit; no native optional engines |
| `3d` | PyVista/VTK via PyVista, initially tested 0.49.x | Both upper layers forward the extra for viewport use |
| `skia` | Current Skia 144 bounds and NumPy | Forward; explicit backend/native text |
| `gpu` | Current ModernGL/glcontext/NumPy bounds | Forward; native probe separate from metadata |
| `effects` | NumPy | Forward for portable reference effects/procedural content |
| `cad` | build123d with existing Python marker **and 3D conversion requirements** | Forward; current CAD-to-ArchMesh path needs PyVista even though CAD objects are prepared before rendering |
| `geometry`, `geometry-advanced` | Current operation-specific mesh helpers and 3D conversion requirements | Forward; do not advertise every operation in a Trimesh-only environment |
| `equations` | Matplotlib MathText adapter | Forward; lazy only when equation measurement/rendering is requested |
| `coding` | No mandatory Core syntax dependency | Pygments becomes Kit's direct optional requirement after domain move; Agent forwards through Kit |
| `web` | Generic prepared-source playback uses Pillow | Playwright becomes Kit's direct optional preparation requirement; Agent forwards through Kit |
| `maps` | Generic primitives/images | Kit owns optional NumPy map implementation; Agent forwards |
| `playground` compatibility alias | No execution during playback | Retain coding+web aggregate alias for compatibility; document coding-only install for Python preparation |
| `chess` | Removed in V2 | No forwarding or supported chess starter; frozen V1 route documented |

For initial packaging extraction keep existing tested native versions; propose a
PyVista `>=0.49.1,<0.50` capability bound until another minor passes its matrix.
That upper bound is a V2 compatibility choice, not the current manifest. Keep
Python `>=3.12` and the existing CAD `<3.15` guard; initial execution evidence is
only Python 3.12/Linux. Certify 3.12 and 3.13 base/native lanes before release;
additional interpreters/platforms require their own evidence. Do not widen Skia's
constraint while its loader explicitly accepts only version 144.

Core lazy root exports must preserve `__all__`, `dir()`, supported import aliases,
type-checking discoverability and CLI entrypoints without eagerly loading domains.
Capabilities report installed versions and declared requirements without imports;
explicit probes may initialize native resources and must close them.

## Import boundaries and cycles

Observed cross-layer edges: Kit uses Core in 28 source modules; Agent uses Kit in
6 and directly uses Core in 4 (`cli`, `examples`, `media`, `project`). No Core → Kit
or Core → Agent edge and no cross-layer private-symbol import was found. Direct
Agent → Core calls are public today, not a circular dependency; the V2 ownership
change moves render operations to Kit services to eliminate duplicated plumbing.
The generated delivery script also contains a Core progress import inside a
string, illustrating the limits of a plain import graph.

The eager direct-reference graph has 405 edges and no cycle after type-only guards
and function bodies are excluded. The 558-edge all-reference graph includes lazy
and type-only coupling. Its large Core SCC and four-module geometry SCC must not
be reported as proven eager runtime failures. String-based workers and implicit
package initializers require separate review.

## Reproduction and validation

Use AST parsing of the tracked package roots for module/import inventories. Resolve
relative imports; annotate imports inside functions and type-checking guards.
Evaluate installed requirements with `packaging.Requirement.marker` for the actual
platform. Compare source manifests, wheel METADATA and the lock independently.

M1 clean-wheel lanes: base, 3D, Skia, GPU, CAD, geometry, geometry-advanced,
equations, Kit base, Agent base, Kit coding and Kit web. Test off-network playback
after preparation. Validate missing-dependency errors with both isolated minimal
environments and blocked-import probes; the latter alone is not an installation test.
No advisory/CVE scan or legal license review was performed. Preserve bundled
license/attribution records and record upstream metadata during release review.

<!-- GENERATED_IMPORT_LEDGER -->

## Complete package import ledger

Generated from all 145 tracked package modules. `E` = import statement outside
a function and outside a type-only guard; `L` = function-local/deferred import;
`T` = type-only import. Conditional runtime branches other than TYPE_CHECKING
are conservatively E. Line numbers refer to the audited source commit.
Every static import statement is included, including standard-library imports.
Relative module names are resolved; this does not execute an import.

Internal direct-reference graph: **145 nodes, 405 eager edges, 558 all-reference edges**.

Dynamic native loads are additional to this ledger: `_require()` loads build123d,
Trimesh and operation-specific helper modules; Core factories import selected
backends; project factories and subprocess worker module strings are resolved
at runtime. See the source/worker and preparation contracts in the audit.

### External import sites (non-stdlib)

| Module root | Source sites with classification |
| --- | --- |
| `OCP` | [src/faceless_champ/arch/cad.py](../../src/faceless_champ/arch/cad.py#L40) (L); [src/faceless_champ/arch/cad.py](../../src/faceless_champ/arch/cad.py#L80) (L); [src/faceless_champ/arch/cad.py](../../src/faceless_champ/arch/cad.py#L81) (L); [src/faceless_champ/arch/cad.py](../../src/faceless_champ/arch/cad.py#L82) (L); [src/faceless_champ/arch/cad.py](../../src/faceless_champ/arch/cad.py#L83) (L); [src/faceless_champ/arch/cad.py](../../src/faceless_champ/arch/cad.py#L84) (L) |
| `PIL` | [facelesschamp-agent/src/facelesschamp_agent/models.py](../../facelesschamp-agent/src/facelesschamp_agent/models.py#L72) (L); [facelesschamp-kit/src/facelesschamp_kit/blocks/whiteboard.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/whiteboard.py#L7) (E); [facelesschamp-kit/src/facelesschamp_kit/themes.py](../../facelesschamp-kit/src/facelesschamp_kit/themes.py#L7) (E); [facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/style.py](../../facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/style.py#L10) (E); [src/faceless_champ/_compositor.py](../../src/faceless_champ/_compositor.py#L5) (E); [src/faceless_champ/_cpu_device.py](../../src/faceless_champ/_cpu_device.py#L6) (E); [src/faceless_champ/_cpu_device.py](../../src/faceless_champ/_cpu_device.py#L81) (L); [src/faceless_champ/_effects_cpu.py](../../src/faceless_champ/_effects_cpu.py#L6) (E); [src/faceless_champ/_effects_cpu.py](../../src/faceless_champ/_effects_cpu.py#L164) (L); [src/faceless_champ/_portable.py](../../src/faceless_champ/_portable.py#L6) (E); [src/faceless_champ/_render_state.py](../../src/faceless_champ/_render_state.py#L7) (E); [src/faceless_champ/_surface_raster.py](../../src/faceless_champ/_surface_raster.py#L8) (E); [src/faceless_champ/arch/clip.py](../../src/faceless_champ/arch/clip.py#L9) (E); [src/faceless_champ/arch/clip.py](../../src/faceless_champ/arch/clip.py#L410) (L); [src/faceless_champ/arch/model.py](../../src/faceless_champ/arch/model.py#L9) (E); [src/faceless_champ/arch/rendering.py](../../src/faceless_champ/arch/rendering.py#L4) (E); [src/faceless_champ/backends/_arch_worker.py](../../src/faceless_champ/backends/_arch_worker.py#L54) (L); [src/faceless_champ/backends/_gl/device.py](../../src/faceless_champ/backends/_gl/device.py#L8) (E); [src/faceless_champ/backends/_native.py](../../src/faceless_champ/backends/_native.py#L31) (L); [src/faceless_champ/backends/skia.py](../../src/faceless_champ/backends/skia.py#L7) (E); [src/faceless_champ/charts/__init__.py](../../src/faceless_champ/charts/__init__.py#L8) (E); [src/faceless_champ/charts/drawing.py](../../src/faceless_champ/charts/drawing.py#L7) (E); [src/faceless_champ/chess.py](../../src/faceless_champ/chess.py#L16) (E); [src/faceless_champ/chess_assets.py](../../src/faceless_champ/chess_assets.py#L8) (E); [src/faceless_champ/coding.py](../../src/faceless_champ/coding.py#L13) (E); [src/faceless_champ/coding_workspace.py](../../src/faceless_champ/coding_workspace.py#L12) (E); [src/faceless_champ/colors.py](../../src/faceless_champ/colors.py#L6) (E); [src/faceless_champ/components.py](../../src/faceless_champ/components.py#L284) (L); [src/faceless_champ/components.py](../../src/faceless_champ/components.py#L285) (L); [src/faceless_champ/effects.py](../../src/faceless_champ/effects.py#L6) (E); [src/faceless_champ/flow/clip.py](../../src/faceless_champ/flow/clip.py#L11) (E); [src/faceless_champ/flow/design.py](../../src/faceless_champ/flow/design.py#L11) (E); [src/faceless_champ/flow/drawing.py](../../src/faceless_champ/flow/drawing.py#L8) (E); [src/faceless_champ/flow/model.py](../../src/faceless_champ/flow/model.py#L8) (E); [src/faceless_champ/gradients.py](../../src/faceless_champ/gradients.py#L8) (E); [src/faceless_champ/indicators.py](../../src/faceless_champ/indicators.py#L6) (E); [src/faceless_champ/maps.py](../../src/faceless_champ/maps.py#L10) (E); [src/faceless_champ/motion.py](../../src/faceless_champ/motion.py#L5) (E); [src/faceless_champ/os_ui/clip.py](../../src/faceless_champ/os_ui/clip.py#L159) (L); [src/faceless_champ/os_ui/drawing.py](../../src/faceless_champ/os_ui/drawing.py#L7) (E); [src/faceless_champ/os_ui/model.py](../../src/faceless_champ/os_ui/model.py#L252) (L); [src/faceless_champ/playground/model.py](../../src/faceless_champ/playground/model.py#L149) (L); [src/faceless_champ/playground/playback.py](../../src/faceless_champ/playground/playback.py#L10) (E); [src/faceless_champ/playground/prepare.py](../../src/faceless_champ/playground/prepare.py#L141) (L); [src/faceless_champ/preview.py](../../src/faceless_champ/preview.py#L12) (E); [src/faceless_champ/preview.py](../../src/faceless_champ/preview.py#L13) (E); [src/faceless_champ/procedural.py](../../src/faceless_champ/procedural.py#L3) (E); [src/faceless_champ/renderer.py](../../src/faceless_champ/renderer.py#L13) (E); [src/faceless_champ/renderer.py](../../src/faceless_champ/renderer.py#L14) (E); [src/faceless_champ/surfaces.py](../../src/faceless_champ/surfaces.py#L7) (E); [src/faceless_champ/surfaces.py](../../src/faceless_champ/surfaces.py#L8) (E); [src/faceless_champ/typography.py](../../src/faceless_champ/typography.py#L5) (E); [src/faceless_champ/web/clip.py](../../src/faceless_champ/web/clip.py#L7) (E); [src/faceless_champ/web/model.py](../../src/faceless_champ/web/model.py#L139) (L); [src/faceless_champ/web/model.py](../../src/faceless_champ/web/model.py#L159) (L) |
| `chess` | [src/faceless_champ/chess.py](../../src/faceless_champ/chess.py#L145) (L); [src/faceless_champ/chess.py](../../src/faceless_champ/chess.py#L303) (L) |
| `matplotlib` | [src/faceless_champ/renderer.py](../../src/faceless_champ/renderer.py#L856) (L); [src/faceless_champ/renderer.py](../../src/faceless_champ/renderer.py#L857) (L); [src/faceless_champ/renderer.py](../../src/faceless_champ/renderer.py#L858) (L); [src/faceless_champ/renderer.py](../../src/faceless_champ/renderer.py#L896) (L); [src/faceless_champ/renderer.py](../../src/faceless_champ/renderer.py#L897) (L); [src/faceless_champ/renderer.py](../../src/faceless_champ/renderer.py#L898) (L); [src/faceless_champ/renderer.py](../../src/faceless_champ/renderer.py#L899) (L); [src/faceless_champ/renderer.py](../../src/faceless_champ/renderer.py#L900) (L) |
| `moderngl` | [src/faceless_champ/backends/moderngl.py](../../src/faceless_champ/backends/moderngl.py#L25) (L) |
| `numpy` | [src/faceless_champ/_effects_cpu.py](../../src/faceless_champ/_effects_cpu.py#L13) (L); [src/faceless_champ/arch/blueprint.py](../../src/faceless_champ/arch/blueprint.py#L40) (L); [src/faceless_champ/arch/cad.py](../../src/faceless_champ/arch/cad.py#L71) (L); [src/faceless_champ/arch/cad.py](../../src/faceless_champ/arch/cad.py#L141) (L); [src/faceless_champ/arch/camera.py](../../src/faceless_champ/arch/camera.py#L19) (L); [src/faceless_champ/arch/camera.py](../../src/faceless_champ/arch/camera.py#L34) (L); [src/faceless_champ/arch/camera.py](../../src/faceless_champ/arch/camera.py#L50) (L); [src/faceless_champ/arch/camera.py](../../src/faceless_champ/arch/camera.py#L56) (L); [src/faceless_champ/arch/clip.py](../../src/faceless_champ/arch/clip.py#L356) (L); [src/faceless_champ/arch/clip.py](../../src/faceless_champ/arch/clip.py#L430) (L); [src/faceless_champ/arch/mechanical.py](../../src/faceless_champ/arch/mechanical.py#L37) (L); [src/faceless_champ/arch/mechanical.py](../../src/faceless_champ/arch/mechanical.py#L52) (L); [src/faceless_champ/arch/mesh.py](../../src/faceless_champ/arch/mesh.py#L17) (L); [src/faceless_champ/arch/mesh.py](../../src/faceless_champ/arch/mesh.py#L41) (L); [src/faceless_champ/arch/mesh.py](../../src/faceless_champ/arch/mesh.py#L120) (L); [src/faceless_champ/arch/mesh.py](../../src/faceless_champ/arch/mesh.py#L170) (L); [src/faceless_champ/arch/model.py](../../src/faceless_champ/arch/model.py#L76) (L); [src/faceless_champ/arch/model.py](../../src/faceless_champ/arch/model.py#L138) (L); [src/faceless_champ/arch/rendering.py](../../src/faceless_champ/arch/rendering.py#L3) (E); [src/faceless_champ/backends/_native.py](../../src/faceless_champ/backends/_native.py#L20) (L); [src/faceless_champ/maps.py](../../src/faceless_champ/maps.py#L27) (L); [src/faceless_champ/renderer.py](../../src/faceless_champ/renderer.py#L855) (L); [src/faceless_champ/renderer.py](../../src/faceless_champ/renderer.py#L895) (L) |
| `packaging` | [facelesschamp-kit/src/facelesschamp_kit/dependencies.py](../../facelesschamp-kit/src/facelesschamp_kit/dependencies.py#L7) (E) |
| `playwright` | [src/faceless_champ/playground/prepare.py](../../src/faceless_champ/playground/prepare.py#L36) (L); [src/faceless_champ/web/capture.py](../../src/faceless_champ/web/capture.py#L124) (L) |
| `pydantic` | [facelesschamp-agent/src/facelesschamp_agent/cli.py](../../facelesschamp-agent/src/facelesschamp_agent/cli.py#L15) (E); [facelesschamp-agent/src/facelesschamp_agent/models.py](../../facelesschamp-agent/src/facelesschamp_agent/models.py#L5) (E) |
| `pygments` | [src/faceless_champ/coding.py](../../src/faceless_champ/coding.py#L209) (L); [src/faceless_champ/coding.py](../../src/faceless_champ/coding.py#L210) (L) |
| `pyvista` | [src/faceless_champ/arch/model.py](../../src/faceless_champ/arch/model.py#L61) (L) |
| `skia` | [src/faceless_champ/backends/_native.py](../../src/faceless_champ/backends/_native.py#L8) (L) |

### faceless_champ

[src/faceless_champ/__init__.py](../../src/faceless_champ/__init__.py)

```text
E L3: faceless_champ.animation import Animation, BounceIn, ChartReveal, Draw, FadeIn, FadeOut, PopIn, PopOut, Pulse, Shake, SlideIn, SlideOut, SpinIn, Typewriter, Wiggle, Write, ZoomIn, ZoomOut, ease_in, ease_out, linear, smooth
E L27: faceless_champ.backends.moderngl import ModernGLRenderer
E L28: faceless_champ.backends.skia import SkiaRenderer
E L29: faceless_champ.charts import Axis, BarChart, Chart, ChartStyle, Heatmap, Histogram, LineChart, NetworkGraph, PieChart, RankedBarChart, SankeyChart, ScatterPlot, VectorField
E L44: faceless_champ.cli import main as main
E L45: faceless_champ.colors import COLOR_SCHEMES, ColorScheme, with_alpha
E L46: faceless_champ.components import Arrow, Canvas, Circle, Component, Ellipse, Equation, Icon, Image, ImageSlot, Line, Number, Polyline, Rectangle, Square, Text, Triangle
E L64: faceless_champ.effects import Bloom, ChromaticAberration, Distortion, EffectStack, GaussianBlur, LightSweep, OuterGlow
E L65: faceless_champ.export import ExportSettings, render
E L66: faceless_champ.flags import Flag, flag_path, supported_flags
E L67: faceless_champ.gpu import GPUOptions, renderer_capabilities
E L68: faceless_champ.gradients import GradientStop, LinearGradient, RadialGradient
E L69: faceless_champ.layout import Bounds, Group
E L70: faceless_champ.maps import EarthMap, OutlineMap, SatelliteMap, supported_countries
E L71: faceless_champ.masks import PathMask
E L72: faceless_champ.narration import CueScene
E L73: faceless_champ.paths import PathData, VectorPath
E L74: faceless_champ.preview import StoryboardSample, render_storyboard, save_frame
E L75: faceless_champ.procedural import ParticleField, ProceduralBackground
E L76: faceless_champ.progress import ExportProgress
E L77: faceless_champ.renderer import PillowRenderer, Renderer, create_renderer, rendering_identity, validate_composition
E L78: faceless_champ.spring import Spring
E L79: faceless_champ.subtitles import Captions, SubtitleCue, SubtitleTrack
E L80: faceless_champ.surfaces import ShadowStyle, Surface, card_content_bounds, card_surface, dot_grid, gradient_surface
E L81: faceless_champ.timeline import Grid, Layer, Scene, Sequence
E L82: faceless_champ.transitions import DirectionalWipe, LuminanceWipe, ZoomBlurTransition
E L83: faceless_champ.typography import CLEAN_FLOW_FONT, fit_text
E L202: faceless_champ.indicators import Checkmark, Countdown, Gauge, LoadingDots, ProgressBar, ProgressRing
E L203: faceless_champ.masks import CircleMask, RectangleMask, ShapeMask, Wipe
E L204: faceless_champ.scheduling import Repeat, Stagger, Succession
E L222: faceless_champ.coding import CodeReveal, CodeTheme, CodingChamp
E L226: faceless_champ.coding_workspace import CodeWindow, CodeWorkspaceDesign
E L230: faceless_champ.chess import ChessAssets, ChessChamp, ChessScript, ChessTheme
E L234: faceless_champ.playground import CanvasItem, CodeCheckpoint, CodeEditor, EditTimeline, EventBinding, PlaygroundCanvas, PlaygroundError, PlaygroundOutput, PlaygroundScript, PreparedPlayground, ValueBinding, prepare_playground
E L264: faceless_champ.flow import FlowChamp, FlowDataError, FlowDesign, FlowEdge, FlowGraph, FlowNode, FlowPort, FlowScript, FlowTheme, FlowVisual
E L290: faceless_champ.arch import ArchCamera, ArchChamp, ArchDataError, ArchDimension, ArchLabel, ArchMesh, ArchPart, ArchScript, ArchStyle
```

### faceless_champ.__main__

[src/faceless_champ/__main__.py](../../src/faceless_champ/__main__.py)

```text
E L1: faceless_champ.cli import main
```

### faceless_champ._composition_plan

[src/faceless_champ/_composition_plan.py](../../src/faceless_champ/_composition_plan.py)

```text
E L3: dataclasses import dataclass
E L4: math import nextafter
L L22: faceless_champ.timeline import Scene
L L40: faceless_champ.timeline import Grid, Layer, Sequence
```

### faceless_champ._compositor

[src/faceless_champ/_compositor.py](../../src/faceless_champ/_compositor.py)

```text
E L3: math
E L5: PIL import Image, ImageChops, ImageDraw
E L7: faceless_champ._composition_plan import composition_plan, fit
E L8: faceless_champ._portable import guard_size
E L9: faceless_champ._render_state import component_ink_box, entry_geometry, ink_box, transformed_box
E L10: faceless_champ.layout import Bounds, Group
E L11: faceless_champ.motion import IDENTITY
E L12: faceless_champ.surfaces import _shadow_padding
E L13: faceless_champ.timeline import Scene, Sequence
L L54: faceless_champ.backends._native import image_to_pillow, load_skia
L L55: faceless_champ.backends._skia_paint import path_data
```

### faceless_champ._cpu_device

[src/faceless_champ/_cpu_device.py](../../src/faceless_champ/_cpu_device.py)

```text
E L3: math
E L4: contextlib import contextmanager
E L6: PIL import Image, ImageChops, ImageFilter
E L8: faceless_champ._portable import guard_size
E L9: faceless_champ.layout import Bounds
E L10: faceless_champ.motion import IDENTITY, inverse, multiply
L L39: faceless_champ._render_state import transformed_box
L L69: faceless_champ._effects_cpu import content
L L75: faceless_champ._effects_cpu import halos
L L81: PIL import ImageColor
L L101: faceless_champ._effects_cpu import crossfade
L L109: faceless_champ._compositor import density
L L110: faceless_champ._effects_cpu import background
L L111: faceless_champ._render_state import component_ink_box
```

### faceless_champ._effects_cpu

[src/faceless_champ/_effects_cpu.py](../../src/faceless_champ/_effects_cpu.py)

```text
E L3: math
E L4: functools import lru_cache
E L6: PIL import Image, ImageColor
E L8: faceless_champ.effects import _phase
L L13: numpy as np
L L159: faceless_champ.procedural import ParticleField, particle_data
L L164: PIL import ImageDraw
L L197: faceless_champ.transitions import LuminanceWipe, ZoomBlurTransition
```

### faceless_champ._portable

[src/faceless_champ/_portable.py](../../src/faceless_champ/_portable.py)

```text
E L3: math
E L4: itertools import pairwise
E L6: PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFilter
E L8: faceless_champ.gradients import LinearGradient, RadialGradient
L L19: faceless_champ._surface_raster import _paint
L L26: faceless_champ._surface_raster import _coverage_replace, _extend_edges
L L27: faceless_champ.surfaces import _shadow_padding
L L69: faceless_champ.components import Circle, Ellipse, Line, Polyline, Triangle
L L70: faceless_champ.paths import VectorPath
L L109: copy import copy
L L111: faceless_champ.renderer import PillowRenderer
```

### faceless_champ._render_state

[src/faceless_champ/_render_state.py](../../src/faceless_champ/_render_state.py)

```text
E L3: math
E L4: collections import OrderedDict
E L5: copy import copy
E L7: PIL import Image
E L9: faceless_champ.components import Arrow, Shape, Text
E L10: faceless_champ.layout import Bounds, Group
E L11: faceless_champ.motion import matrix, multiply, point, style_value
L L25: faceless_champ.surfaces import Surface
L L74: faceless_champ.procedural import ParticleField
L L85: faceless_champ.surfaces import _shadow_padding
L L98: faceless_champ._compositor import density
L L111: faceless_champ._composition_plan import composition_plan
L L112: faceless_champ.timeline import Sequence
L L131: faceless_champ._composition_plan import fit
```

### faceless_champ._surface_raster

[src/faceless_champ/_surface_raster.py](../../src/faceless_champ/_surface_raster.py)

```text
E L3: math
E L4: array import array
E L5: contextlib import ExitStack, closing
E L6: itertools import pairwise
E L8: PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFilter, ImageMath, ImageOps
E L10: faceless_champ.gradients import LinearGradient, _linear_coefficients, _parameter, _sample
```

### faceless_champ.animation

[src/faceless_champ/animation.py](../../src/faceless_champ/animation.py)

```text
E L3: __future__ import annotations
E L5: collections.abc import Callable
E L6: dataclasses import dataclass
E L7: typing import Self
E L9: faceless_champ.components import Component, Equation, Number, Shape, Text, finite
L L43: faceless_champ.timeline import _validate_animated_value
L L52: faceless_champ.motion import rgba
L L65: faceless_champ.motion import rgba
L L70: faceless_champ.motion import rgba
L L99: faceless_champ.charts import Chart
L L109: faceless_champ.indicators import Countdown
L L333: faceless_champ.charts import Chart
```

### faceless_champ.arch

[src/faceless_champ/arch/__init__.py](../../src/faceless_champ/arch/__init__.py)

```text
E L3: faceless_champ.arch.blueprint import blueprint_from_cad
E L4: faceless_champ.arch.cad import TessellationOptions, mesh_from_cad, parts_from_cad, read_step
E L5: faceless_champ.arch.camera import ArchCamera
E L6: faceless_champ.arch.clip import ArchChamp, validate_design
E L7: faceless_champ.arch.dependencies import geometry_capabilities
E L8: faceless_champ.arch.mechanical import slider_crank_pose
E L9: faceless_champ.arch.mesh import boolean_mesh, inspect_mesh, parts_from_trimesh_scene, repair_mesh, simplify_mesh, to_trimesh
E L10: faceless_champ.arch.model import ArchDataError, ArchDimension, ArchLabel, ArchMesh, ArchPart, ArchStyle
E L11: faceless_champ.arch.script import ArchScript
```

### faceless_champ.arch.blueprint

[src/faceless_champ/arch/blueprint.py](../../src/faceless_champ/arch/blueprint.py)

```text
E L3: hashlib
E L4: json
E L5: math
E L6: dataclasses import asdict
E L7: itertools import pairwise
E L9: faceless_champ.arch.cad import _detached, _engine, _unit_scale, parts_from_cad
E L10: faceless_champ.arch.camera import ArchCamera, part_matrix
E L11: faceless_champ.arch.dependencies import _versions
E L12: faceless_champ.arch.model import ArchDataError, ArchDimension, _format_dimension, number
L L40: numpy as np
L L42: faceless_champ.components import Arrow, Polyline, Rectangle, Text
L L43: faceless_champ.layout import Group
```

### faceless_champ.arch.cad

[src/faceless_champ/arch/cad.py](../../src/faceless_champ/arch/cad.py)

```text
E L7: hashlib
E L8: math
E L9: sys
E L10: dataclasses import asdict, dataclass
E L11: pathlib import Path
E L13: faceless_champ.arch.dependencies import _require, _versions
E L14: faceless_champ.arch.model import ArchDataError, ArchMesh, ArchPart, number
L L40: OCP.BRepBuilderAPI import BRepBuilderAPI_Copy
L L71: numpy as np
L L80: OCP.BRep import BRep_Tool
L L81: OCP.BRepMesh import BRepMesh_IncrementalMesh
L L82: OCP.BRepTools import BRepTools
L L83: OCP.TopAbs import TopAbs_Orientation
L L84: OCP.TopLoc import TopLoc_Location
L L141: numpy as np
L L180: dataclasses import replace
L L200: faceless_champ.arch.mechanical import _euler_xyz
L L241: faceless_champ.arch.cad_models import validate_preset
L L263: faceless_champ.arch.cad_models import CAD_PRESETS, validate_preset
```

### faceless_champ.arch.cad_models

[src/faceless_champ/arch/cad_models.py](../../src/faceless_champ/arch/cad_models.py)

```text
E L7: inspect
E L8: math
E L9: copy import deepcopy
E L11: faceless_champ.arch.cad import _engine
E L12: faceless_champ.arch.model import ArchDataError, number
```

### faceless_champ.arch.camera

[src/faceless_champ/arch/camera.py](../../src/faceless_champ/arch/camera.py)

```text
E L3: math
E L4: dataclasses import dataclass
E L6: faceless_champ.arch.model import ArchDataError, number, vector
L L19: numpy as np
L L34: numpy as np
L L50: numpy as np
L L56: numpy as np
```

### faceless_champ.arch.clip

[src/faceless_champ/arch/clip.py](../../src/faceless_champ/arch/clip.py)

```text
E L3: hashlib
E L4: json
E L5: math
E L6: copy import deepcopy
E L7: dataclasses import asdict
E L9: PIL import Image, ImageDraw
E L11: faceless_champ.components import Component
E L12: faceless_champ.typography import load_font
E L13: faceless_champ.arch.camera import ArchCamera, project, world
E L14: faceless_champ.arch.model import ArchDataError, ArchDimension, ArchLabel, ArchMesh, ArchPart, ArchStyle, _format_dimension, construct, number, pyvista, text, vector
E L28: faceless_champ.arch.script import ArchScript
L L55: faceless_champ.arch.cad import _unit_scale, _validate_source
L L267: pathlib import Path
L L288: faceless_champ.arch.cad import _parts_from_source
L L350: faceless_champ.animation import smooth
L L356: numpy as np
L L358: faceless_champ.arch.mechanical import _poses
L L410: PIL import ImageColor
L L430: numpy as np
L L441: faceless_champ.arch.mechanical import _travel_bound
L L551: faceless_champ.arch.rendering import ArchSession
```

### faceless_champ.arch.dependencies

[src/faceless_champ/arch/dependencies.py](../../src/faceless_champ/arch/dependencies.py)

```text
E L3: importlib import import_module
E L4: importlib.metadata import PackageNotFoundError, version
E L6: faceless_champ.arch.model import ArchDataError
L L46: faceless_champ.arch.cad import _engine, mesh_from_cad
L L52: faceless_champ.arch.mesh import inspect_mesh
```

### faceless_champ.arch.mechanical

[src/faceless_champ/arch/mechanical.py](../../src/faceless_champ/arch/mechanical.py)

```text
E L3: math
L L24: faceless_champ.arch.model import ArchDataError, number
L L37: numpy as np
L L52: numpy as np
```

### faceless_champ.arch.mesh

[src/faceless_champ/arch/mesh.py](../../src/faceless_champ/arch/mesh.py)

```text
E L7: faceless_champ.arch.dependencies import _require, _versions
E L8: faceless_champ.arch.model import ArchDataError, ArchMesh, ArchPart, number
L L17: numpy as np
L L41: numpy as np
L L120: numpy as np
L L170: numpy as np
```

### faceless_champ.arch.model

[src/faceless_champ/arch/model.py](../../src/faceless_champ/arch/model.py)

```text
E L3: hashlib
E L4: json
E L5: math
E L6: dataclasses import dataclass, fields
E L7: pathlib import Path
E L9: PIL import ImageColor
L L61: pyvista as pv
L L76: numpy as np
L L138: numpy as np
```

### faceless_champ.arch.rendering

[src/faceless_champ/arch/rendering.py](../../src/faceless_champ/arch/rendering.py)

```text
E L3: numpy as np
E L4: PIL import Image
E L6: faceless_champ.arch.camera import part_matrix
E L7: faceless_champ.arch.model import ArchDataError, pyvista
L L178: math
```

### faceless_champ.arch.script

[src/faceless_champ/arch/script.py](../../src/faceless_champ/arch/script.py)

```text
E L3: copy import deepcopy
E L4: dataclasses import dataclass
E L6: faceless_champ.arch.camera import ArchCamera
E L7: faceless_champ.arch.model import ArchDataError, color, construct, number, vector
L L164: faceless_champ.arch.mechanical import slider_crank_pose
L L181: dataclasses import asdict
```

### faceless_champ.audio

[src/faceless_champ/audio.py](../../src/faceless_champ/audio.py)

```text
E L3: json
E L4: shutil
E L5: subprocess
E L6: dataclasses import dataclass, field
E L7: pathlib import Path
E L9: faceless_champ.components import finite
```

### faceless_champ.backends

[src/faceless_champ/backends/__init__.py](../../src/faceless_champ/backends/__init__.py)

```text
(no static import statements)
```

### faceless_champ.backends._arch_worker

[src/faceless_champ/backends/_arch_worker.py](../../src/faceless_champ/backends/_arch_worker.py)

```text
E L10: pickle
E L11: struct
E L12: subprocess
E L13: sys
E L14: collections import OrderedDict
E L15: contextlib import suppress
L L54: PIL import Image
L L56: faceless_champ.arch import ArchDataError
L L85: faceless_champ.renderer import PillowRenderer
```

### faceless_champ.backends._auto

[src/faceless_champ/backends/_auto.py](../../src/faceless_champ/backends/_auto.py)

```text
L L23: faceless_champ.renderer import create_renderer, rendering_identity
```

### faceless_champ.backends._gl

[src/faceless_champ/backends/_gl/__init__.py](../../src/faceless_champ/backends/_gl/__init__.py)

```text
(no static import statements)
```

### faceless_champ.backends._gl.device

[src/faceless_champ/backends/_gl/device.py](../../src/faceless_champ/backends/_gl/device.py)

```text
E L3: math
E L4: collections import OrderedDict
E L5: contextlib import contextmanager
E L6: importlib.resources import files
E L8: PIL import Image, ImageColor
E L10: faceless_champ._portable import guard_size
E L11: faceless_champ.effects import _phase
E L12: faceless_champ.layout import Bounds
E L13: faceless_champ.motion import IDENTITY
L L122: faceless_champ._effects_cpu import numpy
L L227: faceless_champ._effects_cpu import kernel
L L328: faceless_champ.transitions import LuminanceWipe, ZoomBlurTransition
L L351: faceless_champ.components import Circle, Ellipse, Rectangle
L L352: faceless_champ.gradients import LinearGradient, RadialGradient
L L353: faceless_champ.motion import rgba
L L354: faceless_champ.procedural import ParticleField, ProceduralBackground, particle_data
L L355: faceless_champ.surfaces import Surface
```

### faceless_champ.backends._native

[src/faceless_champ/backends/_native.py](../../src/faceless_champ/backends/_native.py)

```text
E L3: importlib.metadata import version
L L8: skia
L L20: numpy as np
L L31: PIL import Image
```

### faceless_champ.backends._raster_adapter

[src/faceless_champ/backends/_raster_adapter.py](../../src/faceless_champ/backends/_raster_adapter.py)

```text
E L3: contextlib import contextmanager
E L4: functools import lru_cache
E L6: faceless_champ.renderer import PillowRenderer
L L12: ctypes
L L35: ctypes
L L61: faceless_champ.components import Image
L L62: faceless_champ.subtitles import Captions
L L79: faceless_champ.arch import ArchChamp
L L80: faceless_champ.components import Text
L L81: faceless_champ.paths import VectorPath
L L87: faceless_champ.backends._arch_worker import ArchWorker
L L114: math
L L116: faceless_champ._portable import guard_size
L L117: faceless_champ.components import Text
L L118: faceless_champ.backends._native import image_to_pillow, load_skia
L L119: faceless_champ.backends._skia_paint import draw_shape
L L124: faceless_champ.backends._skia_text import TextSession
L L146: faceless_champ.backends._skia_text import text_size
```

### faceless_champ.backends._skia_paint

[src/faceless_champ/backends/_skia_paint.py](../../src/faceless_champ/backends/_skia_paint.py)

```text
E L3: math
E L5: faceless_champ.components import Arrow, Circle, Ellipse, Line, Polyline, Rectangle, Triangle
E L6: faceless_champ.gradients import LinearGradient, RadialGradient
E L7: faceless_champ.motion import rgba
E L8: faceless_champ.paths import VectorPath
L L116: faceless_champ.layout import Bounds
L L158: faceless_champ.layout import Bounds
L L159: faceless_champ.surfaces import _shadow_padding
```

### faceless_champ.backends._skia_text

[src/faceless_champ/backends/_skia_text.py](../../src/faceless_champ/backends/_skia_text.py)

```text
E L3: math
E L4: unicodedata
E L5: collections import OrderedDict
E L6: functools import lru_cache
E L7: pathlib import Path
E L9: faceless_champ.components import Number
E L10: faceless_champ.motion import rgba
E L11: faceless_champ.typography import DEFAULT_FONT, load_font
E L12: faceless_champ.backends._native import load_skia
L L135: faceless_champ.components import Text
```

### faceless_champ.backends.moderngl

[src/faceless_champ/backends/moderngl.py](../../src/faceless_champ/backends/moderngl.py)

```text
E L3: hashlib
E L4: sys
E L5: threading
E L6: importlib.resources import files
E L8: faceless_champ._render_state import ByteCache
E L9: faceless_champ.gpu import GPUOptions
E L10: faceless_champ.timeline import Scene
L L25: moderngl
L L27: faceless_champ._compositor import Compositor
L L28: faceless_champ.backends._gl.device import GLDevice
L L29: faceless_champ.backends._raster_adapter import PillowRasterAdapter
L L113: faceless_champ._composition_plan import composition_plan
L L130: math
L L132: faceless_champ._portable import guard_size
```

### faceless_champ.backends.skia

[src/faceless_champ/backends/skia.py](../../src/faceless_champ/backends/skia.py)

```text
E L3: math
E L4: time as clock
E L5: contextlib import contextmanager
E L7: PIL import Image as PILImage
E L9: faceless_champ._portable import guard_size
E L10: faceless_champ._render_state import ByteCache, composition_frame, entry_geometry, ink_box, transformed_box
E L11: faceless_champ.components import Image, Shape, Text, finite
E L12: faceless_champ.layout import Bounds, Group
E L13: faceless_champ.subtitles import Captions
E L14: faceless_champ.surfaces import Surface, _shadow_padding
E L15: faceless_champ.timeline import Scene
E L16: faceless_champ.backends._native import image_from_pillow, image_to_pillow, load_skia
E L17: faceless_champ.backends._raster_adapter import PillowRasterAdapter
E L18: faceless_champ.backends._skia_paint import color, draw_shape, draw_surface, path_data
E L19: faceless_champ.backends._skia_text import TextSession
L L119: faceless_champ.effects import needs_compositor
L L124: faceless_champ._compositor import Compositor
L L125: faceless_champ._cpu_device import CPUDevice
L L312: faceless_champ.motion import rgba
```

### faceless_champ.charts

[src/faceless_champ/charts/__init__.py](../../src/faceless_champ/charts/__init__.py)

```text
E L3: collections.abc import Mapping
E L4: copy import deepcopy
E L5: dataclasses import dataclass, field
E L6: pathlib import Path
E L8: PIL import ImageColor
E L10: faceless_champ.colors import ColorScheme
E L11: faceless_champ.components import Component, finite
E L12: faceless_champ.charts.scales import Axis, domain, graph_positions, histogram
```

### faceless_champ.charts.drawing

[src/faceless_champ/charts/drawing.py](../../src/faceless_champ/charts/drawing.py)

```text
E L3: math
E L4: functools import lru_cache
E L5: itertools import pairwise
E L7: PIL import Image, ImageDraw
E L9: faceless_champ.typography import load_font
E L10: faceless_champ.charts import BarChart, Heatmap, Histogram, LineChart, NetworkGraph, PieChart, RankedBarChart, ScatterPlot, VectorField
E L11: faceless_champ.charts.scales import palette_color, project, sankey_geometry, separate_positions, ticks
```

### faceless_champ.charts.scales

[src/faceless_champ/charts/scales.py](../../src/faceless_champ/charts/scales.py)

```text
E L3: math
E L4: bisect import bisect_right
E L5: collections.abc import Callable
E L6: dataclasses import dataclass
E L8: faceless_champ.components import finite
```

### faceless_champ.chess

[src/faceless_champ/chess.py](../../src/faceless_champ/chess.py)

```text
E L6: __future__ import annotations
E L8: json
E L9: math
E L10: bisect import bisect_right
E L11: dataclasses import dataclass, fields
E L12: functools import lru_cache
E L13: io import StringIO
E L14: pathlib import Path
E L16: PIL import Image, ImageColor, ImageDraw
E L18: faceless_champ.chess_assets import ChessAssets
E L19: faceless_champ.components import Component, finite
E L20: faceless_champ.typography import load_font
L L145: chess
L L303: chess.pgn
```

### faceless_champ.chess_assets

[src/faceless_champ/chess_assets.py](../../src/faceless_champ/chess_assets.py)

```text
E L3: hashlib
E L4: collections import OrderedDict
E L5: functools import lru_cache
E L6: pathlib import Path
E L8: PIL import Image, ImageOps
```

### faceless_champ.cli

[src/faceless_champ/cli.py](../../src/faceless_champ/cli.py)

```text
E L3: argparse
E L4: runpy
E L5: sys
E L6: pathlib import Path
E L8: faceless_champ.export import render
E L9: faceless_champ.timeline import Renderable
```

### faceless_champ.coding

[src/faceless_champ/coding.py](../../src/faceless_champ/coding.py)

```text
E L3: __future__ import annotations
E L5: math
E L6: re
E L7: collections.abc import Mapping
E L8: dataclasses import dataclass, field
E L9: itertools import pairwise
E L10: pathlib import Path
E L11: types import MappingProxyType
E L13: PIL import Image, ImageColor, ImageDraw
E L15: faceless_champ.animation import Animation, linear
E L16: faceless_champ.components import Component, finite
E L17: faceless_champ.typography import load_font
L L209: pygments.lexers import get_lexer_by_name
L L210: pygments.util import ClassNotFound
```

### faceless_champ.coding_workspace

[src/faceless_champ/coding_workspace.py](../../src/faceless_champ/coding_workspace.py)

```text
E L7: __future__ import annotations
E L9: math
E L10: dataclasses import dataclass, field
E L12: PIL import ImageColor
E L14: faceless_champ.animation import Animation
E L15: faceless_champ.coding import CodeTheme
E L16: faceless_champ.components import Circle, Component, Rectangle, Text, finite
E L17: faceless_champ.layout import Bounds, Group
E L18: faceless_champ.surfaces import ShadowStyle, card_surface
E L19: faceless_champ.typography import CLEAN_FLOW_FONT
```

### faceless_champ.colors

[src/faceless_champ/colors.py](../../src/faceless_champ/colors.py)

```text
E L3: dataclasses import dataclass, fields
E L4: types import MappingProxyType
E L6: PIL import ImageColor
E L8: faceless_champ.components import finite
```

### faceless_champ.components

[src/faceless_champ/components.py](../../src/faceless_champ/components.py)

```text
E L3: __future__ import annotations
E L5: math
E L6: re
E L7: collections.abc import Callable, Mapping
E L8: dataclasses import dataclass
E L9: io import BytesIO
E L10: itertools import pairwise
E L11: pathlib import Path
E L12: typing import TYPE_CHECKING, Any, Self
T L15: faceless_champ.animation import AnimationBuilder
T L16: faceless_champ.layout import Bounds
L L68: faceless_champ.masks import Mask
L L74: faceless_champ.surfaces import ShadowStyle
L L83: faceless_champ.effects import effect_stack
L L103: faceless_champ.layout import bounds
L L111: faceless_champ.layout import next_to
L L118: faceless_champ.layout import align_to
L L125: faceless_champ.animation import AnimationBuilder
L L130: faceless_champ.motion import visual_state
L L284: PIL import Image as PILImage
L L285: PIL import ImageOps
```

### faceless_champ.effects

[src/faceless_champ/effects.py](../../src/faceless_champ/effects.py)

```text
E L3: math
E L4: dataclasses import dataclass, fields, replace
E L6: PIL import ImageColor
E L8: faceless_champ.components import finite
L L142: faceless_champ.timeline import Scene
```

### faceless_champ.export

[src/faceless_champ/export.py](../../src/faceless_champ/export.py)

```text
E L3: __future__ import annotations
E L5: math
E L6: os
E L7: subprocess
E L8: tempfile
E L9: collections.abc import Callable
E L10: dataclasses import dataclass
E L11: pathlib import Path
E L13: faceless_champ.audio import require_tools
E L14: faceless_champ.components import Canvas, finite
E L15: faceless_champ.gpu import GPUOptions
E L16: faceless_champ.renderer import PillowRenderer, Renderer, managed_renderer
E L17: faceless_champ.timeline import Grid, Layer, Renderable, Scene, Sequence
```

### faceless_champ.flags

[src/faceless_champ/flags.py](../../src/faceless_champ/flags.py)

```text
E L3: functools import lru_cache
E L4: pathlib import Path
E L5: typing import Any
E L7: faceless_champ.components import Image
```

### faceless_champ.flow

[src/faceless_champ/flow/__init__.py](../../src/faceless_champ/flow/__init__.py)

```text
E L3: faceless_champ.flow.clip import FlowChamp
E L4: faceless_champ.flow.design import FlowDesign, FlowVisual
E L5: faceless_champ.flow.model import SYMBOLS, FlowDataError, FlowEdge, FlowGraph, FlowNode, FlowPort, FlowTheme
E L6: faceless_champ.flow.script import FlowScript
```

### faceless_champ.flow.clip

[src/faceless_champ/flow/clip.py](../../src/faceless_champ/flow/clip.py)

```text
E L3: json
E L4: bisect import bisect_right
E L5: collections import OrderedDict
E L6: copy import deepcopy
E L7: dataclasses import asdict
E L8: itertools import pairwise
E L9: pathlib import Path
E L11: PIL import Image
E L13: faceless_champ.components import Component
E L14: faceless_champ.layout import Bounds
E L15: faceless_champ.flow.geometry import edge_path, layout_graph, length, sample, transform
E L16: faceless_champ.flow.model import FlowDataError, FlowGraph, FlowTheme, construct, number, object_fields
E L17: faceless_champ.flow.script import FlowScript
E L18: faceless_champ.flow.symbols import symbol_paths
L L79: faceless_champ.flow.drawing import prepare_labels
L L140: faceless_champ.flow.drawing import raster_label
L L285: faceless_champ.flow.drawing import draw_frame
```

### faceless_champ.flow.design

[src/faceless_champ/flow/design.py](../../src/faceless_champ/flow/design.py)

```text
E L3: __future__ import annotations
E L5: dataclasses import dataclass
E L6: itertools import pairwise
E L7: math import ceil
E L8: pathlib import Path
E L9: types import MappingProxyType
E L11: PIL import ImageColor
E L13: faceless_champ.animation import Animation, linear, smooth
E L14: faceless_champ.components import Component, Image, Rectangle, Text, finite
E L15: faceless_champ.layout import Bounds, Group, transform_point
E L16: faceless_champ.surfaces import ShadowStyle, card_surface
E L17: faceless_champ.typography import CLEAN_FLOW_FONT, fit_text
E L18: faceless_champ.flow.clip import FlowChamp
E L19: faceless_champ.flow.model import FlowGraph, FlowTheme
E L20: faceless_champ.flow.script import FlowScript
```

### faceless_champ.flow.drawing

[src/faceless_champ/flow/drawing.py](../../src/faceless_champ/flow/drawing.py)

```text
E L3: math
E L4: random
E L5: functools import lru_cache
E L6: itertools import pairwise
E L8: PIL import Image, ImageColor, ImageDraw, ImageFilter
E L10: faceless_champ.typography import load_font
E L11: faceless_champ.flow.geometry import length, prefix, sample, transform
E L12: faceless_champ.flow.model import FlowDataError
```

### faceless_champ.flow.examples

[src/faceless_champ/flow/examples.py](../../src/faceless_champ/flow/examples.py)

```text
E L3: faceless_champ.flow.model import FlowEdge, FlowGraph, FlowNode, FlowPort
E L4: faceless_champ.flow.script import FlowScript
```

### faceless_champ.flow.geometry

[src/faceless_champ/flow/geometry.py](../../src/faceless_champ/flow/geometry.py)

```text
E L3: math
E L4: itertools import pairwise
E L6: faceless_champ.flow.model import FlowDataError
```

### faceless_champ.flow.model

[src/faceless_champ/flow/model.py](../../src/faceless_champ/flow/model.py)

```text
E L3: json
E L4: math
E L5: dataclasses import asdict, dataclass, fields
E L6: pathlib import Path
E L8: PIL import ImageColor
```

### faceless_champ.flow.script

[src/faceless_champ/flow/script.py](../../src/faceless_champ/flow/script.py)

```text
E L3: json
E L4: copy import deepcopy
E L5: dataclasses import dataclass
E L6: pathlib import Path
E L8: faceless_champ.flow.model import FlowDataError, choice, color, number, object_fields, point, text
```

### faceless_champ.flow.symbols

[src/faceless_champ/flow/symbols.py](../../src/faceless_champ/flow/symbols.py)

```text
E L3: math
```

### faceless_champ.gpu

[src/faceless_champ/gpu.py](../../src/faceless_champ/gpu.py)

```text
E L3: dataclasses import dataclass
E L4: importlib.metadata import PackageNotFoundError, version
E L6: faceless_champ.components import finite
L L47: faceless_champ.backends.moderngl import ModernGLRenderer
```

### faceless_champ.gradients

[src/faceless_champ/gradients.py](../../src/faceless_champ/gradients.py)

```text
E L3: math
E L4: bisect import bisect_right
E L5: dataclasses import dataclass, field
E L6: itertools import islice, pairwise
E L8: PIL import ImageColor
```

### faceless_champ.indicators

[src/faceless_champ/indicators.py](../../src/faceless_champ/indicators.py)

```text
E L3: math
E L4: itertools import pairwise
E L6: PIL import Image, ImageDraw
E L8: faceless_champ.components import Component, Number, finite
E L9: faceless_champ.motion import rgba
```

### faceless_champ.layout

[src/faceless_champ/layout.py](../../src/faceless_champ/layout.py)

```text
E L3: __future__ import annotations
E L5: math
E L6: dataclasses import dataclass
E L7: typing import Any, Self
E L9: faceless_champ.components import Component, Image, finite
L L55: faceless_champ.arch import ArchChamp
L L56: faceless_champ.charts import Chart
L L57: faceless_champ.chess import ChessChamp
L L58: faceless_champ.coding import CodingChamp
L L59: faceless_champ.components import Text
L L60: faceless_champ.flow import FlowChamp
L L61: faceless_champ.gradients import LinearGradient, RadialGradient
L L62: faceless_champ.maps import Map
L L63: faceless_champ.os_ui import OSClip
L L64: faceless_champ.paths import VectorPath
L L65: faceless_champ.playground.playback import PlaygroundView
L L66: faceless_champ.subtitles import Captions
L L67: faceless_champ.surfaces import Surface
L L68: faceless_champ.web.clip import HtmlClip
L L83: faceless_champ.backends._skia_text import text_size
L L128: faceless_champ.renderer import PillowRenderer
```

### faceless_champ.maps

[src/faceless_champ/maps.py](../../src/faceless_champ/maps.py)

```text
E L3: __future__ import annotations
E L5: json
E L6: math
E L7: functools import lru_cache
E L8: pathlib import Path
E L10: PIL import Image, ImageColor, ImageDraw
E L12: faceless_champ.animation import AnimationBuilder
E L13: faceless_champ.components import Component, finite
L L27: numpy as np
```

### faceless_champ.masks

[src/faceless_champ/masks.py](../../src/faceless_champ/masks.py)

```text
E L3: dataclasses import dataclass
E L5: faceless_champ.components import finite
L L31: faceless_champ.paths import PathData
L L67: faceless_champ.animation import Animation, linear
```

### faceless_champ.motion

[src/faceless_champ/motion.py](../../src/faceless_champ/motion.py)

```text
E L3: math
E L5: PIL import ImageColor
L L20: faceless_champ.components import Shape, Text
L L37: faceless_champ.gradients import LinearGradient, RadialGradient
```

### faceless_champ.narration

[src/faceless_champ/narration.py](../../src/faceless_champ/narration.py)

```text
E L3: __future__ import annotations
E L5: typing import Self
E L7: faceless_champ.components import Canvas, finite
E L8: faceless_champ.subtitles import SubtitleTrack
E L9: faceless_champ.timeline import Scene
```

### faceless_champ.os_ui

[src/faceless_champ/os_ui/__init__.py](../../src/faceless_champ/os_ui/__init__.py)

```text
E L3: faceless_champ.os_ui.clip import OSClip
E L4: faceless_champ.os_ui.model import Control, File, Folder, MacOSPreset, SettingsPage, VirtualFileSystem, starter_pages
E L5: faceless_champ.os_ui.script import OSScript
```

### faceless_champ.os_ui.clip

[src/faceless_champ/os_ui/clip.py](../../src/faceless_champ/os_ui/clip.py)

```text
E L3: __future__ import annotations
E L5: bisect import bisect_right
E L6: collections import OrderedDict
E L7: copy import deepcopy
E L8: dataclasses import replace
E L9: math import ceil
E L11: faceless_champ.components import Component, finite
E L12: faceless_champ.os_ui.layout import geometry, listing
E L13: faceless_champ.os_ui.model import File, Folder, MacOSPreset, VirtualFileSystem, starter_pages
E L14: faceless_champ.os_ui.script import OSScript
L L159: PIL import Image
L L464: faceless_champ.os_ui.drawing import display_state
L L479: faceless_champ.os_ui.drawing import draw_frame
```

### faceless_champ.os_ui.drawing

[src/faceless_champ/os_ui/drawing.py](../../src/faceless_champ/os_ui/drawing.py)

```text
E L3: math
E L4: copy import deepcopy
E L5: functools import lru_cache
E L7: PIL import Image, ImageDraw, ImageFilter, ImageOps
E L9: faceless_champ.typography import DEFAULT_FONT, load_font
E L10: faceless_champ.os_ui.layout import geometry, listing
E L11: faceless_champ.os_ui.model import Folder
```

### faceless_champ.os_ui.layout

[src/faceless_champ/os_ui/layout.py](../../src/faceless_champ/os_ui/layout.py)

```text
E L3: faceless_champ.layout import Bounds
E L4: faceless_champ.os_ui.model import Folder
```

### faceless_champ.os_ui.model

[src/faceless_champ/os_ui/model.py](../../src/faceless_champ/os_ui/model.py)

```text
E L3: __future__ import annotations
E L5: copy import deepcopy
E L6: dataclasses import dataclass, field
E L7: pathlib import Path
L L84: dataclasses import replace
L L112: dataclasses import replace
L L167: math import isfinite
L L177: math import isfinite
L L252: PIL import ImageColor
L L254: faceless_champ.components import finite
```

### faceless_champ.os_ui.script

[src/faceless_champ/os_ui/script.py](../../src/faceless_champ/os_ui/script.py)

```text
E L3: copy import deepcopy
E L4: dataclasses import dataclass
E L6: faceless_champ.components import finite
```

### faceless_champ.paths

[src/faceless_champ/paths.py](../../src/faceless_champ/paths.py)

```text
E L3: math
E L4: dataclasses import dataclass
E L5: itertools import pairwise
E L7: faceless_champ.components import Shape, finite
L L21: itertools import islice
L L69: faceless_champ.layout import Bounds
```

### faceless_champ.playground

[src/faceless_champ/playground/__init__.py](../../src/faceless_champ/playground/__init__.py)

```text
E L3: faceless_champ.playground.model import CanvasItem, CodeCheckpoint, EventBinding, PlaygroundError, PlaygroundScript, ValueBinding
E L4: faceless_champ.playground.playback import CodeEditor, EditTimeline, PlaygroundCanvas, PlaygroundOutput, PlaygroundView
E L5: faceless_champ.playground.prepare import PreparedPlayground, prepare_playground
E L6: faceless_champ.playground.runtime import emit, event, inputs
```

### faceless_champ.playground.model

[src/faceless_champ/playground/model.py](../../src/faceless_champ/playground/model.py)

```text
E L3: __future__ import annotations
E L5: json
E L6: dataclasses import dataclass, field
E L7: pathlib import PurePosixPath
E L8: types import MappingProxyType
E L10: faceless_champ.components import finite
L L90: faceless_champ.web import WebScript
L L99: copy import deepcopy
L L149: PIL import ImageColor
L L239: dataclasses import asdict
L L259: faceless_champ.web.model import WebAction, WebScript
```

### faceless_champ.playground.playback

[src/faceless_champ/playground/playback.py](../../src/faceless_champ/playground/playback.py)

```text
E L3: __future__ import annotations
E L5: difflib
E L6: json
E L7: math
E L8: dataclasses import asdict
E L10: PIL import Image, ImageDraw, ImageOps
E L12: faceless_champ.coding import CodeTheme, CodingChamp, draw_code
E L13: faceless_champ.components import Component, finite
E L14: faceless_champ.typography import load_font
E L15: faceless_champ.playground.model import PlaygroundError, PlaygroundScript
E L16: faceless_champ.playground.prepare import PreparedPlayground
L L163: faceless_champ.renderer import PillowRenderer
L L171: faceless_champ.coding import MONO_FONT
L L209: faceless_champ.web import WebCapture
L L366: faceless_champ.web import WebCapture
L L373: faceless_champ.coding import MONO_FONT
L L396: textwrap
```

### faceless_champ.playground.prepare

[src/faceless_champ/playground/prepare.py](../../src/faceless_champ/playground/prepare.py)

```text
E L3: __future__ import annotations
E L5: hashlib
E L6: importlib.metadata
E L7: json
E L8: os
E L9: platform
E L10: shutil
E L11: signal
E L12: subprocess
E L13: sys
E L14: tempfile
E L15: time
E L16: uuid
E L17: pathlib import Path
E L19: faceless_champ.components import finite
E L20: faceless_champ.playground.model import PlaygroundError, PlaygroundScript, json_copy, valid_canvas_value
L L36: playwright.sync_api import sync_playwright
L L141: PIL import ImageColor
L L219: faceless_champ.web import WebCapture
L L304: faceless_champ.web import WebCapture
```

### faceless_champ.playground.runtime

[src/faceless_champ/playground/runtime.py](../../src/faceless_champ/playground/runtime.py)

```text
E L3: json
E L4: os
```

### faceless_champ.playground.web_worker

[src/faceless_champ/playground/web_worker.py](../../src/faceless_champ/playground/web_worker.py)

```text
E L3: json
E L4: sys
E L5: pathlib import Path
E L7: faceless_champ.web import HtmlPage, WebScript, capture_html
E L8: faceless_champ.playground.model import PlaygroundScript
```

### faceless_champ.preview

[src/faceless_champ/preview.py](../../src/faceless_champ/preview.py)

```text
E L3: __future__ import annotations
E L5: math
E L6: os
E L7: tempfile
E L8: collections.abc import Iterable
E L9: dataclasses import dataclass
E L10: pathlib import Path
E L12: PIL import Image as PILImage
E L13: PIL import ImageDraw
E L15: faceless_champ.components import finite
E L16: faceless_champ.renderer import PillowRenderer, Renderer, managed_renderer
E L17: faceless_champ.timeline import Renderable
E L18: faceless_champ.typography import load_font
```

### faceless_champ.procedural

[src/faceless_champ/procedural.py](../../src/faceless_champ/procedural.py)

```text
E L3: PIL import ImageColor
E L5: faceless_champ.components import Component, finite
L L23: math
L L25: faceless_champ.effects import _phase
L L53: faceless_champ._effects_cpu import numpy
```

### faceless_champ.progress

[src/faceless_champ/progress.py](../../src/faceless_champ/progress.py)

```text
E L3: __future__ import annotations
E L5: math
E L6: sys
E L7: time
E L8: typing import TextIO
```

### faceless_champ.renderer

[src/faceless_champ/renderer.py](../../src/faceless_champ/renderer.py)

```text
E L3: __future__ import annotations
E L5: math
E L6: collections import OrderedDict
E L7: copy import copy
E L8: functools import wraps
E L9: io import BytesIO
E L10: itertools import pairwise
E L11: typing import Protocol
E L13: PIL import Image as PILImage
E L14: PIL import ImageChops, ImageColor, ImageDraw, ImageFilter, ImageOps
E L16: faceless_champ.arch import ArchChamp
E L17: faceless_champ.charts import Chart
E L18: faceless_champ.charts.drawing import draw_chart
E L19: faceless_champ.chess import ChessChamp
E L20: faceless_champ.components import Arrow, Circle, Ellipse, Equation, Icon, Image, ImageSlot, Line, Number, Polyline, Rectangle, Shape, Text, Triangle, finite
E L37: faceless_champ.flow import FlowChamp
E L38: faceless_champ.layout import Group, transform_point
E L39: faceless_champ.maps import Map, draw_map
E L40: faceless_champ.motion import style_value
E L41: faceless_champ.os_ui import OSClip
E L42: faceless_champ.playground.playback import PlaygroundView
E L43: faceless_champ.subtitles import Captions
E L44: faceless_champ.timeline import Grid, Layer, Renderable, Scene, Sequence
E L45: faceless_champ.typography import DEFAULT_FONT, load_font
E L46: faceless_champ.web.clip import HtmlClip
L L60: faceless_champ.backends.skia import SkiaRenderer
L L64: faceless_champ.backends.moderngl import ModernGLRenderer
L L68: faceless_champ.backends._auto import AutoRenderer
L L76: importlib.metadata import PackageNotFoundError, version
L L105: hashlib
L L106: pathlib import Path
L L108: faceless_champ.surfaces import Surface
L L284: faceless_champ.gradients import LinearGradient, RadialGradient
L L285: faceless_champ.paths import VectorPath
L L286: faceless_champ.surfaces import Surface
L L293: faceless_champ._effects_cpu import numpy
L L301: faceless_champ.coding import CodingChamp
L L302: faceless_champ.indicators import ProgressBar
L L305: faceless_champ._effects_cpu import numpy
L L313: faceless_champ.backends._native import load_skia
L L320: faceless_champ._effects_cpu import numpy
L L342: faceless_champ.backends._skia_text import text_size
L L374: faceless_champ.effects import needs_compositor
L L378: faceless_champ._compositor import Compositor
L L379: faceless_champ._cpu_device import CPUDevice
L L380: faceless_champ.backends._raster_adapter import PillowRasterAdapter
L L388: faceless_champ._render_state import composition_frame
L L393: faceless_champ._render_state import fit_frame
L L492: faceless_champ.layout import Bounds
L L493: faceless_champ.motion import inverse, matrix, multiply, point
L L587: faceless_champ._portable import guard_size
L L619: faceless_champ.gradients import LinearGradient, RadialGradient
L L620: faceless_champ.paths import VectorPath
L L621: faceless_champ.surfaces import Surface
L L628: faceless_champ._portable import shape_sprite, surface_sprite
L L645: faceless_champ.coding import CodingChamp, draw_code
L L646: faceless_champ.indicators import ProgressBar, draw_indicator
L L652: faceless_champ.arch.rendering import ArchSession
L L855: numpy as np
L L856: matplotlib import rc_context
L L857: matplotlib.font_manager import FontProperties
L L858: matplotlib.mathtext import MathTextParser
L L895: numpy as np
L L896: matplotlib import ft2font
L L897: matplotlib.backends.backend_agg import RendererAgg
L L898: matplotlib.mathtext import MathTextParser
L L899: matplotlib.path import Path as MathPath
L L900: matplotlib.transforms import Affine2D, Bbox
```

### faceless_champ.scheduling

[src/faceless_champ/scheduling.py](../../src/faceless_champ/scheduling.py)

```text
E L3: math
E L4: copy import copy, deepcopy
E L6: faceless_champ.animation import Animation, _cycles
E L7: faceless_champ.components import finite
E L8: faceless_champ.spring import Spring, _ReversedSpring
```

### faceless_champ.spring

[src/faceless_champ/spring.py](../../src/faceless_champ/spring.py)

```text
E L9: __future__ import annotations
E L11: math
E L12: dataclasses import dataclass, field
E L13: numbers import Real
```

### faceless_champ.subtitles

[src/faceless_champ/subtitles.py](../../src/faceless_champ/subtitles.py)

```text
E L3: __future__ import annotations
E L5: re
E L6: bisect import bisect_right
E L7: collections.abc import Iterable
E L8: dataclasses import dataclass
E L9: itertools import accumulate
E L10: pathlib import Path
E L11: typing import Any
E L13: faceless_champ.components import Component, finite
```

### faceless_champ.surfaces

[src/faceless_champ/surfaces.py](../../src/faceless_champ/surfaces.py)

```text
E L3: math
E L4: contextlib import closing
E L5: dataclasses import dataclass
E L7: PIL import Image as PILImage
E L8: PIL import ImageColor, ImageDraw, ImageFilter
E L10: faceless_champ.components import Component, Image, finite
E L11: faceless_champ.gradients import LinearGradient, RadialGradient
E L12: faceless_champ.layout import Bounds
L L122: faceless_champ._surface_raster import _allocation, gradient_card
```

### faceless_champ.timeline

[src/faceless_champ/timeline.py](../../src/faceless_champ/timeline.py)

```text
E L3: __future__ import annotations
E L5: math
E L6: collections.abc import Callable
E L7: contextlib import contextmanager
E L8: copy import deepcopy
E L9: dataclasses import dataclass, field
E L10: itertools import pairwise
E L11: numbers import Real
E L12: pathlib import Path
E L13: typing import Any, Self
E L15: faceless_champ.animation import Animation, interpolate, relative_value, smooth
E L16: faceless_champ.audio import AudioClip
E L17: faceless_champ.components import Canvas, Component, finite
E L18: faceless_champ.layout import Group
E L19: faceless_champ.motion import style_value
E L20: faceless_champ.spring import _spring_progress_bounds
E L21: faceless_champ.subtitles import Captions
L L32: faceless_champ.export import render
L L244: copy import copy
L L274: faceless_champ._render_state import entry_geometry, ink_box
L L275: faceless_champ.backends._raster_adapter import PillowRasterAdapter
L L292: faceless_champ.scheduling import Schedule, play_schedule
L L348: faceless_champ.indicators import Countdown
L L399: faceless_champ.indicators import Countdown
L L506: faceless_champ.effects import validate_effect_value
L L557: faceless_champ.transitions import transition as validate_transition
L L634: faceless_champ.effects import effect_stack
```

### faceless_champ.transitions

[src/faceless_champ/transitions.py](../../src/faceless_champ/transitions.py)

```text
E L3: dataclasses import dataclass
E L5: faceless_champ.components import finite
```

### faceless_champ.typography

[src/faceless_champ/typography.py](../../src/faceless_champ/typography.py)

```text
E L3: pathlib import Path
E L5: PIL import ImageFont
L L29: faceless_champ.components import Text, finite
L L30: faceless_champ.layout import Bounds
```

### faceless_champ.web

[src/faceless_champ/web/__init__.py](../../src/faceless_champ/web/__init__.py)

```text
E L3: faceless_champ.web.capture import capture_html
E L4: faceless_champ.web.clip import HtmlClip, WebCallout, WebFocus, WebHighlight
E L5: faceless_champ.web.model import HtmlPage, WebAction, WebCapture, WebError, WebScript
```

### faceless_champ.web.capture

[src/faceless_champ/web/capture.py](../../src/faceless_champ/web/capture.py)

```text
E L3: __future__ import annotations
E L5: hashlib
E L6: json
E L7: math
E L8: shutil
E L9: tempfile
E L10: threading
E L11: contextlib import contextmanager
E L12: http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
E L13: pathlib import Path
E L14: urllib.parse import quote, urlsplit
E L16: faceless_champ.components import finite
E L17: faceless_champ.web.model import HtmlPage, WebCapture, WebError, WebScript
L L124: playwright.sync_api import sync_playwright
```

### faceless_champ.web.clip

[src/faceless_champ/web/clip.py](../../src/faceless_champ/web/clip.py)

```text
E L3: __future__ import annotations
E L5: dataclasses import dataclass
E L7: PIL import Image, ImageDraw, ImageOps
E L9: faceless_champ.components import Component, finite
E L10: faceless_champ.typography import DEFAULT_FONT, load_font
E L11: faceless_champ.web.model import WebCapture, WebError
```

### faceless_champ.web.model

[src/faceless_champ/web/model.py](../../src/faceless_champ/web/model.py)

```text
E L3: __future__ import annotations
E L5: json
E L6: math
E L7: dataclasses import asdict, dataclass, field
E L8: pathlib import Path
E L10: faceless_champ.components import finite
L L139: PIL import Image
L L159: PIL import Image
```

### facelesschamp_agent

[facelesschamp-agent/src/facelesschamp_agent/__init__.py](../../facelesschamp-agent/src/facelesschamp_agent/__init__.py)

```text
E L3: facelesschamp_agent.errors import AgentError
E L4: facelesschamp_agent.models import BeatSelection, DesignSpec, QualityReport, ReviewFinding, ScenePlan, SelectionPlan, StoryPlan, VideoBrief, VideoPlan
L L40: facelesschamp_agent import templates
L L44: facelesschamp_agent.context import read_project_context
L L48: facelesschamp_agent import planning
L L52: facelesschamp_agent.project import AgentProject
L L56: facelesschamp_agent.registry import CapabilityRegistry
```

### facelesschamp_agent.__main__

[facelesschamp-agent/src/facelesschamp_agent/__main__.py](../../facelesschamp-agent/src/facelesschamp_agent/__main__.py)

```text
E L1: facelesschamp_agent.cli import main
```

### facelesschamp_agent.cli

[facelesschamp-agent/src/facelesschamp_agent/cli.py](../../facelesschamp-agent/src/facelesschamp_agent/cli.py)

```text
E L3: argparse
E L4: json
E L5: shutil
E L6: sys
E L7: dataclasses import asdict
E L8: importlib.resources import as_file, files
E L9: pathlib import Path
E L11: faceless_champ import ExportProgress
E L12: facelesschamp_kit.cli import doctor
E L13: facelesschamp_kit.diagnostics import KitError
E L14: facelesschamp_kit.recipes import recipe_specs
E L15: pydantic import ValidationError
E L17: facelesschamp_agent.context import read_project_context
E L18: facelesschamp_agent.errors import AgentError
E L19: facelesschamp_agent.models import SCHEMAS
E L20: facelesschamp_agent.planning import plan_project
E L21: facelesschamp_agent.project import AgentProject, init_project
E L22: facelesschamp_agent.registry import CapabilityRegistry
L L110: facelesschamp_agent import __version__
```

### facelesschamp_agent.context

[facelesschamp-agent/src/facelesschamp_agent/context.py](../../facelesschamp-agent/src/facelesschamp_agent/context.py)

```text
E L9: __future__ import annotations
E L11: hashlib
E L12: json
E L13: math
E L14: os
E L15: re
E L16: collections.abc import Iterable
E L17: itertools import pairwise
E L18: pathlib import Path
E L19: typing import Any
E L21: facelesschamp_agent.errors import AgentError
```

### facelesschamp_agent.delivery

[facelesschamp-agent/src/facelesschamp_agent/delivery.py](../../facelesschamp-agent/src/facelesschamp_agent/delivery.py)

```text
E L3: pathlib import Path
E L5: facelesschamp_agent.errors import AgentError
```

### facelesschamp_agent.errors

[facelesschamp-agent/src/facelesschamp_agent/errors.py](../../facelesschamp-agent/src/facelesschamp_agent/errors.py)

```text
E L3: facelesschamp_kit.diagnostics import KitError
```

### facelesschamp_agent.examples

[facelesschamp-agent/src/facelesschamp_agent/examples.py](../../facelesschamp-agent/src/facelesschamp_agent/examples.py)

```text
E L3: importlib.resources import files
E L5: faceless_champ import CanvasItem, CodeCheckpoint, PlaygroundScript, ValueBinding, prepare_playground
E L7: facelesschamp_agent.models import VideoPlan
E L8: facelesschamp_agent.project import AgentProject, init_project
```

### facelesschamp_agent.layout

[facelesschamp-agent/src/facelesschamp_agent/layout.py](../../facelesschamp-agent/src/facelesschamp_agent/layout.py)

```text
E L8: math
E L9: bisect import bisect_left
E L10: itertools import combinations
E L12: facelesschamp_agent.errors import AgentError
```

### facelesschamp_agent.media

[facelesschamp-agent/src/facelesschamp_agent/media.py](../../facelesschamp-agent/src/facelesschamp_agent/media.py)

```text
E L3: array
E L4: math
E L5: subprocess
E L6: sys
E L7: fractions import Fraction
E L8: pathlib import Path
E L10: faceless_champ.audio import probe
E L12: facelesschamp_agent.errors import AgentError
```

### facelesschamp_agent.models

[facelesschamp-agent/src/facelesschamp_agent/models.py](../../facelesschamp-agent/src/facelesschamp_agent/models.py)

```text
E L3: typing import Annotated, Literal
E L5: pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
L L72: PIL import ImageColor
L L128: facelesschamp_kit.recipes import validate_recipe
```

### facelesschamp_agent.planning

[facelesschamp-agent/src/facelesschamp_agent/planning.py](../../facelesschamp-agent/src/facelesschamp_agent/planning.py)

```text
E L7: hashlib
E L8: json
E L9: math
E L10: re
E L11: copy import deepcopy
E L12: pathlib import Path
E L14: facelesschamp_agent.context import read_project_context
E L15: facelesschamp_agent.errors import AgentError
E L16: facelesschamp_agent.models import BeatSelection, DesignSpec, SelectionPlan
E L17: facelesschamp_agent.registry import CapabilityRegistry
E L18: facelesschamp_agent.templates import TEMPLATE_ID, coding_template_guidance, default_coding_template, load_coding_tutorial
L L640: facelesschamp_agent.project import _write_json
L L649: facelesschamp_agent.templates import install_coding_tutorial
```

### facelesschamp_agent.project

[facelesschamp-agent/src/facelesschamp_agent/project.py](../../facelesschamp-agent/src/facelesschamp_agent/project.py)

```text
E L3: hashlib
E L4: importlib
E L5: json
E L6: math
E L7: shutil
E L8: tempfile
E L9: uuid
E L10: dataclasses import replace
E L11: pathlib import Path
E L13: faceless_champ import Scene, StoryboardSample, SubtitleTrack, create_renderer, render, render_storyboard, rendering_identity, save_frame
E L23: faceless_champ.audio import probe
E L24: facelesschamp_kit import Project, Video
E L25: facelesschamp_kit.assets import digest
E L26: facelesschamp_kit.themes import THEMES
E L28: facelesschamp_agent.errors import AgentError
E L29: facelesschamp_agent.media import run_tool, verify_media
E L30: facelesschamp_agent.models import QualityReport, ReviewSubmission, VideoPlan
L L146: facelesschamp_agent.templates import load_coding_tutorial
L L458: facelesschamp_agent.layout import audit_layout
L L473: shlex
L L475: facelesschamp_agent.delivery import write_render_entrypoint
L L878: facelesschamp_agent.delivery import write_render_entrypoint
L L879: facelesschamp_agent.scaffold import CONFIG, INITIAL_PLAN, SOURCE
```

### facelesschamp_agent.registry

[facelesschamp-agent/src/facelesschamp_agent/registry.py](../../facelesschamp-agent/src/facelesschamp_agent/registry.py)

```text
E L3: ast
E L4: hashlib
E L5: importlib
E L6: inspect
E L7: json
E L8: re
E L9: sys
E L10: collections import Counter
E L11: collections.abc import Mapping
E L12: copy import deepcopy
E L13: dataclasses import asdict
E L14: functools import lru_cache
E L15: importlib.resources import files
E L16: pathlib import Path
E L18: facelesschamp_kit.recipes import recipe_specs
E L20: facelesschamp_agent.errors import AgentError
```

### facelesschamp_agent.scaffold

[facelesschamp-agent/src/facelesschamp_agent/scaffold.py](../../facelesschamp-agent/src/facelesschamp_agent/scaffold.py)

```text
E L3: facelesschamp_agent.models import VideoPlan
```

### facelesschamp_agent.templates

[facelesschamp-agent/src/facelesschamp_agent/templates.py](../../facelesschamp-agent/src/facelesschamp_agent/templates.py)

```text
E L3: re
E L4: importlib.resources import files
E L5: pathlib import Path
E L7: facelesschamp_kit import CodingTutorialStyle, CodingTutorialTemplate
E L9: facelesschamp_agent.errors import AgentError
L L25: facelesschamp_agent.scaffold import INITIAL_PLAN
```

### facelesschamp_kit

[facelesschamp-kit/src/facelesschamp_kit/__init__.py](../../facelesschamp-kit/src/facelesschamp_kit/__init__.py)

```text
E L3: facelesschamp_kit.blocks import Block, BlockBuild
E L4: facelesschamp_kit.blocks.effects import EffectBlock, ParticleBackdrop, ProceduralBackdrop
E L5: facelesschamp_kit.compiler import CompiledVideo
E L6: facelesschamp_kit.context import BuildContext
E L7: facelesschamp_kit.diagnostics import KitError
E L8: facelesschamp_kit.project import Project
E L9: facelesschamp_kit.recipes import RecipeEvent, RecipeSpec, apply_recipe, recipe_specs, validate_recipe
E L10: facelesschamp_kit.themes import CLEAN_FLOW, Theme
E L11: facelesschamp_kit.tutorials import CodingTutorialStyle, CodingTutorialTemplate
E L12: facelesschamp_kit.video import Segment, Video
```

### facelesschamp_kit.__main__

[facelesschamp-kit/src/facelesschamp_kit/__main__.py](../../facelesschamp-kit/src/facelesschamp_kit/__main__.py)

```text
E L1: facelesschamp_kit.cli import main
```

### facelesschamp_kit.assets

[facelesschamp-kit/src/facelesschamp_kit/assets.py](../../facelesschamp-kit/src/facelesschamp_kit/assets.py)

```text
E L3: hashlib
E L4: json
E L5: copy import deepcopy
E L6: importlib.resources import files
E L7: pathlib import Path, PurePosixPath
E L9: facelesschamp_kit.diagnostics import KitError, fields
```

### facelesschamp_kit.blocks

[facelesschamp-kit/src/facelesschamp_kit/blocks/__init__.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/__init__.py)

```text
E L3: dataclasses import dataclass
E L4: pathlib import Path
E L6: faceless_champ import Bounds, ImageSlot, Number, Rectangle, card_content_bounds, card_surface
E L8: facelesschamp_kit.diagnostics import KitError, number
E L9: facelesschamp_kit.blocks.base import Block, BlockBuild, build_group, centered, fit_text
E L10: facelesschamp_kit.blocks.chess import ChessBoard
E L11: facelesschamp_kit.blocks.coding import CodeEditor, CodingPlayground
E L12: facelesschamp_kit.blocks.effects import EffectBlock, ParticleBackdrop, ProceduralBackdrop
E L13: facelesschamp_kit.blocks.flow import FlowDiagram
E L14: facelesschamp_kit.blocks.flow_canvas import FlowCanvas
E L15: facelesschamp_kit.blocks.flow_design import FlowBackdrop, FlowCard, FlowPopup
E L16: facelesschamp_kit.blocks.os_ui import FinderWindow, OSWalkthrough, SettingsWindow
E L17: facelesschamp_kit.blocks.web import WebElement, WebWalkthrough
E L18: facelesschamp_kit.blocks.whiteboard import WhiteboardArrow, WhiteboardCircle, WhiteboardDrawing, WhiteboardLine, WhiteboardPath, WhiteboardRectangle
L L188: facelesschamp_kit.layouts import Split
L L203: facelesschamp_kit.layouts import Stack
E L243: facelesschamp_kit.blocks.arch import ArchCanvas
```

### facelesschamp_kit.blocks.arch

[facelesschamp-kit/src/facelesschamp_kit/blocks/arch.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/arch.py)

```text
E L3: copy import deepcopy
E L4: dataclasses import asdict, dataclass
E L6: faceless_champ.arch import ArchChamp, ArchStyle
E L8: facelesschamp_kit.blocks.base import BlockBuild
```

### facelesschamp_kit.blocks.base

[facelesschamp-kit/src/facelesschamp_kit/blocks/base.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/base.py)

```text
E L1: dataclasses import dataclass, field
E L2: typing import Protocol, runtime_checkable
E L4: faceless_champ import Bounds, Component, Group
E L5: faceless_champ import fit_text as core_fit_text
E L7: facelesschamp_kit.diagnostics import KitError
```

### facelesschamp_kit.blocks.chess

[facelesschamp-kit/src/facelesschamp_kit/blocks/chess.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/chess.py)

```text
E L3: dataclasses import dataclass
E L5: faceless_champ import ChessAssets, ChessChamp, ChessScript, ChessTheme
E L7: facelesschamp_kit.blocks.base import BlockBuild
```

### facelesschamp_kit.blocks.coding

[facelesschamp-kit/src/facelesschamp_kit/blocks/coding.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/coding.py)

```text
E L3: dataclasses import dataclass
E L5: faceless_champ import Bounds, Group, PlaygroundCanvas, PlaygroundOutput, PlaygroundScript, PreparedPlayground
E L6: faceless_champ import CodeEditor as CoreEditor
E L8: facelesschamp_kit.diagnostics import KitError
E L9: facelesschamp_kit.blocks.base import BlockBuild
L L45: faceless_champ.components import finite
```

### facelesschamp_kit.blocks.effects

[facelesschamp-kit/src/facelesschamp_kit/blocks/effects.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/effects.py)

```text
E L3: dataclasses import dataclass
E L5: faceless_champ import EffectStack, Group, ParticleField, ProceduralBackground
E L7: facelesschamp_kit.blocks.base import BlockBuild
```

### facelesschamp_kit.blocks.flow

[facelesschamp-kit/src/facelesschamp_kit/blocks/flow.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/flow.py)

```text
E L3: dataclasses import dataclass
E L4: itertools import pairwise
E L6: faceless_champ import Arrow, Bounds, Group, Rectangle, card_content_bounds, card_surface
E L8: facelesschamp_kit.diagnostics import KitError
E L9: facelesschamp_kit.blocks.base import BlockBuild, fit_text
```

### facelesschamp_kit.blocks.flow_canvas

[facelesschamp-kit/src/facelesschamp_kit/blocks/flow_canvas.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/flow_canvas.py)

```text
E L3: dataclasses import dataclass
E L5: faceless_champ.flow import FlowChamp, FlowDesign, FlowGraph, FlowScript, FlowTheme
E L7: facelesschamp_kit.blocks.base import BlockBuild
E L8: facelesschamp_kit.blocks.flow_design import _design
```

### facelesschamp_kit.blocks.flow_design

[facelesschamp-kit/src/facelesschamp_kit/blocks/flow_design.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/flow_design.py)

```text
E L3: dataclasses import dataclass
E L5: faceless_champ.flow import FlowDesign
E L7: facelesschamp_kit.blocks.base import BlockBuild
```

### facelesschamp_kit.blocks.os_ui

[facelesschamp-kit/src/facelesschamp_kit/blocks/os_ui.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/os_ui.py)

```text
E L3: dataclasses import dataclass
E L5: faceless_champ.os_ui import MacOSPreset, OSClip, OSScript, VirtualFileSystem
E L7: facelesschamp_kit.blocks.base import BlockBuild
```

### facelesschamp_kit.blocks.web

[facelesschamp-kit/src/facelesschamp_kit/blocks/web.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/web.py)

```text
E L3: dataclasses import dataclass
E L5: faceless_champ import Bounds, Group, Rectangle, fit_text
E L6: faceless_champ.web import HtmlClip, WebCallout, WebCapture, WebFocus, WebHighlight
E L8: facelesschamp_kit.blocks.base import BlockBuild
```

### facelesschamp_kit.blocks.whiteboard

[facelesschamp-kit/src/facelesschamp_kit/blocks/whiteboard.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/whiteboard.py)

```text
E L3: math
E L4: dataclasses import dataclass
E L6: faceless_champ import Arrow, Circle, Group, Polyline, Rectangle
E L7: PIL import ImageColor
E L9: facelesschamp_kit.diagnostics import KitError, number
E L10: facelesschamp_kit.blocks.base import BlockBuild
```

### facelesschamp_kit.cli

[facelesschamp-kit/src/facelesschamp_kit/cli.py](../../facelesschamp-kit/src/facelesschamp_kit/cli.py)

```text
E L3: argparse
E L4: json
E L5: os
E L6: shutil
E L7: subprocess
E L8: sys
E L9: pathlib import Path
E L11: facelesschamp_kit.diagnostics import KitError
E L12: facelesschamp_kit.project import Project, package_version
E L13: facelesschamp_kit.scaffold import init_project
E L14: facelesschamp_kit.themes import THEMES
L L78: importlib.util
L L89: facelesschamp_kit.dependencies import dependencies
L L100: faceless_champ import renderer_capabilities
```

### facelesschamp_kit.compiler

[facelesschamp-kit/src/facelesschamp_kit/compiler.py](../../facelesschamp-kit/src/facelesschamp_kit/compiler.py)

```text
E L3: dataclasses import dataclass, field
E L5: faceless_champ import Animation, Bounds, Captions, ChessChamp, FadeIn, FadeOut, Group, PopIn, Scene, SlideIn, SlideOut, dot_grid, smooth
E L20: faceless_champ.arch import ArchChamp, ArchDataError
E L21: faceless_champ.flow import FlowChamp, FlowDataError
E L22: faceless_champ.os_ui import OSClip
E L24: facelesschamp_kit.assets import digest
E L25: facelesschamp_kit.blocks import BlockBuild
E L26: facelesschamp_kit.diagnostics import KitError, number
L L314: faceless_champ import PlaygroundError
```

### facelesschamp_kit.context

[facelesschamp-kit/src/facelesschamp_kit/context.py](../../facelesschamp-kit/src/facelesschamp_kit/context.py)

```text
E L1: csv
E L2: json
E L3: random
E L4: dataclasses import dataclass, field
E L5: pathlib import Path
E L7: faceless_champ import Bounds, Canvas
E L9: facelesschamp_kit.assets import AssetRegistry
E L10: facelesschamp_kit.diagnostics import KitError, number
E L11: facelesschamp_kit.themes import MIDNIGHT, Theme
L L56: hashlib
L L57: os
L L58: tempfile
L L60: faceless_champ import PlaygroundError, PreparedPlayground, prepare_playground
```

### facelesschamp_kit.dependencies

[facelesschamp-kit/src/facelesschamp_kit/dependencies.py](../../facelesschamp-kit/src/facelesschamp_kit/dependencies.py)

```text
E L3: tomllib
E L4: importlib.metadata import PackageNotFoundError, version
E L5: pathlib import Path
E L7: packaging.requirements import InvalidRequirement, Requirement
E L9: facelesschamp_kit.diagnostics import KitError
```

### facelesschamp_kit.diagnostics

[facelesschamp-kit/src/facelesschamp_kit/diagnostics.py](../../facelesschamp-kit/src/facelesschamp_kit/diagnostics.py)

```text
E L3: math
```

### facelesschamp_kit.layouts

[facelesschamp-kit/src/facelesschamp_kit/layouts.py](../../facelesschamp-kit/src/facelesschamp_kit/layouts.py)

```text
E L3: dataclasses import dataclass
E L5: faceless_champ import Bounds
E L7: facelesschamp_kit.blocks.base import build_group
E L8: facelesschamp_kit.diagnostics import KitError, number
```

### facelesschamp_kit.project

[facelesschamp-kit/src/facelesschamp_kit/project.py](../../facelesschamp-kit/src/facelesschamp_kit/project.py)

```text
E L3: hashlib
E L4: importlib
E L5: json
E L6: os
E L7: platform
E L8: subprocess
E L9: sys
E L10: threading
E L11: tomllib
E L12: contextlib import contextmanager
E L13: dataclasses import asdict
E L14: functools import lru_cache, wraps
E L15: importlib.metadata import PackageNotFoundError, version
E L16: pathlib import Path
E L18: faceless_champ import ArchDataError, Canvas, ExportSettings, GPUOptions, Grid, Layer, Scene, Sequence, StoryboardSample, create_renderer, render, render_storyboard, rendering_identity, save_frame, validate_composition
E L35: faceless_champ.audio import probe
E L37: facelesschamp_kit.assets import digest
E L38: facelesschamp_kit.compiler import CompiledVideo
E L39: facelesschamp_kit.context import BuildContext
E L40: facelesschamp_kit.diagnostics import KitError, fields
E L41: facelesschamp_kit.themes import THEMES
E L42: facelesschamp_kit.video import Video
L L138: facelesschamp_kit.dependencies import dependencies
L L143: facelesschamp_kit.dependencies import check_dependencies
L L213: faceless_champ.arch import ArchChamp
```

### facelesschamp_kit.recipes

[facelesschamp-kit/src/facelesschamp_kit/recipes.py](../../facelesschamp-kit/src/facelesschamp_kit/recipes.py)

```text
E L7: copy import deepcopy
E L8: dataclasses import dataclass
E L9: pathlib import Path
E L11: faceless_champ import Bounds, ChartReveal, ChartStyle, ColorScheme, FadeIn, LineChart, PieChart, Pulse
E L21: faceless_champ.flow import FlowEdge, FlowGraph, FlowNode, FlowScript
E L23: facelesschamp_kit.blocks import BlockBuild, CodingPlayground, FlowCanvas, MetricCard, TextPanel
E L24: facelesschamp_kit.diagnostics import KitError, fields, number
L L169: faceless_champ.arch import ArchDataError, validate_design
L L391: faceless_champ import with_alpha
L L432: faceless_champ import PreparedPlayground
L L493: facelesschamp_kit.blocks import ArchCanvas
```

### facelesschamp_kit.sample_assets.archchamp

[facelesschamp-kit/src/facelesschamp_kit/sample_assets/archchamp.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/archchamp.py)

```text
E L1: facelesschamp_kit import Video
E L2: facelesschamp_kit.recipes import apply_recipe
```

### facelesschamp_kit.sample_assets.coding_backend

[facelesschamp-kit/src/facelesschamp_kit/sample_assets/coding_backend.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/coding_backend.py)

```text
E L3: faceless_champ import CanvasItem, CodeCheckpoint, EventBinding, PlaygroundScript, ValueBinding
E L5: facelesschamp_kit.templates import coding_playground
```

### facelesschamp_kit.sample_assets.coding_concept

[facelesschamp-kit/src/facelesschamp_kit/sample_assets/coding_concept.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/coding_concept.py)

```text
E L3: faceless_champ import CanvasItem, CodeCheckpoint, EventBinding, PlaygroundScript, ValueBinding
E L5: facelesschamp_kit.templates import coding_playground
```

### facelesschamp_kit.sample_assets.coding_web

[facelesschamp-kit/src/facelesschamp_kit/sample_assets/coding_web.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/coding_web.py)

```text
E L3: faceless_champ import CodeCheckpoint, PlaygroundScript
E L5: facelesschamp_kit.templates import coding_playground
L L45: faceless_champ.web import WebScript
```

### facelesschamp_kit.sample_assets.flowchamp

[facelesschamp-kit/src/facelesschamp_kit/sample_assets/flowchamp.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/flowchamp.py)

```text
E L3: faceless_champ.flow.examples import recipe
E L5: facelesschamp_kit import Video
E L6: facelesschamp_kit.blocks import FlowCanvas
```

### facelesschamp_kit.sample_assets.os_ui

[facelesschamp-kit/src/facelesschamp_kit/sample_assets/os_ui.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/os_ui.py)

```text
E L3: faceless_champ.os_ui import File, Folder, OSScript, VirtualFileSystem
E L5: facelesschamp_kit import Video
E L6: facelesschamp_kit.blocks import OSWalkthrough
```

### facelesschamp_kit.sample_assets.whiteboard

[facelesschamp-kit/src/facelesschamp_kit/sample_assets/whiteboard.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/whiteboard.py)

```text
E L3: facelesschamp_kit.blocks import WhiteboardArrow, WhiteboardCircle, WhiteboardDrawing, WhiteboardLine, WhiteboardPath, WhiteboardRectangle
E L11: facelesschamp_kit.templates import WhiteboardScene, whiteboard_basic
```

### facelesschamp_kit.scaffold

[facelesschamp-kit/src/facelesschamp_kit/scaffold.py](../../facelesschamp-kit/src/facelesschamp_kit/scaffold.py)

```text
E L1: json
E L2: os
E L3: shutil
E L4: tempfile
E L5: importlib.resources import files
E L6: pathlib import Path
E L8: facelesschamp_kit.diagnostics import KitError
```

### facelesschamp_kit.templates

[facelesschamp-kit/src/facelesschamp_kit/templates.py](../../facelesschamp-kit/src/facelesschamp_kit/templates.py)

```text
E L3: collections.abc import Mapping
E L4: dataclasses import dataclass
E L6: faceless_champ import Bounds, Canvas, Draw, linear
E L8: facelesschamp_kit.blocks import Comparison, Heading, MetricCard, StepList, WhiteboardDrawing
E L9: facelesschamp_kit.diagnostics import KitError, number
E L10: facelesschamp_kit.themes import WHITEBOARD, Theme
E L11: facelesschamp_kit.video import Video
L L162: faceless_champ import Bounds
L L185: faceless_champ import ChessScript
L L186: faceless_champ.chess import ChessDataError
L L188: facelesschamp_kit.blocks import ChessBoard
L L222: facelesschamp_kit.blocks import CodingPlayground
```

### facelesschamp_kit.themes

[facelesschamp-kit/src/facelesschamp_kit/themes.py](../../facelesschamp-kit/src/facelesschamp_kit/themes.py)

```text
E L3: dataclasses import dataclass, replace
E L4: types import MappingProxyType
E L6: faceless_champ import CLEAN_FLOW_FONT, ShadowStyle
E L7: PIL import ImageColor
E L9: facelesschamp_kit.diagnostics import KitError, number
```

### facelesschamp_kit.tutorials

[facelesschamp-kit/src/facelesschamp_kit/tutorials/__init__.py](../../facelesschamp-kit/src/facelesschamp_kit/tutorials/__init__.py)

```text
E L3: facelesschamp_kit.tutorials.coding import CodingTutorialStyle, CodingTutorialTemplate
```

### facelesschamp_kit.tutorials.coding

[facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/__init__.py](../../facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/__init__.py)

```text
E L3: facelesschamp_kit.tutorials.coding.components import CodingTutorialTemplate
E L4: facelesschamp_kit.tutorials.coding.style import CodingTutorialStyle
```

### facelesschamp_kit.tutorials.coding.components

[facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/components.py](../../facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/components.py)

```text
E L3: math
E L5: faceless_champ import CLEAN_FLOW_FONT, Canvas, Circle, CodingChamp, FlowChamp, FlowEdge, FlowGraph, FlowNode, FlowScript, FlowTheme, Group, Polyline, Rectangle, Spring
E L21: faceless_champ.os_ui import File, Folder, MacOSPreset, OSClip, OSScript, VirtualFileSystem
E L23: facelesschamp_kit.tutorials.coding.style import CodingTutorialStyle
```

### facelesschamp_kit.tutorials.coding.style

[facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/style.py](../../facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/style.py)

```text
E L3: json
E L4: math
E L5: dataclasses import asdict, dataclass, fields, replace
E L6: importlib.resources import files
E L7: pathlib import Path
E L9: faceless_champ import Bounds, CodeTheme, CodeWorkspaceDesign, Spring
E L10: PIL import ImageColor
E L12: facelesschamp_kit.diagnostics import KitError
```

### facelesschamp_kit.video

[facelesschamp-kit/src/facelesschamp_kit/video.py](../../facelesschamp-kit/src/facelesschamp_kit/video.py)

```text
E L3: copy import deepcopy
E L4: dataclasses import dataclass, field
E L5: pathlib import Path
E L6: weakref import WeakSet
E L8: faceless_champ import SubtitleTrack
E L9: faceless_champ.audio import AudioClip
E L11: facelesschamp_kit.diagnostics import KitError, number
L L246: facelesschamp_kit.compiler import compile_video
```
