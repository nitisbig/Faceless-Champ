"""Source-time stills and contact sheets for inspecting compositions cheaply."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from PIL import Image as PILImage
from PIL import ImageDraw

from .components import finite
from .renderer import PillowRenderer
from .timeline import Renderable
from .typography import load_font


@dataclass(frozen=True)
class StoryboardSample:
    time: float
    label: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "time", finite(self.time, "sample time", 0))
        if not isinstance(self.label, str):
            raise TypeError("Storyboard label must be a string")


def _frame_size(node: Renderable, size: tuple[int, int] | None) -> tuple[int, int]:
    size = size if size is not None else (480, max(1, round(480 / node.canvas.aspect_ratio)))
    if len(size) != 2 or any(not isinstance(v, int) or isinstance(v, bool) or v < 1 for v in size):
        raise ValueError("Frame size must contain two positive integers")
    if abs(size[0] / size[1] - node.canvas.aspect_ratio) > 2 / min(size):
        raise ValueError("Frame dimensions must preserve the canvas aspect ratio")
    return size


def _sample_time(node: Renderable, time: float) -> float:
    time = finite(time, "sample time", 0)
    if not time < node.duration:
        raise ValueError(f"Sample time must be less than composition duration ({node.duration:g})")
    return time


def save_frame(
    node: Renderable,
    time: float,
    output: str | Path,
    *,
    size: tuple[int, int] | None = None,
    renderer: PillowRenderer | None = None,
    overwrite: bool = False,
) -> Path:
    """Save one PNG at original composition time, respecting overwrite protection."""
    time, size = _sample_time(node, time), _frame_size(node, size)
    output = Path(output)
    if output.suffix.lower() != ".png":
        raise ValueError("Frame output must have a .png extension")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; pass overwrite=True")
    renderer = renderer or PillowRenderer(1)
    renderer.validate(node)
    frame = renderer.frame(node, time, size).convert("RGB")
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.save(output)
    return output


def render_storyboard(
    node: Renderable,
    samples: Iterable[StoryboardSample | float],
    directory: str | Path,
    *,
    size: tuple[int, int] | None = None,
    columns: int = 3,
    renderer: PillowRenderer | None = None,
    overwrite: bool = False,
) -> Path:
    """Save numbered source-time PNGs and storyboard.png, without rendering video.

    Samples retain caller order, including repeated times. All requested output
    paths are checked before any writing. Labels are fitted to the cell width.
    The default cell width is 480 with height matching the canvas, including portrait.
    """
    if not isinstance(columns, int) or isinstance(columns, bool) or columns < 1:
        raise ValueError("columns must be a positive integer")
    samples = tuple(s if isinstance(s, StoryboardSample) else StoryboardSample(s) for s in samples)
    if not samples:
        raise ValueError("Storyboard needs at least one sample")
    for sample in samples:
        _sample_time(node, sample.time)
    size = _frame_size(node, size)
    directory = Path(directory)
    paths = [directory / f"{i + 1:02d}-{sample.time:08.3f}s.png" for i, sample in enumerate(samples)]
    output = directory / "storyboard.png"
    if not overwrite:
        for path in (*paths, output):
            if path.exists():
                raise FileExistsError(f"Output already exists: {path}; pass overwrite=True")
    renderer = renderer or PillowRenderer(1)
    renderer.validate(node)
    columns = min(columns, len(samples))
    label_height = 34
    sheet = PILImage.new(
        "RGB", (size[0] * columns, (size[1] + label_height) * math.ceil(len(samples) / columns)), "#F4F3EE"
    )
    draw = ImageDraw.Draw(sheet)
    font = load_font(None, 14)
    directory.mkdir(parents=True, exist_ok=True)
    for i, (sample, path) in enumerate(zip(samples, paths)):
        frame = renderer.frame(node, sample.time, size).convert("RGB")
        frame.save(path)
        x, y = (i % columns) * size[0], (i // columns) * (size[1] + label_height)
        sheet.paste(frame, (x, y))
        label = f"{sample.time:.3f}s" + (f" / {sample.label}" if sample.label else "")
        while label and draw.textlength(label, font=font) > size[0] - 16:
            label = label[:-1]
        draw.text((x + 8, y + size[1] + 8), label, font=font, fill="#292724")
    sheet.save(output)
    return output
