"""Streaming MP4 export and composition-aware audio mixing."""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ._rendering.process import ProcessIO
from .audio import require_tools
from .components import Canvas, finite
from .gpu import GPUOptions
from .renderer import PillowRenderer, Renderer, managed_renderer
from .timeline import Grid, Layer, Renderable, Scene, Sequence

#: codec -> (output suffix, encoder arguments, audio arguments or None for AAC at audio_bitrate)
CODECS = {
    "h264": (".mp4", ["-c:v", "libx264", "-pix_fmt", "yuv420p"], None),
    "hevc10": (".mp4", ["-c:v", "libx265", "-pix_fmt", "yuv420p10le", "-tag:v", "hvc1"], None),
    "prores": (
        ".mov",
        ["-c:v", "prores_ks", "-profile:v", "3", "-vendor", "apl0", "-pix_fmt", "yuv422p10le"],
        ["-c:a", "pcm_s16le"],
    ),
}
# SDR web video is BT.709: convert with its matrix and tag the stream so players do not guess.
COLOR = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]
LOUDNESS_RANGE = 11.0


@dataclass(frozen=True)
class ExportSettings:
    quality: str = "qh"
    width: int | None = None
    height: int | None = None
    fps: float = 30
    crf: int = 18
    preset: str = "medium"
    antialias: int = 2
    backend: str = "pillow"
    gpu: GPUOptions | None = None
    encoder_timeout: float = 60
    codec: str = "h264"
    lut: str | Path | None = None
    loudness: float | None = None
    true_peak: float = -1.0
    audio_bitrate: str = "192k"

    @property
    def suffix(self) -> str:
        return CODECS[self.codec][0] if self.codec in CODECS else ".mp4"

    def dimensions(self, canvas: Canvas) -> tuple[int, int]:
        if self.backend not in {"pillow", "skia", "moderngl", "auto"}:
            raise ValueError("backend must be pillow, skia, moderngl or auto")
        if self.gpu is not None and not isinstance(self.gpu, GPUOptions):
            raise TypeError("gpu must be GPUOptions or None")
        presets = {"ql": 720, "720p": 720, "qh": 1080, "1080p": 1080, "qk": 2160, "4k": 2160}
        if self.antialias not in (1, 2, 3, 4):
            raise ValueError("antialias must be 1, 2, 3, or 4")
        if self.quality not in presets:
            raise ValueError("quality must be ql/720p, qh/1080p, or qk/4k")
        finite(self.fps, "fps", 0.001)
        finite(self.encoder_timeout, "encoder_timeout", 0.001)
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
        if self.codec not in CODECS:
            raise ValueError(f"codec must be one of: {', '.join(CODECS)}")
        if self.lut is not None:
            lut = Path(self.lut)
            if lut.suffix.lower() != ".cube":
                raise ValueError("lut must be a .cube 3D LUT file")
            if not lut.is_file():
                raise FileNotFoundError(f"LUT not found: {lut}")
        if self.loudness is not None:
            finite(self.loudness, "loudness", -70)
            if self.loudness > -5:
                raise ValueError("loudness is an integrated LUFS target between -70 and -5 (YouTube: -14)")
        finite(self.true_peak, "true_peak", -9)
        if self.true_peak > 0:
            raise ValueError("true_peak is a dBTP ceiling between -9 and 0")
        if not isinstance(self.audio_bitrate, str) or not self.audio_bitrate.rstrip("k").isdigit():
            raise ValueError("audio_bitrate must look like '192k'")
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


def _audio_command(events, duration, start_time=0.0, *, first_input=1, post=()):
    """FFmpeg inputs and a filter graph mixing ``events`` into ``[audio]``.

    ``first_input`` is the input index of the first clip (0 when there is no video input);
    ``post`` filters run on the finished mix (loudness normalization).
    """
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
        filters.append(f"[{i + first_input}:a:0]" + ",".join(chain) + f"[{label}]")
        labels.append(f"[{label}]")
    filters.append(
        "".join(labels)
        + f"amix=inputs={len(labels)}:normalize=0:duration=longest,apad,"
        + ",".join([f"atrim=start={start_time}:end={start_time + duration}", "asetpts=PTS-STARTPTS", *post])
        + "[audio]"
    )
    return inputs, ";".join(filters)


def _loudnorm(settings, measured=None):
    target = f"loudnorm=I={settings.loudness}:TP={settings.true_peak}:LRA={LOUDNESS_RANGE}"
    if measured is None:
        return target + ":print_format=json"
    keys = ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")
    names = ("measured_I", "measured_TP", "measured_LRA", "measured_thresh", "offset")
    values = ":".join(f"{name}={measured[key]}" for name, key in zip(names, keys))
    # loudnorm resamples to 192 kHz internally; return to the mix rate.
    return f"{target}:{values}:linear=true,aresample=48000"


