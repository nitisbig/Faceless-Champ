# CodingChamp

CodingChamp renders source code inside an editor surface using the ordinary Pillow renderer.
Install syntax highlighting with `pip install 'facelesschamp-kit[coding]'` (or `uv pip install -e . -e ./facelesschamp-kit[coding]`).
`language="text"` is the dependency-free default. Set a Pygments language alias such as `python`,
`javascript`, or `typescript` to color syntax. This editor displays source without executing it. For explicit checkpoint execution and side canvases,
see [CodingChamp playgrounds](coding-playgrounds.md).

```python
from faceless_champ import Canvas, Scene
from facelesschamp_kit.coding import CodingChamp, CodeReveal

scene = Scene(Canvas(1920, 1080, "#080E1B"))
code = CodingChamp(
    'class Player:\n    health = 100',
    language="python", theme="midnight", filename="player.py",
    width=1500, height=720, font_size=48, position=(960, 540),
    reveal_mode="typewriter", highlighted_lines=(2,),
)
scene.play(CodeReveal(code), run_time=2)
scene.wait(1)
```

## Editor and themes

`CodingChamp(code, *, language="text", theme="midnight", width=1200, height=720,
font_size=32, font=None, filename="", chrome=True, line_numbers=True,
highlighted_lines=(), reveal_mode="typewriter", reveal=1, block_ends=None, first_line=1,
tab_size=4, padding=28, **component_options)` is a standard Component.
It supports position, anchor, scale, rotation, opacity, groups and masks.
`first_line` changes displayed numbering; highlighted lines and block ends always use
local, one-based line numbers. Tabs advance to tab stops without changing the source.
Configure the component before adding it to a scene; scenes snapshot its state.

The bundled DejaVu Sans Mono font uses the included `assets/FONT-LICENSE.txt`.
Use `font=` for another local font. Text layout is measured before animation: the
editor and glyph positions do not move while text is revealed. Oversized code raises
an error with suggestions to use a shorter excerpt, enlarge the panel, or reduce font size.
There is no implicit wrapping, scrolling, or execution.

`CodeTheme.named("midnight")`, `"ocean"`, and `"paper"` provide dark, teal, and light
palettes. `"clean-flow"` uses a charcoal editor and chrome, orange accent, and
restrained syntax colors alongside the light clean-flow card style. Customize
immutable themes with `dataclasses.replace`, for example:

```python
from dataclasses import replace
from facelesschamp_kit.coding import CodeTheme

theme = replace(CodeTheme.named("midnight"), accent="#FFCF70",
                syntax={"Keyword": "#C6A0F6", "Literal.String": "#A6DA95"})
```

Theme fields are `background`, `chrome`, `foreground`, `muted`, `accent`, `highlight`,
and `syntax`. Syntax keys follow Pygments token names without `Token.`; child token
categories inherit their nearest configured parent. Unmapped tokens use `foreground`.
Unknown languages and missing optional dependencies raise explicit errors; select
`language="text"` deliberately for plain code or console output.

## Reveal effects

- `typewriter`: successive source characters, including whitespace.
- `word`: successive whitespace-separated words, with adjacent whitespace preserved.
- `block`: successive groups ending at `block_ends`; defaults to one complete line per step.
  For four lines, `block_ends=(1, 2, 4)` reveals three groups. Ends must strictly increase
  and include the final line. A trailing newline does not add an extra blank group.

`CodeReveal(panel, start=0, end=1)` uses linear, normalized progress. It leaves chrome
and line numbers visible. Text defaults to fully visible when no reveal animation is authored.
Pass `reveal=0` (or set `panel.reveal` before adding it) to initialize hidden code;
values in `[0, 1]` are snapshotted when the panel joins the scene. Later changes use
`CodeReveal` or the timeline's normal reveal animation.
To pause between blocks, animate 0→1/3, hold, then 1/3→2/3, and finally 2/3→1.
Use ordinary `Scene.at`/`CueScene.at_cue` for narration timing. Effects have no implicit clock.

Tokenization and geometry are prepared once per component. `PillowRenderer(code_cache_mb=32)`
bounds the cached full editor/ink layers; intermediate reveal frames are not retained there.
Set `code_cache_mb=0` and `frame_cache_mb=0` to disable both code and held-frame caches.

## Saved clean-flow workspace design

`CodeWorkspaceDesign.named("clean-flow")` provides reusable editor and terminal
geometry, chrome and motion helpers. It contains no lesson content or execution.
The editor scales uniformly to 64% for the terminal arrangement. At 1920×1080,
the saved layout uses a 48px outer margin and a 32px window gap. Whole-window
transforms include the code, chrome, highlights and shadow.

The saved timings are 0.8s to shrink, 0.6s for terminal entrance, 0.45s for terminal
exit, and 0.9s to restore the editor. The monotonic `design.fluid` easing settles
without overshoot. Code, chrome, highlights and shadow share the window transform.
Only source, window labels, commands and output need appear on screen.

```python
from faceless_champ import Canvas, Scene
from facelesschamp_kit.coding.workspace import CodeWorkspaceDesign
from facelesschamp_kit.coding import CodingChamp

design = CodeWorkspaceDesign.named("clean-flow")
scene = Scene(Canvas(1920, 1080, design.background))
box = design.code_bounds
code = CodingChamp(
    'print("Hello, Python!")', language="python", theme=design.theme,
    chrome=False, font_size=design.code_size * design.unit, padding=8 * design.unit,
    width=box.width, height=box.height,
    position=(box.left, box.top), anchor="top_left",
)
editor = design.window(design.editor_full, "functions.py", children=(code,), fullscreen=True)
# Add the complete hierarchy before animating its code or highlights.
scene.add(editor)
scene.play(
    design.editor_motion(editor, running=True),
    *design.editor_corners(editor, running=True),
    run_time=design.shrink_duration,
)
# After the terminal exits, restore with running=False and restore_duration.
```

`CodeWorkspaceDesign(bounds=Bounds(...))` adapts the layout to an allocated region;
`unit` scales the typography and chrome from the 1920×1080 reference. `editor_full`,
`editor_split`, `terminal_bounds`, and `code_bounds` expose the layout. Customize
the immutable design with `dataclasses.replace`; the default remains the saved look.
Allocations must leave at least `192 * unit` of terminal width for window chrome;
an `editor_scale` that leaves less room raises `ValueError` during design construction.

`CodeWindow` is an ordinary `Group` built by `design.window(...)`. It exposes
`face`, `header`, `heading`, `shadow`, and `bounds_box` (the face allocation).
Direct window faces also require at least `192 * unit` width. Long or multiline
titles scale down uniformly to stay within the header, preserving their text.
Pass chrome-free content as `children` when constructing it. Build a terminal with
`design.window(design.terminal_bounds, "Terminal", children=(command, output))`,
then animate it with `design.terminal_in(window)` / `design.terminal_out(window)`.
The caller schedules typing, output publication, visibility and durations; these
helpers never run code or add audio. Existing editor/playground defaults are unchanged.

The current [approved coding reference](../examples/programming/hello_world/README.md)
uses these public helpers. Its lesson content and timing remain local. Reusable template data lives in the kit.
In Kit projects, return a fresh complete hierarchy from a `Segment.add_core` factory.

For default agent coding tutorials, see the [approved template collection](../templates/README.md).
The kit exposes CodingTutorialStyle and CodingTutorialTemplate; each agent project
gets editable style.json data. Custom design/instructions bypass automatic selection.
