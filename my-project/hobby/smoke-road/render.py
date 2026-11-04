"""Render the 20 s smoke road preview: 1280x720, 30 fps, antialias 1, two forked workers."""

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")

from pathlib import Path  # noqa: E402

from faceless_champ.export import ExportSettings, render  # noqa: E402
from faceless_champ.progress import ExportProgress  # noqa: E402
from scene import build  # noqa: E402

out = Path(__file__).with_name("output") / "smoke_road_720p.mp4"
out.parent.mkdir(exist_ok=True)
settings = ExportSettings(width=1280, height=720, fps=30, antialias=1, workers=2, preset="medium")
with ExportProgress() as progress:
    render(build(), out, settings=settings, overwrite=True, progress=progress)
print(out)
