"""Local audio clips, FFmpeg probing, and the measurements the mix needs (speech spans, SFX marks)."""

import array
import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from .components import finite

ROLES = ("mix", "voice", "music", "sfx")


def require_tools() -> None:
    for name in ("ffmpeg", "ffprobe"):
        if not shutil.which(name):
            raise RuntimeError(f"{name} is required; install FFmpeg and add it to PATH")


def probe(path: Path) -> dict:
    require_tools()
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise ValueError(f"Cannot probe {path}: {result.stderr.strip()}")
    return json.loads(result.stdout)


@dataclass
class AudioClip:
    path: Path
    start: float = 0
    trim_start: float = 0
    trim_end: float | None = None
    volume: float = 1
    fade_in: float = 0
    fade_out: float = 0
    role: str = "mix"  # "voice" clips key the ducking of clips with duck < 0
    duck: float = 0  # dB applied while any voice clip is speaking (e.g. -12 for a music bed)
    rate: float = 1  # playback rate; changes pitch and length together
    duration: float = field(init=False)

    def __post_init__(self):
        self.path = Path(self.path)
        if not self.path.is_file():
            raise FileNotFoundError(f"Audio file not found: {self.path}")
        if self.path.suffix.lower() not in {".wav", ".mp3", ".m4a", ".flac", ".ogg"}:
            raise ValueError("Audio must be WAV, MP3, M4A, FLAC or OGG")
        for name in ("start", "trim_start", "volume", "fade_in", "fade_out"):
            setattr(self, name, finite(getattr(self, name), name, 0))
        if self.role not in ROLES:
            raise ValueError(f"Audio role must be one of {', '.join(ROLES)}")
        self.duck = finite(self.duck, "duck", -60)
        if self.duck > 0:
            raise ValueError("duck is a reduction in dB and must be <= 0")
        self.rate = finite(self.rate, "rate", 0.25)
        if self.rate > 4:
            raise ValueError("rate must be between 0.25 and 4")
        info = probe(self.path)
        if not any(s["codec_type"] == "audio" for s in info["streams"]):
            raise ValueError(f"No audio stream in {self.path}")
        source_duration = float(info["format"]["duration"])
        end = source_duration if self.trim_end is None else finite(self.trim_end, "trim_end", 0)
        if not self.trim_start < end <= source_duration + 0.001:
            raise ValueError("Audio trim must satisfy 0 <= trim_start < trim_end <= source duration")
        self.trim_end = end
        self.duration = (end - self.trim_start) / self.rate
        if max(self.fade_in, self.fade_out) > self.duration:
            raise ValueError("Audio fades cannot exceed clip duration")


def _identity(path: Path) -> tuple[str, int, int]:
    stat = path.stat()
    return str(path.resolve()), stat.st_mtime_ns, stat.st_size


def speech_spans(clip: AudioClip, *, threshold: float = -40.0, gap: float = 0.3) -> tuple[tuple[float, float], ...]:
    """Spans of ``clip`` that are not silent, in seconds from the clip's start on the timeline.

    Pauses shorter than ``gap`` seconds count as speech. Measured once per file and trim.
    """
    spans = _speech_spans(_identity(clip.path), clip.trim_start, clip.trim_end, threshold, gap)
    return tuple((a / clip.rate, b / clip.rate) for a, b in spans)


@lru_cache(maxsize=256)
def _speech_spans(identity, trim_start, trim_end, threshold, gap):
    require_tools()
    length = trim_end - trim_start
    command = ["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{trim_start}", "-t", f"{length}", "-i", identity[0]]
    command += ["-af", f"silencedetect=n={threshold}dB:d={gap}", "-f", "null", "-"]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(f"Cannot analyse {identity[0]}: {result.stderr[-500:]}")
    starts = [float(v) for v in re.findall(r"silence_start: (-?[\d.]+)", result.stderr)]
    ends = [float(v) for v in re.findall(r"silence_end: (-?[\d.]+)", result.stderr)]
    spans, cursor = [], 0.0
    for i, start in enumerate(starts):
        start = max(0.0, start)
        if start > cursor:
            spans.append((cursor, min(start, length)))
        cursor = ends[i] if i < len(ends) else length
    if cursor < length:
        spans.append((cursor, length))
    return tuple(spans)


@lru_cache(maxsize=256)
def _marks(identity) -> tuple[float, float, float]:
    """(onset, peak, length) in seconds: first sample above -40 dB of the peak, loudest 10 ms, file length."""
    require_tools()
    data = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", identity[0], "-f", "s16le", "-ac", "1", "-ar", "48000", "pipe:1"],
        capture_output=True,
        check=False,
    )
    if data.returncode:
        raise RuntimeError(f"Cannot decode {identity[0]}: {data.stderr.decode(errors='replace')[-500:]}")
    samples = array.array("h")
    samples.frombytes(data.stdout[: len(data.stdout) // 2 * 2])
    if not any(samples):
        raise ValueError(f"Sound effect is silent: {identity[0]}")
    hop = 240  # 5 ms blocks; the loudest pair of blocks is the peak
    energy = [sum(v * v for v in samples[i : i + hop]) for i in range(0, len(samples), hop)]
    energy.append(0)
    loudest = max(range(len(energy) - 1), key=lambda i: energy[i] + energy[i + 1])
    floor = max(abs(v) for v in samples) / 100  # -40 dB
    onset = next(i for i, v in enumerate(samples) if abs(v) >= floor)
    onset = max(0, onset - 96)  # keep 2 ms of attack
    return onset / 48000, max(onset, (loudest + 1) * hop) / 48000, len(samples) / 48000


def sound_marks(path: str | Path) -> tuple[float, float]:
    """(onset, peak) of a short sound effect, in seconds from the file start.

    ``Scene.add_sfx`` uses these to land a hit's first transient or its loudest moment on a beat.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")
    onset, peak, _ = _marks(_identity(path))
    return onset, peak
