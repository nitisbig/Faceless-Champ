"""Local audio clips and FFmpeg probing."""

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .components import finite


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
    duration: float = field(init=False)

    def __post_init__(self):
        self.path = Path(self.path)
        if not self.path.is_file():
            raise FileNotFoundError(f"Audio file not found: {self.path}")
        if self.path.suffix.lower() not in {".wav", ".mp3", ".m4a"}:
            raise ValueError("Audio must be WAV, MP3, or M4A")
        for name in ("start", "trim_start", "volume", "fade_in", "fade_out"):
            setattr(self, name, finite(getattr(self, name), name, 0))
        info = probe(self.path)
        if not any(s["codec_type"] == "audio" for s in info["streams"]):
            raise ValueError(f"No audio stream in {self.path}")
        source_duration = float(info["format"]["duration"])
        end = source_duration if self.trim_end is None else finite(self.trim_end, "trim_end", 0)
        if not self.trim_start < end <= source_duration + 0.001:
            raise ValueError("Audio trim must satisfy 0 <= trim_start < trim_end <= source duration")
        self.trim_end = end
        self.duration = end - self.trim_start
        if max(self.fade_in, self.fade_out) > self.duration:
            raise ValueError("Audio fades cannot exceed clip duration")
