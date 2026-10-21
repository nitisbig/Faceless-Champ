# Raster sources and animation extensions

Core supports custom raster viewports on Pillow, Skia and ModernGL. The base
installation still needs only Pillow. Integrations supply a deepcopy-safe input
descriptor and open renderer-owned sessions when pixels are requested.

```python
from dataclasses import dataclass
from PIL import Image
from faceless_champ import Canvas, Scene, Viewport, save_frame


@dataclass(frozen=True)
class Swatch:
    intrinsic_size = (160, 90)
    duration = 2.0
    fingerprint = "example:swatch:v1"
    requirements = ()

    def frame_key(self, source_time):
        return int(source_time * 10)

    def open(self, size):
        class Session:
            def frame(self, source_time):
                step = int(source_time * 10)
                return Image.new("RGBA", size, (20 + step * 8, 80, 180, 255))

            def close(self):
                pass

        return Session()


view = Viewport(Swatch(), width=320, height=180, position=(320, 180))
scene = Scene(Canvas(640, 360)).add(view).wait(2)
save_frame(scene, 0.5, "swatch.png", size=(640, 360))
```

The public contracts are `RasterSource`, `RasterSession` and `Viewport` in
`faceless_champ.sources`, also available from the lazy package root. Structural
typing suffices; no inheritance or registration is required.

- A source declares positive integer `intrinsic_size`, positive finite `duration`
  or `None`, a nonempty `fingerprint`, and a tuple of requirement names.
- Omit both viewport dimensions to use intrinsic size, or supply both. Viewports
  use ordinary component transforms, lifetimes, masks, opacity and effects.
  Adding one does not advance the scene cursor.
- Component age maps to `source_start + max(0, age)`, clamped at a finite source's
  duration. `source_start` may equal that duration for a terminal hold.
- `frame_key(t)` must be pure and hashable. Equal keys for the same fingerprint
  and sampling size must mean equal pixels. Include every input affecting pixels
  in the fingerprint. The session receives the requested timestamp, never the key.
  Quantization belongs to the source; Core imposes no universal source FPS.
- `open(size)` returns a session owning its native resources. `frame(t)` returns
  an independent Pillow image in straight-alpha RGBA/sRGB at exactly that size.
  Sessions must support arbitrary sampling order. A failed `open()` must clean up
  any partial allocation itself. A failed frame closes its session automatically.
- Dimensions and layout never open a source. Target sampling size follows viewport
  size and output density; ancestor scale is applied during compositing. Renderer
  close, size/session eviction and frame errors release owned sessions. Decoded
  frame retention is bounded by bytes and session retention by count; these limits
  do not measure a native library's internal allocations or total process RSS.
- Descriptors contain inputs and immutable prepared data, never live plotters,
  browsers, GPU contexts or open handles. Scene snapshots isolate later descriptor
  mutation. Keep preparation outside frame evaluation. Requirement names are
  metadata for the integration; the integration reports its own missing engines
  when opened. Core does not install packages automatically.

Existing FlowChamp, browser, OS and scientific viewport APIs remain usable.
Their internal adapter preserves domain frame keys, source ranges and endpoint
policies; their package extraction and removal decisions belong to later phases.
Scientific sessions retain VTK isolation and floating-point environment guards.

## Animation extension hooks

`Component.validate_animation(property, value)` validates Core-owned state keys.
A custom component overrides its own keys and delegates the rest to `super()`.
Scene calls the hook for resolved starts, targets and keyframes before publishing
any tracks. Unknown keys are rejected. Chart, Map, Group and Countdown enforce
their own additional rules through this hook.

`Animation.resolve(state)` returns a detached animation description. Overrides
may normalize a request against current state at scheduling time, as Map's
shortest longitude route does. Keep this method pure: do not mutate the input
state, component, original animation or scene. Return an animation for the same
component. The default copies target/start/keyframe containers. Normal relative
transforms and Spring certification still run after resolution. Components that
offer additional additive relative numeric properties declare them through
`relative_animation_properties`; the default is position, scale and rotation.

The compiled scene and frame records in `_rendering` are private. Existing custom
renderers still implement just `validate(renderable)` and `frame(renderable,
time, size)`. They receive public Scene/Sequence/Grid/Layer objects and remain
caller-owned when supplied to a preview/export helper.

## Raw subtitle cues

`faceless_champ.parse_srt_cues(text)` returns immutable `SubtitleCue` records,
preserving source overlaps, cue numbers and multiline content. It rejects invalid
timestamps, duplicate numbers and descending start times. `SubtitleTrack` retains
its separate overlap-tolerance policy. Kit exposes the same operation as
`read_subtitle_cues(text)`. Agent uses that facade and retains its input byte/cue
limits, structured diagnostics and whitespace normalization.
