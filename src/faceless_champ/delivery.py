"""Pre-upload checks on a finished video: loudness, true peak, color tags, black, frozen and silent spans.

    report = delivery_report("output/full_1080p.mp4")
    print(report)            # one line per finding
    report.ok                # False only for errors (clipping, missing video)

One FFmpeg decode pass measures EBU R128 loudness and runs blackdetect, freezedetect and
silencedetect; ffprobe supplies the stream facts. Freezes and silences are notes, not failures:
explainers hold still frames and end screens are often silent.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .audio import probe, require_tools
from .components import finite

STANDARD_FPS = (23.976, 24, 25, 29.97, 30, 50, 59.94, 60)


@dataclass(frozen=True)
class DeliveryFinding:
    severity: str  # "error", "warning" or "info"
    code: str
    message: str
    start: float | None = None
    end: float | None = None

    def __str__(self) -> str:
        span = f" [{self.start:.2f}s-{self.end:.2f}s]" if self.start is not None and self.end is not None else ""
        return f"{self.severity.upper():7} {self.code}: {self.message}{span}"


@dataclass(frozen=True)
class DeliveryReport:
    path: Path
    width: int
    height: int
    fps: float
    duration: float
    video_codec: str
    pix_fmt: str
    color_space: str | None
    audio_codec: str | None = None
    sample_rate: int | None = None
    loudness: float | None = None  # integrated, LUFS
    loudness_range: float | None = None  # LU
    true_peak: float | None = None  # dBTP
    findings: tuple[DeliveryFinding, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return not any(f.severity == "error" for f in self.findings)

    def __str__(self) -> str:
        audio = (
            f"{self.audio_codec} {self.sample_rate} Hz, {self.loudness:.1f} LUFS, "
            f"LRA {self.loudness_range:.1f} LU, peak {self.true_peak:.1f} dBTP"
            if self.audio_codec and self.loudness is not None
            else self.audio_codec or "no audio"
        )
        lines = [
            f"{self.path.name}: {self.width}x{self.height} {self.fps:g} fps {self.duration:.2f}s",
            f"  video {self.video_codec} {self.pix_fmt} color={self.color_space or 'untagged'}",
            f"  audio {audio}",
        ]
        lines += [f"  {finding}" for finding in self.findings] or ["  no findings"]
        return "\n".join(lines)


def _rate(text: str) -> float:
    num, _, den = text.partition("/")
    return float(num) / float(den or 1) if float(den or 1) else 0.0


def _spans(log: str, start_pattern: str, end_pattern: str, duration: float):
    starts = [float(v) for v in re.findall(start_pattern, log)]
    ends = [float(v) for v in re.findall(end_pattern, log)]
    # A span still open at the end of the file has no end line.
    return [(s, ends[i] if i < len(ends) else duration) for i, s in enumerate(starts)]


def _last(pattern: str, text: str) -> float | None:
    found = re.findall(pattern, text)
    return float(found[-1]) if found else None


def delivery_report(
    path: str | Path,
    *,
    loudness: float = -14.0,
    true_peak: float = -1.0,
    tolerance: float = 1.0,
    black: float = 1.0,
    freeze: float = 3.0,
    silence: float = 3.0,
) -> DeliveryReport:
    """Measure ``path`` against a delivery target (defaults: YouTube, -14 LUFS, -1 dBTP).

    black/freeze/silence: minimum span lengths in seconds to report.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Video not found: {path}")
    for name, value in (("tolerance", tolerance), ("black", black), ("freeze", freeze), ("silence", silence)):
        finite(value, name, 0.001)
    require_tools()
    info = probe(path)
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    if video is None:
        raise ValueError(f"No video stream in {path}")
    duration = float(info["format"].get("duration") or video.get("duration") or 0.0)
    fps = _rate(video.get("avg_frame_rate") or video.get("r_frame_rate") or "0/1")
    graph = f"[0:v:0]blackdetect=d={black}:pic_th=0.999:pix_th=0.02,freezedetect=n=-60dB:d={freeze}[v]"
    maps = ["-map", "[v]"]
    if audio is not None:
        graph += f";[0:a:0]ebur128=peak=true,silencedetect=n=-50dB:d={silence}[a]"
        maps += ["-map", "[a]"]
    command = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-filter_complex", graph, *maps, "-f", "null"]
    result = subprocess.run([*command, "-"], capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError("FFmpeg analysis failed: " + result.stderr[-2000:])
    log = result.stderr
    summary = log.rsplit("Summary:", 1)[-1] if "Summary:" in log else ""

    findings = []
    color = video.get("color_space")
    if color in (None, "unknown"):
        findings.append(DeliveryFinding("warning", "COLOR_TAGS", "video is untagged; players will guess its colors"))
    elif color != "bt709":
        findings.append(DeliveryFinding("warning", "COLOR_TAGS", f"color space {color}, expected bt709 for SDR web"))
    if not any(abs(fps - s) < 0.01 for s in STANDARD_FPS):
        findings.append(DeliveryFinding("info", "FPS", f"{fps:g} fps is not a standard rate"))
    if abs(int(video["width"]) / int(video["height"]) - 16 / 9) > 0.01:
        findings.append(DeliveryFinding("info", "ASPECT", f"{video['width']}x{video['height']} is not 16:9"))

    measured_i = measured_lra = measured_tp = None
    if audio is None:
        findings.append(DeliveryFinding("warning", "NO_AUDIO", "the file has no audio stream"))
    else:
        measured_i = _last(r"I:\s+(-?[\d.]+|-inf) LUFS", summary)
        measured_lra = _last(r"LRA:\s+(-?[\d.]+) LU", summary)
        measured_tp = _last(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summary)
        if int(audio.get("sample_rate", 0)) != 48000:
            findings.append(DeliveryFinding("info", "SAMPLE_RATE", f"{audio.get('sample_rate')} Hz; 48000 is standard"))
        if measured_i is not None and abs(measured_i - loudness) > tolerance:
            findings.append(
                DeliveryFinding(
                    "warning", "LOUDNESS", f"{measured_i:.1f} LUFS, target {loudness:g} ± {tolerance:g} (loudness=)"
                )
            )
        if measured_tp is not None and measured_tp > 0:
            findings.append(DeliveryFinding("error", "CLIPPING", f"true peak {measured_tp:.1f} dBTP is above 0"))
        elif measured_tp is not None and measured_tp > true_peak + 0.1:
            findings.append(DeliveryFinding("warning", "TRUE_PEAK", f"{measured_tp:.1f} dBTP, ceiling {true_peak:g}"))
        for start, end in _spans(log, r"silence_start: (-?[\d.]+)", r"silence_end: (-?[\d.]+)", duration):
            findings.append(DeliveryFinding("info", "SILENCE", f"{end - start:.1f}s of silence", start, end))
    for start, end in _spans(log, r"black_start:(-?[\d.]+)", r"black_end:(-?[\d.]+)", duration):
        findings.append(DeliveryFinding("warning", "BLACK", f"{end - start:.1f}s of black frames", start, end))
    for start, end in _spans(
        log, r"lavfi\.freezedetect\.freeze_start: (-?[\d.]+)", r"lavfi\.freezedetect\.freeze_end: (-?[\d.]+)", duration
    ):
        findings.append(DeliveryFinding("info", "FREEZE", f"{end - start:.1f}s without visual change", start, end))
    return DeliveryReport(
        path=path,
        width=int(video["width"]),
        height=int(video["height"]),
        fps=fps,
        duration=duration,
        video_codec=video.get("codec_name", "?"),
        pix_fmt=video.get("pix_fmt", "?"),
        color_space=color if color not in (None, "unknown") else None,
        audio_codec=audio.get("codec_name") if audio else None,
        sample_rate=int(audio["sample_rate"]) if audio and audio.get("sample_rate") else None,
        loudness=measured_i,
        loudness_range=measured_lra,
        true_peak=measured_tp,
        findings=tuple(findings),
    )
