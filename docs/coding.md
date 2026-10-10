# CodingChamp

CodingChamp renders source code inside an editor surface using the ordinary Pillow renderer.
Install syntax highlighting with `pip install 'faceless-champ[coding]'` (or `uv sync --extra coding`).
`language="text"` is the dependency-free default. Set a Pygments language alias such as `python`,
`javascript`, or `typescript` to color syntax. Source is displayed, never executed.

```python
from faceless_champ import Canvas, Scene, CodingChamp, CodeReveal

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
highlighted_lines=(), reveal_mode="typewriter", block_ends=None, first_line=1,
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
palettes. Customize immutable themes with `dataclasses.replace`, for example:

```python
from dataclasses import replace
from faceless_champ import CodeTheme

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
and line numbers visible. Text starts fully visible when no reveal animation is authored.
To pause between blocks, animate 0→1/3, hold, then 1/3→2/3, and finally 2/3→1.
Use ordinary `Scene.at`/`CueScene.at_cue` for narration timing. Effects have no implicit clock.

Tokenization and geometry are prepared once per component. `PillowRenderer(code_cache_mb=32)`
bounds the cached full editor/ink layers; intermediate reveal frames are not retained there.
Set `code_cache_mb=0` and `frame_cache_mb=0` to disable both code and held-frame caches.

See `examples/coding/showcase.py` for staged blocks and `training project/coding-video`
for a complete narrated tutorial with export controls. Existing `Text`/`Typewriter` APIs are unchanged.
