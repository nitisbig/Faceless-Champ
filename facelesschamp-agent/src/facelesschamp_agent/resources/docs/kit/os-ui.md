# OS UI tutorials

The framework provides `OSWalkthrough`, `FinderWindow`, and `SettingsWindow` in
`facelesschamp_kit.blocks`. They use the public core `faceless_champ.os_ui` API.

```bash
fc-kit init my-tutorial --template os-ui
fc-kit --project my-tutorial validate main
fc-kit --project my-tutorial preview main -o output/os-preview.mp4
fc-kit --project my-tutorial render main -o output/os-final.mp4
```

The starter is a 35-second landscape tutorial with virtual files, navigation, rename,
previews, drag-and-drop, trash/restore, settings, and window controls. Edit
`videos/main.py`; the tree and script are ordinary Python data. No assets need downloading.

```python
from faceless_champ.os_ui import OSScript
from facelesschamp_kit import Video
from facelesschamp_kit.blocks import SettingsWindow


def build(ctx):
    video = Video(ctx)
    script = OSScript().set_value("appearance:theme", "dark").wait(1)
    with video.segment("settings", duration=script.duration) as segment:
        segment.add(SettingsWindow(script=script))
    return video
```

Each block accepts `filesystem`, `script`, `preset`, `pages`, `source_start`, and
`cursor`. The default desktop design viewport is 1920×1080; isolated windows use
1280×800. Set `viewport=(width, height)` to change the design space. Blocks fit
proportionally inside their allocated bounds, including portrait layouts, and create
independent instances on every composition. `handle["ui"]` addresses the core clip
for normal framework transforms and opacity animations.

Scripts are local to the placement start. `segment.add(..., at=2)` starts script time
zero two seconds into the segment; `source_start=1` instead begins at script time one.
For cue timing, subtract the placement offset from `segment.cue_time(index)` and add
`source_start` when authoring an explicit action time. Preserve the narration source
clock and original cue timestamps.

A script's remaining duration must fit the authored placement. Overflow raises
`MOTION_WINDOW`; a narration tail hold cannot make an overflowing script valid.
Use a shorter script or an explicitly longer segment. Do not silently speed up actions.

See the core [OS UI guide](../../docs/os-ui.md) for supported actions, stable target IDs,
custom settings controls, timing, transparency, and simulated-system boundaries.
