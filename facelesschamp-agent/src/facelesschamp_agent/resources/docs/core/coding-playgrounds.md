# CodingChamp playgrounds

CodingChamp can pair an animated editor with actual web output, concept illustrations,
or backend/AI data. Authors supply complete source revisions and explicitly bind results
to visuals. It does not infer diagrams from arbitrary code.

Install `faceless-champ[playground]` for core authoring or
`facelesschamp-kit[playground]` for the kit. For web captures, separately run
`python -m playwright install chromium`. Python and prepared-asset playback do not
need a browser. Syntax-colored editors require the `coding` extra.

## Start with the kit

```sh
fc-kit init lesson --template coding-concept
cd lesson
fc-kit prepare main
fc-kit validate main
fc-kit frame main --time 4.4 -o output/frame.png
fc-kit preview main -o output/preview.mp4
fc-kit render main -o output/main.mp4
```

Other templates: `coding-web` and `coding-backend`. Each starter is an editable
six-second project with two complete revisions. The concept example creates two
independent cars; the backend example executes a small matrix/vector calculation;
the web example changes CSS and clicks an actual browser button.

`prepare` is the only kit operation that executes checkpoints. Build, validate,
inspect, frame, storyboard, preview, and render require a prepared asset and do not
start Python programs or browsers. Changes to sources, inputs, timing, bindings, or
preparation settings require another preparation. Use `fc-kit prepare main --refresh`
to explicitly run again even when the input fingerprint matches.

Preparation results are reported under `prepared_assets` with their fingerprint and
path. Errors retain `PLAYGROUND_*` codes and checkpoint/placement context through
`--json`. An unprepared lesson fails with `PLAYGROUND_UNPREPARED` and a preparation
instruction. Successful preparation is not a claim that a video export was verified.

## Core authoring

```python
from faceless_champ import (
    Canvas,
    CanvasItem,
    CodeCheckpoint,
    CodeEditor,
    PlaygroundCanvas,
    PlaygroundOutput,
    PlaygroundScript,
    Scene,
    ValueBinding,
    prepare_playground,
)

source = """from faceless_champ.playground.runtime import emit
x = 6 * 7
emit("answer", x)
print(x)
"""
script = PlaygroundScript(
    [CodeCheckpoint("answer", {"main.py": source}, "main.py", "main.py", edit_start=0, edit_end=1, publish=1)],
    duration=3,
    mode="backend",
    items=[CanvasItem("answer", "variable", "Answer")],
    bindings=[ValueBinding("answer", "answer")],
)
asset = prepare_playground(script, cache_dir=".playground-cache")
scene = Scene(Canvas(1920, 1080, "#0B1020"))
scene.add(CodeEditor(script, width=880, height=950, position=(500, 540)))
scene.add(PlaygroundCanvas(asset, width=850, height=700, position=(1420, 410)))
scene.add(PlaygroundOutput(asset, width=850, height=200, position=(1420, 890)))
scene.wait(script.duration)
```

`PreparedPlayground(path)` loads and verifies the saved asset without executing its
sources. Prepared assets contain the full source revisions, inputs, results, runtime
identity, and hashed browser frames. Keep the complete directory when moving it.

## Code edits and clocks

`CodeCheckpoint` declares an id, complete `files` mapping, `active_file`, `entrypoint`,
`edit_start`, `edit_end`, and `publish`. Paths are project-relative POSIX paths;
contents are text, copied without newline normalization. Files omitted from the next
revision disappear. The active editor file must belong to that revision.

Checkpoints are ordered: `edit_start <= edit_end <= publish < duration`. An edit
cannot begin before the preceding publication. A zero-length edit switches immediately.
The first revision starts from empty text; later revisions diff the previous version
of the active file, even when switching files. Deletions, insertions, and replacements
are evaluated directly from time. Final source matches the executed revision exactly.
Only completed revisions run; intermediate text does not execute.

The previous output holds until the next publication. Before the first publication,
the result canvas and console are empty. `first_line` explicitly scrolls the editor
when that revision begins; line numbers remain source-relative. Vertical overflow is
viewed through this fixed viewport. Horizontal overflow raises an actionable layout
error; use shorter lines, a wider editor, or a readable smaller font. Changed lines
are emphasized. No wrapping or automatic scrolling changes the source.

All core viewports accept `source_start`, transforms, opacity, groups, and masks.
`EditTimeline.state_at(seconds)` exposes source and changed-line state for inspection.
Rendering can seek forward or backward and start at any excerpt time.

