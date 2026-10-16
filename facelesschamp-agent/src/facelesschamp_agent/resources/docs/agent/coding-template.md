# Default coding tutorial design

The coding tutorial design approved from the Hello World opening is stored in
the kit's `tutorials/coding/` folder. It contains `style.json`, `TEMPLATE.md` and
reusable component factories. Lesson code, narration and source cue timing stay
in the authored project.

## Selection and precedence

```bash
fc-agent --project my-video plan --prompt "Teach a Python coding tutorial"
```

When no custom direction is provided, the returned `template` points to a copied
`templates/coding-tutorial/` folder. The selection artifact records
`design.template: "coding-tutorial"` and directing guidance. Carry that design
marker into agent-plan.json when authoring the actual video.

An explicit `--design` object (even `{}`), `--instructions`, project constraints,
existing custom project design, or known design/instruction files bypass this
automatic default. Untouched agent starter settings are recognized as defaults.
Prompts with explicit style terms also bypass it. External authors must pass
custom prose direction through `--instructions`/`--design` and follow it first;
keyword matching is not a substitute for understanding user instructions.
The current approved layout targets landscape. Portrait requests use their own
composition and do not receive this fallback automatically.

## Edit the design

```json
{
  "background": "#F4F1EB",
  "accent": "#517AEE",
  "editor_background": "#151820",
  "code_size": 54,
  "editor_scale": 0.64
}
```

Change these fields in the copied style.json; unspecified fields use the approved
defaults. Also available: editor chrome/text colors, connector and Python emblem
colors, insets, terminal size, shrink/restore/terminal durations and springs.
Edits load on every build, survive planning runs, and invalidate cached plans and
media/review fingerprints. Invalid values produce TUTORIAL_STYLE.

```python
from facelesschamp_agent import AgentProject, load_coding_tutorial
from facelesschamp_kit import BlockBuild

def workspace(ctx, bounds):
    template = load_coding_tutorial(ctx.root)
    editor, code, caret = template.editor('print("Your lesson")', filename="lesson.py")
    return BlockBuild(template.group(editor, bounds=bounds),
                      {"editor": editor, "code": code, "caret": caret})

def build(ctx):
    video = AgentProject(ctx.root).new_video(ctx)
    segment = video.segment("lesson", duration=6)
    handle = segment.add_core(workspace, enter=None, exit=None)
    # Author visibility, source reveal and motion on the lesson's cue clock.
    return video
```

`group` fits the reference canvas uniformly into kit bounds, retaining child
coordinates. Build the complete hierarchy in the factory. Helpers return fresh,
initially hidden editor/terminal components; author entrances and code reveals
explicitly. Never execute displayed code during playback. Python emblems and
Finder introductions are optional teaching choices.

## Render options

```bash
python my-video/render.py --fps 60 --quality high
python my-video/render.py --full --fps 30 --quality 4k
fc-agent --project my-video preview -o output/review.mp4 --fps 48 --quality low
```

`low`, `high`, and `4k` select 720p, 1080p and 2160p, preserving aspect ratio.
Quality does not select the full film; `--full` does that. Overrides are used in
verification expectations and never rewrite facelesschamp.toml. Without overrides,
the preview/final profile remains in force. `entrypoint` preserves custom renderers.

Generated renderers and the fc-agent preview/render commands show a frame progress
bar, elapsed time and estimated time remaining on stderr, keeping stdout JSON
parseable. ETA uses observed export throughput; Finalizing covers the encoder's
last work after all frames have been sent. Success appears after export returns.
`--full` exports the complete authored timeline, including every scene.

For Python integrations, pass `progress(completed_frames, total_frames)` to
`AgentProject.preview()` or `render()`. The core `ExportProgress` context manager
provides the same terminal display without adding a progress dependency:

```python
from faceless_champ import ExportProgress

with ExportProgress() as progress:
    project.render(progress=progress, fps=60, quality="high")
```
