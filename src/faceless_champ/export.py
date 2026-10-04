"""Streaming MP4 export and composition-aware audio mixing."""

from __future__ import annotations

import math
import os
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .audio import require_tools
from .components import Canvas, finite
from .renderer import PillowRenderer, Renderer
from .timeline import Grid, Layer, Renderable, Scene, Sequence


@dataclass(frozen=True)
class ExportSettings:
    quality: str = "qh"
    width: int | None = None
    height: int | None = None
    fps: float = 30
    crf: int = 18
    preset: str = "medium"
    antialias: int = 2

    def dimensions(self, canvas: Canvas) -> tuple[int, int]:
        presets = {"ql": 720, "720p": 720, "qh": 1080, "1080p": 1080, "qk": 2160, "4k": 2160}
        if self.antialias not in (1, 2, 3, 4):
            raise ValueError("antialias must be 1, 2, 3, or 4")
        if self.quality not in presets:
            raise ValueError("quality must be ql/720p, qh/1080p, or qk/4k")
        finite(self.fps, "fps", 0.001)
        if not isinstance(self.crf, int) or not 0 <= self.crf <= 51:
            raise ValueError("crf must be an integer between 0 and 51")
        if self.preset not in {
            "ultrafast",
            "superfast",
            "veryfast",
            "faster",
            "fast",
            "medium",
            "slow",
            "slower",
            "veryslow",
        }:
            raise ValueError("Invalid H.264 encoder preset")
        if (self.width is None) != (self.height is None):
            raise ValueError("Specify both width and height")
        if self.width is not None:
            size = (self.width, self.height)
        else:
            short = presets[self.quality]
            ratio = short / min(canvas.width, canvas.height)
            size = tuple(max(2, round(v * ratio / 2) * 2) for v in (canvas.width, canvas.height))
        if any(not isinstance(v, int) or isinstance(v, bool) or v <= 0 or v % 2 for v in size):
            raise ValueError("Export dimensions must be positive even integers")
        if abs(size[0] / size[1] - canvas.aspect_ratio) > 2 / min(size):
            raise ValueError("Export dimensions must preserve the canvas aspect ratio")
        return size


def _audio_events(node, offset=0.0, envelopes=()):
    if isinstance(node, Scene):
        node.build()
        return [(clip, offset + clip.start, envelopes) for clip in node.audio]
    result = []
    if isinstance(node, Sequence):
        starts = node.starts
        for i, (start, child) in enumerate(zip(starts, node.children)):
            fades = list(envelopes)
            if node.crossfade:
                if i:
                    fades.append(("in", offset + start, node.crossfade))
                if i < len(node.children) - 1:
                    fades.append(("out", offset + start + child.duration - node.crossfade, node.crossfade))
            result.extend(_audio_events(child, offset + start, tuple(fades)))
    elif isinstance(node, Grid):
        for start, child in zip(node.start_times, node.children):
            result.extend(_audio_events(child, offset + start, envelopes))
    elif isinstance(node, Layer):
        for child in node.children:
            result.extend(_audio_events(child, offset, envelopes))
    return result


def _audio_command(events, duration):
    inputs, filters, labels = [], [], []
    for i, (clip, start, envelopes) in enumerate(events):
        inputs.extend(["-i", str(clip.path.resolve())])
        chain = [
            f"atrim=start={clip.trim_start}:end={clip.trim_end}",
            "asetpts=PTS-STARTPTS",
            "aresample=48000",
            "aformat=channel_layouts=stereo",
            f"volume={clip.volume}",
        ]
        if clip.fade_in:
            chain.append(f"afade=t=in:st=0:d={clip.fade_in}")
        if clip.fade_out:
            chain.append(f"afade=t=out:st={clip.duration - clip.fade_out}:d={clip.fade_out}")
        # FFmpeg 6.1 may emit unset timestamps for inserted silence. Rebase by sample count.
        chain.extend([f"adelay={round(start * 48000)}S:all=1", "asetpts=N/SR/TB"])
        for direction, at, length in envelopes:
            chain.append(f"afade=t={direction}:st={at}:d={length}")
        label = f"a{i}"
        filters.append(f"[{i + 1}:a:0]" + ",".join(chain) + f"[{label}]")
        labels.append(f"[{label}]")
    filters.append(
        "".join(labels)
        + f"amix=inputs={len(labels)}:normalize=0:duration=longest,apad,atrim=duration={duration}[audio]"
    )
    return inputs, ";".join(filters)


def render(
    node: Renderable,
    output: str | Path,
    *,
    settings: ExportSettings | None = None,
    renderer: Renderer | None = None,
    overwrite: bool = False,
    progress: Callable[[int, int], None] | None = None,
    **options,
) -> Path:
    """Render to MP4. ``progress(completed_frames, total_frames)`` is optional.

    Pass an ExportSettings object or its fields as keywords. Progress starts at
    zero and runs after each streamed frame; publication follows encoder completion.
    """
    if settings is not None and options:
        raise ValueError("Use settings or keyword export options, not both")
    if progress is not None and not callable(progress):
        raise TypeError("progress must be callable")
    if not isinstance(node, Renderable):
        raise TypeError("Expected a Scene, Sequence, Grid, or Layer")
    settings = settings or ExportSettings(**options)
    output = Path(output).resolve()
    if output.suffix.lower() != ".mp4":
        raise ValueError("Output must have an .mp4 extension")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; pass overwrite=True")
    require_tools()
    size = settings.dimensions(node.canvas)
    renderer = renderer or PillowRenderer(settings.antialias)
    renderer.validate(node)
    duration = finite(node.duration, "duration", 0.000001)
    frame_count = math.ceil(duration * settings.fps - 1e-9)
    export_duration = frame_count / settings.fps
    events = _audio_events(node)
    if progress is not None:
        progress(0, frame_count)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="faceless-champ-", dir=output.parent) as temporary:
        temporary = Path(temporary)
        encoded = temporary / "encoded.mp4"
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{size[0]}x{size[1]}",
            "-r",
            str(settings.fps),
            "-i",
            "pipe:0",
        ]
        if events:
            inputs, graph = _audio_command(events, export_duration)
            command.extend(
                inputs + ["-filter_complex", graph, "-map", "0:v:0", "-map", "[audio]", "-c:a", "aac", "-b:a", "192k"]
            )
        else:
            command.extend(["-map", "0:v:0", "-an"])
        command.extend(
            [
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                str(settings.crf),
                "-preset",
                settings.preset,
                "-t",
                str(export_duration),
                "-movflags",
                "+faststart",
                str(encoded),
            ]
        )
        with (temporary / "ffmpeg.log").open("w+b") as log:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log)
            try:
                for index in range(frame_count):
                    frame = renderer.frame(node, index / settings.fps, size).convert("RGB")
                    process.stdin.write(frame.tobytes())
                    if progress is not None:
                        progress(index + 1, frame_count)
                process.stdin.close()
                returncode = process.wait()
                if returncode:
                    log.seek(0)
                    raise RuntimeError("FFmpeg failed: " + log.read().decode(errors="replace"))
            except BaseException as exc:
                if process.poll() is None:
                    process.terminate()
                process.wait()
                if process.stdin and not process.stdin.closed:
                    process.stdin.close()
                if isinstance(exc, BrokenPipeError):
                    log.seek(0)
                    raise RuntimeError("FFmpeg failed: " + log.read().decode(errors="replace")) from exc  # noqa: TRY004
                raise
        if overwrite:
            os.replace(encoded, output)
        else:
            # Atomic exclusive publication avoids overwriting a file created during rendering.
            os.link(encoded, output)
    return output
