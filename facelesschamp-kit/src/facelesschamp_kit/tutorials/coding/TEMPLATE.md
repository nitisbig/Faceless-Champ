# Coding tutorial design

Approved from the Hello World opening on 2026-10-16. This is a reusable visual
design, not a lesson script or a fixed 14.96-second timeline.

Use this fallback only for landscape coding tutorials with no custom design or
instructions. Explicit user direction and existing custom project design win.
Read narration first; choose which of the helpers teach each beat. Never insert
the Hello World program, its timings, narration or Python emblem into unrelated
lessons. The emblem is appropriate for Python; other languages need suitable art.

The project-owned `templates/coding-tutorial/style.json` is editable. Change
`background`, `accent`, editor colors, typography, insets, scale or spring tuning.
Edits are loaded on each build and participate in evidence fingerprints. Recheck
layout after changing geometry. Keep explicit plan palette overrides consistent.

```python
from facelesschamp_agent import load_coding_tutorial

template = load_coding_tutorial(ctx.root)
editor, code, caret = template.editor(source, filename="lesson.py")
terminal, output = template.terminal(authored_output)
```

Factories return fresh core components. Group children before scene ownership.
`template.workspace`, `window_spring` and `icon_spring` expose the approved layout
and motion. `emblem()`, `finder(filename, source)` and `flow()` support the opening
journey; use them only where they explain the lesson. Author timing yourself.
Use core `Scene.at`/`CodeReveal`. For kit scenes, return a complete hierarchy
from `Segment.add_core`, wrapped with `template.group(..., bounds=bounds)`. This
uniformly fits the reference canvas into the allocation while retaining child
workspace coordinates. Disable implicit kit entrances/outros when authoring them.
Set `design.template` to `"coding-tutorial"` in agent-plan.json only when this
fallback was selected; start `build(ctx)` with `AgentProject(ctx.root).new_video(ctx)`.

Show code, filenames, necessary OS labels and output. Omit headings, captions and
explanatory overlays by default. Keep whole-window motion uniform and reserve
shadow clearance. Spring applies to transforms; fades/reveals use ordinary easing.
Output is authored unless explicitly prepared checkpoints are required. Never
execute displayed source during playback. Attach supplied narration once at zero.

Generated render.py supports `--fps` and `--quality low|high|4k`, independently
of preview/full duration. Honor requests to deliver source without rendering.
