"""Render the 30 s forest tunnel preview: 1280x720, 30 fps, GPU (moderngl), one process."""

from pathlib import Path

from faceless_champ.export import ExportSettings, render
from faceless_champ.progress import ExportProgress
from scene import build

out = Path(__file__).with_name("output") / "forest_tunnel_720p.mp4"
out.parent.mkdir(exist_ok=True)
settings = ExportSettings(width=1280, height=720, fps=30, antialias=1, workers=1, preset="medium")
with ExportProgress() as progress:
    render(build(), out, settings=settings, overwrite=True, progress=progress)
print(out)