In the kit, `coding_playground(ctx, script, start=...)` places the script at an absolute
video time; checkpoint times are relative to that segment. Supply `audio`, `subtitles`,
`markers`, and `cues=(start_marker, end_marker)` to use existing narration windows.
The window must fit the script; any extra window time holds the final result. No
source audio is shifted or stretched. Captions are controlled by the existing project
setting, and starters add neither titles nor subtitles.

## Executing and binding Python

Each checkpoint runs in a fresh subprocess and temporary project directory, with
`runtime="python"`. Import these helpers in the authored program:

```python
from faceless_champ.playground.runtime import emit, event, inputs

emit("car", {"speed": 40, "color": "red"})
event("accelerated", {"amount": 40})
```

`inputs()` returns the checkpoint's declared JSON object. `emit` names must be unique
within a run; data must be finite JSON. `event` records preserve execution order.
Stdout, stderr, and exit status are also captured. There is no implicit object tracing
or persistent state between runs. Normal imports from the current Python environment
and sibling source files work; dependencies are never installed automatically.

`CanvasItem(id, kind, label, value, color)` supports:

| Kind | Bound value |
| --- | --- |
| `car`, `object` | Object with property names and values |
| `flow`, `variable` | JSON value; null may leave the node label-only |
| `collection` | Array or object |
| `vector` | Nonempty array of finite numbers |
| `matrix` | Nonempty rectangular array of finite numbers |

`ValueBinding(key, target, property="value")` maps one emitted key to a canvas item.
Other bindable properties are `label` and `color`, both strings (colors are validated).
Missing keys, incompatible values, unknown targets, and duplicate property bindings
fail preparation. Unbound items use their authored static value.

`EventBinding(checkpoint, event, target, at, duration=.6, to=None, cell=None)` emphasizes
a target. Set `to` to animate a travelling event to another item, or use
`cell=(row, column)` for zero-based tensor-cell emphasis (vectors use row zero).
The named event must occur exactly once in its run. Authored event times must preserve
execution order and fit within the checkpoint output window; execution wall time does
not control video time. Event payloads remain available in the prepared results.

Canvas labels and numbers never shrink below the configured minimum. Oversized data
raises a layout error; show a smaller collection or tensor, or allocate more space.
The console wraps text and displays its latest visible lines, marking omitted earlier
output. Complete logs remain in the prepared results.

## Web revisions

Set `mode="web"` and `runtime="web"`; supply HTML, CSS, and JavaScript together in
`files`. Use an HTML entrypoint, `ready=("#selector", ...)`, and an optional existing
`WebScript` for clicks, typing, scrolling, or readiness checks. Its duration must cover
the interval from publication to the next publication (or the lesson end).

Every revision gets a fresh local page. The existing offline browser-capture engine
prepares pixels at the requested FPS; later video exports replay them without a
browser. Browser console messages follow capture time. JavaScript errors, console
errors, blocked external requests, and failed HTTP responses are captured as errors.
Local source assets are supported; live remote services and framework development
servers are outside this release.

## Execution boundaries and cache behavior

`prepare_playground` accepts `timeout=10` seconds per checkpoint,
`output_limit=1_000_000` bytes, `fps=15`, and `refresh=False`. Source programs are
**trusted local code**: a subprocess is not a security sandbox. They retain the user's
OS permissions. Python runs use bounded output files and POSIX file-size limits;
process groups are terminated on timeout, interruption, and completion on POSIX.
Windows terminates the direct worker process. Browser preparation also runs in a
killable worker with a total checkpoint deadline.

Unexpected program errors stop preparation. `expected_failure=True` explicitly
accepts a nonzero execution result for an error lesson; success is then an error.
Infrastructure failures, invalid emissions, timeouts, and output-limit failures are
never treated as a successful expected failure. Failed results display diagnostics,
not stale successful values. No incomplete preparation directory becomes public.

Fingerprints cover the script, inputs, settings, implementation, and runtime identity.
Refresh creates a new immutable generation so existing readers retain their asset.
Corrupt prepared data is rejected rather than silently re-executed; explicitly prepare
with refresh to repair it. Rendering is repeatable from prepared assets; arbitrary
programs using clocks, network, or random external inputs are not promised reproducible
across separate preparations.

## Kit composition

`ctx.playground(script, ...)` declares a dependency resolved by `Project.prepare()`.
`CodeEditor` and `CodingPlayground` are exported from `facelesschamp_kit.blocks`.
`CodingPlayground` has `layout="side"|"stacked"`, `code_ratio=.5`, `font_size=24`,
`theme="midnight"`, `output=True`, and `source_start=0`. Named children are `editor`,
`canvas`, and optional `output`, usable with ordinary kit animations. Composition
belongs to the kit; preparation, source edits, pixels, and result validation belong
to core. Existing display-only `CodingChamp` and `CodeReveal` remain unchanged.
