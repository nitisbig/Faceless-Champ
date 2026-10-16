# Clean-flow

Select `theme = "clean-flow"` in a video's `facelesschamp.toml` configuration. The design uses a warm gray `#E8E6E2` canvas, a subtle dot grid, white rounded cards with soft shadows, orange `#FF5A20` accents, black DM Sans headings, and charcoal code editors. DM Sans and its OFL license are packaged with core; rendering downloads nothing.

```python
from facelesschamp_kit import Video
from facelesschamp_kit.blocks import Heading, MetricCard

def build(ctx):
    video = Video(ctx)
    with video.segment("overview", duration=4) as segment:
        segment.add(MetricCard(42, "Prepared results"))
    with video.segment("next", duration=3) as segment:
        segment.add(Heading("Keep it clear"), enter="fade", exit="flow")
    return video
```

## Motion

`Segment.add` and `add_core` default to `enter="theme", exit="theme"`. Clean-flow resolves both to `flow`; the other built-in themes resolve both to no motion. Explicit `enter=None` or `exit=None` disables one side. Existing entrance recipes remain available, and `exit="fade"` is available for a simple outro.

Each flow side occupies `theme.motion_duration` (0.6 seconds): an opacity change and a 24-design-pixel upward slide with easing. Nested groups reveal their leaves in stable authoring order; exits reverse that order. Stagger gaps default to 0.06 seconds and are capped to 35% of the total window, so large groups still complete on time. Native OS, HTML, code, FlowChamp, chess and ArchChamp clips retain their internal scripted playback and flow as outer viewports.

Entrances restore authored positions and opacity; outros start from the current timeline state. Entrance and outro windows must fit without overlapping. Position/opacity animations authored inside those windows conflict normally; disable that side when supplying your own reveal. `enter_duration` and `exit_duration` override individual windows.

Use overlapping segment windows for major transitions: for a nominal boundary at 6 seconds, finish outgoing content at 6.3 seconds and begin incoming content at 5.7 seconds. Their 0.6-second motion windows overlap over the same interval. Keep the final end at the intended duration. The compiler's common dot-grid backdrop persists across segments, with one entrance and final outro.

## Surfaces and overrides

The theme supplies body weight 400, heading/metric weight 700, card radius 44, and `ShadowStyle(color="#00000026", blur=16, offset=(0, 12))`. Core `card_surface` creates an in-memory image once during composition, including 60 pixels of transparent shadow clearance inside each allocated edge. Use `card_content_bounds` to place contents within that face; its default content padding adds 28 pixels. Cards therefore need more space than their visible content. Tight allocations fail rather than clipping their shadow or text. Charts placed on these surfaces should use a transparent chart background and fit inside the content bounds.

Explicit code themes, OS presets, chess themes and Arch styles override defaults. Clean-flow playgrounds use the selected code palette for editor, result canvas and console. Captured HTML retains its authored CSS, so use the clean-flow colors and local font while preparing the page.

```python
from dataclasses import replace
from facelesschamp_kit import CLEAN_FLOW

ctx.theme = replace(CLEAN_FLOW, background_pattern=None, motion_distance=16)
# A regular custom font has no variable Weight axis:
ctx.theme = replace(ctx.theme, font="assets/custom.ttf", font_weight=None, heading_weight=None)
```

Theme tokens are per-build and immutable. Existing themes retain their colors, fonts, panel rendering and motion defaults.
