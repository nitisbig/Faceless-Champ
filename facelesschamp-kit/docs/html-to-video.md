# HTML walkthrough blocks

Install the matching core and kit sources with the `web` extra and explicitly install
Chromium (see the core HTML-to-video guide). Prepare captures using
`faceless_champ.web.capture_html` before compiling a kit video.

```python
from faceless_champ.web import WebCapture, WebFocus, WebHighlight, WebCallout
from facelesschamp_kit.blocks import WebWalkthrough, WebElement

capture = WebCapture('path/to/prepared/capture')
block = WebWalkthrough(
    capture, title='Product tour', cursor=True,
    highlights=(WebHighlight('#search', 1, 3),),
    focuses=(WebFocus('#search', 3, 6, zoom=1.5),),
    callouts=(WebCallout('Find what you need', 1, 4),),
)
# Use block with segment.add(block), like other kit blocks.
# A separate reusable crop:
element = WebElement(capture, '#search', source_start=3)
```

Track selectors in the core `WebScript` before capture. Blocks fit into their allocated
bounds and create fresh components on every compose. `WebWalkthrough` exposes named children
`page`, `chrome`, and `title` (the latter two when `browser_chrome=True`); `WebElement` exposes
`element`. Use ordinary kit motion on the block or its named children.

`source_start` offsets capture playback; focus/highlight/callout times still refer to the
original capture clock. Disable chrome with `browser_chrome=False`, or cursor with
`cursor=False`. Selectors follow their captured visible bounds through scrolling and zooming.
Callout text is fitted inside the viewport; use short phrases for legibility.

No browser starts during `compose`, kit compilation, or export. Preparation is an explicit
step in the project runner. Use core sparse captures for storyboards and source-time ranges
for preview; prepare every frame needed by the eventual render before exporting.

The complete example is in `training project/web-video`: its `main.py` combines kit blocks
and core scheduling, while `render.py` owns preparation and export. No backend, live URL,
API key, or narration is needed.
