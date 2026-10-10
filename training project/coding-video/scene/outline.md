# Python classes — source-clock outline

The video demonstrates one idea: a class bundles data and behavior, while each instance owns its state.
No chapter titles or subtitles appear in the film. Code, filenames, console results and short diagram labels are the only text.

| Original cues | Source seconds | Visual proof |
|---|---|---|
| 1–51 | 0–18.440 | Two player cards; duplicated variables accumulate; Player consolidates them. |
| 52–87 | 18.440–29.720 | One blueprint produces multiple houses, then one class produces objects. |
| 88–139 | 29.720–46.840 | Type class Player and __init__; focus the double underscores and creation path. |
| 140–189 | 46.840–63.360 | Name and 100 HP attributes; self connects to separate object cards. |
| 190–253 | 63.360–84.200 | Reveal damage, heal, and status methods as distinct code blocks. |
| 254–278 | 84.200–91.960 | Highlight data and behavior together in the class. |
| 279–334 | 91.960–110.640 | Instantiate Alex, then Sam; each owns 100 HP. |
| 335–373 | 110.640–124.840 | Alex 100→70→85, then Sam 100→90; console prints final states. |
| 374–447 | 124.840–151.464 | Highlight class, instance, attributes, methods and self; hold through audio tail. |

Read snippets from class.py through AST source spans, never importing it. Calls are presented in spoken order:
Alex damage, Alex heal, Sam damage. The reference orders Sam damage before Alex heal; independence makes the final states identical.
Preserve audio.mp3, both SRT files, and class.py. cue-per-word.srt alone controls visual timing.
Every transition starts at an original cue boundary and completes inside its authored window.
Use a 1920×1080 design canvas; split code and diagrams with at least 60 px outer margins.
Validate the entire timeline structurally, then a storyboard and short source-clock excerpts only.