def measure_loudness(events, duration, start_time, settings) -> dict | None:
    """First loudnorm pass over the mixed audio. None when the mix is silent (nothing to normalize)."""
    inputs, graph = _audio_command(events, duration, start_time, first_input=0, post=(_loudnorm(settings),))
    command = ["ffmpeg", "-hide_banner", "-nostats", *inputs, "-filter_complex", graph, "-map", "[audio]", "-f", "null"]
    result = subprocess.run([*command, "-"], capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError("FFmpeg loudness analysis failed: " + result.stderr[-2000:])
    found = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", result.stderr)
    if not found:
        raise RuntimeError("FFmpeg loudness analysis printed no measurement")
    measured = json.loads(found[-1])
    if not all(math.isfinite(float(measured[k])) for k in ("input_i", "input_tp", "input_lra", "input_thresh")):
        return None
    return measured


@managed_renderer(2)
def render(
    node: Renderable,
    output: str | Path,
    *,
    settings: ExportSettings | None = None,
    renderer: Renderer | None = None,
    overwrite: bool = False,
    progress: Callable[[int, int], None] | None = None,
    start_time: float = 0.0,
    end_time: float | None = None,
    cancel: Callable[[], bool] | None = None,
    **options,
) -> Path:
    """Render to MP4 (or MOV for ``codec="prores"``). ``progress(completed_frames, total_frames)`` is optional.

    Video is converted with the BT.709 matrix and tagged BT.709 limited range. ``lut`` applies a
    .cube grade in RGB first; ``loudness`` normalizes the mixed audio to an integrated LUFS target
    in two passes (the analysis pass runs before any frame is rendered).

    Pass an ExportSettings object or its fields as keywords. Progress starts at
    zero and runs after each streamed frame; publication follows encoder completion.
    A source-clock range trims both visuals and mixed audio without moving events.
    ``cancel()`` raises concurrent.futures.CancelledError when true. Pipe writes
    and encoder completion are bounded by ``encoder_timeout`` (seconds per
    operation). Cancellation is checked between frames and while waiting on I/O.
    """
    if settings is not None and options:
        raise ValueError("Use settings or keyword export options, not both")
    if progress is not None and not callable(progress):
        raise TypeError("progress must be callable")
    if cancel is not None and not callable(cancel):
        raise TypeError("cancel must be callable")
    if not isinstance(node, Renderable):
        raise TypeError("Expected a Scene, Sequence, Grid, or Layer")
    settings = settings or ExportSettings(**options)
    output = Path(output).resolve()
    if output.suffix.lower() != settings.suffix:
        raise ValueError(f"Output must have an {settings.suffix} extension for codec={settings.codec!r}")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; pass overwrite=True")
    require_tools()
    size = settings.dimensions(node.canvas)
    renderer = renderer or PillowRenderer(settings.antialias)
    source_duration = finite(node.duration, "duration", 0.000001)
    start_time = finite(start_time, "start_time", 0)
    end_time = source_duration if end_time is None else finite(end_time, "end_time", 0)
    if not start_time < end_time <= source_duration:
        raise ValueError("Render range must satisfy 0 <= start_time < end_time <= duration")
    renderer.validate(node)
    duration = end_time - start_time
    frame_count = math.ceil(duration * settings.fps - 1e-9)
    export_duration = frame_count / settings.fps
    events = _audio_events(node)
    post = ()
    if events and settings.loudness is not None:
        measured = measure_loudness(events, export_duration, start_time, settings)
        if measured is not None:
            post = (_loudnorm(settings, measured),)
    _, video_args, audio_args = CODECS[settings.codec]
    pix_fmt = video_args[video_args.index("-pix_fmt") + 1]
    if progress is not None:
        progress(0, frame_count)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="faceless-champ-", dir=output.parent) as temporary:
        temporary = Path(temporary)
        encoded = temporary / f"encoded{settings.suffix}"
        video_filters = []
        if settings.lut is not None:
            # FFmpeg runs in the temporary folder, so the LUT path never needs filtergraph escaping.
            shutil.copyfile(settings.lut, temporary / "grade.cube")
            video_filters.append("lut3d=file=grade.cube")
        video_filters += ["scale=out_color_matrix=bt709:out_range=tv", f"format={pix_fmt}"]
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
            inputs, graph = _audio_command(events, export_duration, start_time, post=post)
            audio = audio_args or ["-c:a", "aac", "-b:a", settings.audio_bitrate]
            command.extend(inputs + ["-filter_complex", graph, "-map", "0:v:0", "-map", "[audio]", *audio])
        else:
            command.extend(["-map", "0:v:0", "-an"])
        command.extend(["-vf", ",".join(video_filters), *video_args, *COLOR])
        if settings.codec == "h264":
            command.extend(["-crf", str(settings.crf), "-preset", settings.preset])
        elif settings.codec == "hevc10":
            command.extend(["-crf", str(settings.crf), "-preset", settings.preset, "-x265-params", "log-level=error"])
        command.extend(["-t", str(export_duration), "-movflags", "+faststart", str(encoded)])
        with (temporary / "ffmpeg.log").open("w+b") as log:
            process = subprocess.Popen(
                command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log, cwd=temporary
            )
            try:
                with ProcessIO(process, timeout=settings.encoder_timeout, cancel=cancel) as pipe:
                    for index in range(frame_count):
                        pipe.check_cancelled()
                        frame = renderer.frame(node, start_time + index / settings.fps, size).convert("RGB")
                        payload = frame.tobytes()
                        pipe.call(lambda payload=payload: process.stdin.write(payload))
                        if progress is not None:
                            progress(index + 1, frame_count)
                    pipe.call(process.stdin.close)
                    returncode = pipe.call(process.wait)
                if returncode:
                    log.seek(0)
                    raise RuntimeError("FFmpeg failed: " + log.read().decode(errors="replace"))
            except BaseException as exc:
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
