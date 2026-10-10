# HTML to video

`faceless-champ` 0.1.2 provides optional browser preparation and browser-free scene playback.
`facelesschamp-kit` provides presentation blocks. Supply a local HTML app and its assets;
the application must work without a backend or external requests.

## Installation

From the repository root:

```bash
uv pip install -e '.[web]' -e './facelesschamp-kit[web]'
.venv/bin/python -m playwright install chromium
```

Chromium is an explicit extra download, never downloaded on import or render. FFmpeg is
required for MP4 export as usual. Use the same Python environment for installation and capture.
The default core and kit imports work without Playwright installed.

## Author interactions, prepare, compose

```python
from faceless_champ import Canvas, Scene
from faceless_champ.web import HtmlPage, WebScript, capture_html, HtmlClip

page = HtmlPage('ui/index.html', viewport=(1440, 900),
                storage={'theme': 'light'}, ready=('#prompt-input',))
script = WebScript(duration=12)
script.move('#prompt-input', at=1, duration=.5)
script.click('#prompt-input', at=1.5)
script.type('#prompt-input', 'Explain async JavaScript', at=2, duration=2)
script.click('#send', at=4.5)
script.track('.composer')
capture = capture_html(page, script, fps=30, cache_dir='.web-cache')
scene = Scene(Canvas(1920, 1080, '#101827'))
scene.add(HtmlClip(capture, width=1440, height=900, position=(960, 540)))
scene.wait(12)
# Export explicitly when ready:
# scene.render('tour.mp4', fps=30)
```

`HtmlPage.asset_root` defaults to the HTML's directory. Declare a common root when using
sibling assets. An isolated localhost server serves only that root; external requests fail
with a diagnostic. Sources outside the root and escaping symlinks are rejected. Only use
HTML you trust: offline resource restrictions are not a security sandbox for hostile code.

`WebScript` supports `move`, `click`, `type`, `press`, `select`, `scroll`, `assert_ready`,
and `track`. Selectors are CSS selectors and must identify exactly one visible, enabled
action target. `type` appends text progressively and emits input events. `press` accepts
Playwright key names such as `Enter` or `Control+A`. `select` uses an option's value.
`scroll(selector, at=..., x=0, y=..., duration=.7)` interpolates to absolute element scroll
coordinates. Use a scroll container selector. Action times are seconds on the capture
clock; simultaneous or overlapping input actions are rejected. Adjacent actions are allowed.
Explicit movement animates the cursor; click alone moves it immediately to the target.

`ready` selectors assert initial readiness. `assert_ready` asserts a target at a particular
script time; it does not shift the timeline waiting for app state. Documents, fonts, and
images load before time zero. Delayed app startup should be represented in the script.

## Prepared assets and ranges

`capture_html` returns a `WebCapture`. Reopen it later with `WebCapture(directory)` without
Playwright. Lossless PNG frames and a manifest remain on disk. Core frame rendering loads
one frame at a time and does not retain all frames in RAM. The normal scene cache is bounded.

Cache identity includes the source tree, authored actions, selectors, viewport, initial
storage, FPS, browser version, and requested frame set. Repeated identical preparation reuses
a complete cache. Source edits make a new entry; incomplete caches are regenerated. The browser
is launched to identify its version even on cache lookup. `WebCapture` playback never launches it.
Delete `.web-cache` to reclaim disk space. Uncompressed working captures can use substantial disk.

```python
capture = capture_html(page, script, fps=30, start_time=4, end_time=8)
# Replay 0–4 to restore app state; save only frames in the requested range.
# Or prepare a sparse storyboard:
capture = capture_html(page, script, fps=30, sample_times=[2, 6, 10])
```

Always prepare at the intended export FPS. Playback chooses the containing source frame,
so exporting faster repeats frames. Range exports retain the original scene clock.
A request outside prepared frames fails with instructions to prepare that range.
`HtmlClip(source_start=4)` starts playback at capture second four; after the source ends it
holds its final frame. Its scene lifetime remains controlled by `Scene`.

For element reuse, track the selector and use `HtmlClip(capture, selector='.composer',
width=900, height=250, source_start=...)`. The visible crop follows the element and is contained
inside the fixed output box. Crops retain the page background and any occluding content;
they are not DOM-to-vector conversion or automatic transparent cutouts. Hidden or untracked
crop targets fail clearly. Layout and grouping do not need the target frame to be prepared.

## Presentation primitives

`HtmlClip` accepts `cursor=True`, `highlights=(WebHighlight(selector,start,end),)`,
`focuses=(WebFocus(selector,start,end,zoom=1.6,transition=.4),)`, and
`callouts=(WebCallout(text,start,end),)`. These are low-level visual controls; prefer kit
`WebWalkthrough` for framed presentations. Times use the capture source clock, including
when `source_start` is nonzero. Focus windows cannot overlap. Cursor and highlights are drawn
before the focus transform, so they stay aligned. Callouts stay readable in viewport space.

## Timing and support boundaries

JavaScript timers and animation-frame callbacks advance on a controlled clock. CSS/Web
Animations are paused and sought using the browser Web Animations API; finite animations
finish at their authored end. Native smooth scrolling is replaced by authored interpolation.
Subframe events use millisecond precision and animation discovery steps of at most 10 ms.

Repeatability applies to the tested Chromium/font environment, not pixels across operating
systems. Local apps relying on workers, wall-clock performance measurements, media playback,
scroll-driven animations, randomness from crypto, or external services need adaptation.
Audio/video elements and browser audio capture are outside this release.

Errors report action/selector/time or missing resource. Verify selectors and use local
fonts/assets. A browser startup error usually needs `python -m playwright install chromium`
or the OS libraries recommended by Playwright. Browser and server resources close on failure;
failed preparations are never published as completed assets.

See `training project/web-video/README.md` for the supplied 30-second tour and preview commands.
