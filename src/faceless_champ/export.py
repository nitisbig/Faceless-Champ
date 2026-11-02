"""Streaming MP4 export and composition-aware audio mixing."""

from __future__ import annotations

import hashlib
import json
import math
import multiprocessing
import multiprocessing.connection
import os
import re
import shutil
import subprocess
import tempfile
import traceback
from collections.abc import Callable
from concurrent.futures import CancelledError
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
    workers: int = 1
    chunk_frames: int = 300

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
        for name in ("workers", "chunk_frames"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
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
    chunk_dir: str | Path | None = None,
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

    ``workers > 1`` renders ``chunk_frames``-long video-only chunks in forked processes (each makes its
    own renderer from ``backend``), then joins them without re-encoding and adds the mixed audio.
    ``chunk_dir`` keeps chunks in a folder so an interrupted render resumes; chunks are matched by
    settings and frame range, not scene content, so clear the folder after editing the scene.
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
    chunked = settings.workers > 1 or chunk_dir is not None
    if settings.workers > 1:
        if settings.backend not in {"pillow", "skia"}:
            raise ValueError("workers > 1 needs backend='pillow' or 'skia' (GPU contexts cannot be forked)")
        if "fork" not in multiprocessing.get_all_start_methods():
            raise RuntimeError("workers > 1 needs the fork start method (Linux); use workers=1 here")
    if progress is not None:
        progress(0, frame_count)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="faceless-champ-", dir=output.parent) as temporary:
        temporary = Path(temporary)
        encoded = temporary / f"encoded{settings.suffix}"
        if settings.lut is not None:
            # FFmpeg runs in the temporary folder, so the LUT path never needs filtergraph escaping.
            shutil.copyfile(settings.lut, temporary / "grade.cube")
        if events:
            inputs, graph = _audio_command(events, export_duration, start_time, post=post)
            audio = CODECS[settings.codec][2] or ["-c:a", "aac", "-b:a", settings.audio_bitrate]
            audio_args = [*inputs, "-filter_complex", graph, "-map", "0:v:0", "-map", "[audio]", *audio]
        else:
            audio_args = ["-map", "0:v:0", "-an"]
        tail = ["-t", str(export_duration), "-movflags", "+faststart", str(encoded)]
        if not chunked:
            command = [*_FFMPEG, *_raw_input(size, settings.fps), *audio_args, *_video_args(settings), *tail]
            times = [start_time + index / settings.fps for index in range(frame_count)]
            _stream(renderer, node, times, size, command, temporary, settings, cancel, progress, frame_count)
        else:
            folder = Path(chunk_dir) if chunk_dir is not None else temporary / "chunks"
            folder.mkdir(parents=True, exist_ok=True)
            step = settings.chunk_frames
            if chunk_dir is None:  # nothing to resume: split short renders so every worker has work
                step = min(step, math.ceil(frame_count / settings.workers))
            chunks = _render_chunks(
                renderer, node, settings, size, start_time, frame_count, step, folder, temporary, progress, cancel
            )
            listing = temporary / "chunks.txt"
            listing.write_text("".join("file '" + str(c).replace("'", "'\\''") + "'\n" for c in chunks))
            command = [*_FFMPEG, "-f", "concat", "-safe", "0", "-i", str(listing), *audio_args, "-c:v", "copy", *tail]
            result = subprocess.run(command, capture_output=True, cwd=temporary, check=False)
            if result.returncode:
                raise RuntimeError("FFmpeg failed joining chunks: " + result.stderr.decode(errors="replace"))
        if overwrite:
            os.replace(encoded, output)
        else:
            # Atomic exclusive publication avoids overwriting a file created during rendering.
            os.link(encoded, output)
    return output


_FFMPEG = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]


def _raw_input(size, fps):
    return ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}", "-r", str(fps), "-i", "pipe:0"]


def _video_args(settings):
    """Filters and encoder arguments shared by single-pass and chunked exports (cwd holds grade.cube)."""
    video_args = CODECS[settings.codec][1]
    pix_fmt = video_args[video_args.index("-pix_fmt") + 1]
    filters = ["lut3d=file=grade.cube"] if settings.lut is not None else []
    filters += ["scale=out_color_matrix=bt709:out_range=tv", f"format={pix_fmt}"]
    args = ["-vf", ",".join(filters), *video_args, *COLOR]
    if settings.codec == "h264":
        args += ["-crf", str(settings.crf), "-preset", settings.preset]
    elif settings.codec == "hevc10":
        args += ["-crf", str(settings.crf), "-preset", settings.preset, "-x265-params", "log-level=error"]
    return args


