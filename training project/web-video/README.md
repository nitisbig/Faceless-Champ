# HTML-to-video example

A 30-second silent, landscape tour of the supplied interactive HTML, using public core
capture APIs and kit presentation blocks. The HTML is preserved unchanged. It provides
simulated local replies, not a connection to ChatGPT.

Install from the repository root:

```bash
uv pip install -e '.[web]' -e './facelesschamp-kit[web]'
.venv/bin/python -m playwright install chromium
```

Run from the repository root:

```bash
# Sparse storyboard: replays interactions, saves seven sampled frames, no video.
.venv/bin/python 'training project/web-video/render.py' --mode storyboard
# Short preview only.
.venv/bin/python 'training project/web-video/render.py' --mode preview --start 4 --end 9 --resolution 540p
# One frame.
.venv/bin/python 'training project/web-video/render.py' --mode frame --time 21
# Prepare all browser frames without encoding.
.venv/bin/python 'training project/web-video/render.py' --mode prepare
# Full export, when you choose to render it.
.venv/bin/python 'training project/web-video/render.py' --mode render
```

Defaults: 1920×1080 at 30 FPS. `--resolution` also accepts `540p`, `720p`, `4k`;
`--fps`, `--output`, and `--overwrite` are supported. Storyboard output is a directory.
The HTML viewport is 1440×900; higher video resolutions upscale that capture.
For sharper close-ups or 4K, increase the viewport in `browser_script()` and recheck layout.

Outputs go under `output/`; browser frames go under `.web-cache/`. Both are ignored by Git.
A cache is keyed by requested frames, browser version, and source/settings. It can be
removed and rebuilt. Preparation of previews replays earlier actions without saving their
frames. Rendering is deterministic against prepared frames and can seek backward.

`main.py` defines the interactions and scene composition. The tour introduces the composer,
types and sends a coding question, examines the code response, switches appearance, reuses
the composer as a separate card, and returns to the page. Change selectors and interactions
to adapt it to a different local application.