def _stream(renderer, node, times, size, command, cwd, settings, cancel, progress=None, total=None, on_frame=None):
    """Pipe rendered frames at ``times`` into an FFmpeg ``command`` and wait for it."""
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log, cwd=cwd)
        try:
            with ProcessIO(process, timeout=settings.encoder_timeout, cancel=cancel) as pipe:
                for index, time in enumerate(times):
                    pipe.check_cancelled()
                    payload = renderer.frame(node, time, size).convert("RGB").tobytes()
                    pipe.call(lambda payload=payload: process.stdin.write(payload))
                    if progress is not None:
                        progress(index + 1, total)
                    if on_frame is not None:
                        on_frame()
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


# ---------------------------------------------------------------- chunked export


def _chunk_key(settings, size, start_time, step) -> str:
    """Identity of everything that changes chunk pixels except the scene itself."""
    lut = hashlib.sha1(Path(settings.lut).read_bytes()).hexdigest() if settings.lut is not None else ""
    fields = (size, settings.fps, settings.codec, settings.crf, settings.preset, settings.antialias, settings.backend)
    return hashlib.sha1(repr((fields, lut, round(start_time, 6), step)).encode()).hexdigest()[:10]


def _frame_count(path) -> int | None:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0"]
        + ["-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


def _encode_chunk(renderer, node, settings, size, start_time, chunk, cwd, on_frame=None, cancel=None):
    f0, f1, path = chunk
    part = path.with_name(path.stem + ".part" + path.suffix)
    command = [*_FFMPEG, *_raw_input(size, settings.fps), "-map", "0:v:0", "-an", *_video_args(settings), str(part)]
    times = [start_time + index / settings.fps for index in range(f0, f1)]
    _stream(renderer, node, times, size, command, cwd, settings, cancel, on_frame=on_frame)
    if _frame_count(part) != f1 - f0:
        raise RuntimeError(f"chunk {path.name} has the wrong frame count")
    os.replace(part, path)


def _chunk_worker(node, settings, size, start_time, todo, cwd, claimed, frames, number):
    """Forked worker: claim chunks until none are left. Errors go to ``worker-N.err``."""
    try:
        from .renderer import create_renderer

        def tick():
            with frames.get_lock():
                frames.value += 1

        with create_renderer(settings.backend, antialias=settings.antialias, gpu=settings.gpu) as renderer:
            renderer.validate(node)
            while True:
                with claimed.get_lock():
                    index = claimed.value
                    claimed.value += 1
                if index >= len(todo):
                    return
                _encode_chunk(renderer, node, settings, size, start_time, todo[index], cwd, on_frame=tick)
    except Exception:  # noqa: BLE001 -- any worker failure is reported to the parent
        (Path(cwd) / f"worker-{number}.err").write_text(traceback.format_exc())
        raise SystemExit(1) from None


def _render_chunks(renderer, node, settings, size, start_time, frame_count, step, folder, cwd, progress, cancel):
    """Render the frame grid as ``step``-frame video-only chunks in ``folder``; finished chunks are reused."""
    key = _chunk_key(settings, size, start_time, step)
    plan = []
    for f0 in range(0, frame_count, step):
        f1 = min(f0 + step, frame_count)
        plan.append((f0, f1, folder / f"chunk-{key}-{f0:07d}-{f1:07d}{settings.suffix}"))
    todo = [c for c in plan if not (c[2].is_file() and _frame_count(c[2]) == c[1] - c[0])]
    done = frame_count - sum(f1 - f0 for f0, f1, _ in todo)
    if progress is not None and done:
        progress(done, frame_count)
    if settings.workers <= 1 or len(todo) <= 1:
        count = [done]

        def tick():
            count[0] += 1
            if progress is not None:
                progress(count[0], frame_count)

        for chunk in todo:
            _encode_chunk(renderer, node, settings, size, start_time, chunk, cwd, on_frame=tick, cancel=cancel)
        return [path for _, _, path in plan]
    context = multiprocessing.get_context("fork")
    claimed, frames = context.Value("i", 0), context.Value("q", 0)
    workers = [
        context.Process(
            target=_chunk_worker,
            args=(node, settings, size, start_time, todo, cwd, claimed, frames, number),
            daemon=True,
        )
        for number in range(min(settings.workers, len(todo)))
    ]
    reported = done
    try:
        for worker in workers:
            worker.start()
        while True:
            multiprocessing.connection.wait([w.sentinel for w in workers], timeout=0.25)
            failed = [w for w in workers if w.exitcode not in (None, 0)]
            if failed:
                errors = sorted(Path(cwd).glob("worker-*.err"))
                detail = errors[0].read_text() if errors else f"exit code {failed[0].exitcode}"
                raise RuntimeError("A render worker failed:\n" + detail)
            if cancel is not None and cancel():
                raise CancelledError("Video export cancelled")
            current = done + frames.value
            if progress is not None and current != reported:
                reported = current
                progress(current, frame_count)
            if all(w.exitcode == 0 for w in workers):
                break
    finally:
        for worker in workers:
            if worker.is_alive():
                worker.terminate()
            worker.join()
    if progress is not None and reported != frame_count:
        progress(frame_count, frame_count)
    return [path for _, _, path in plan]
