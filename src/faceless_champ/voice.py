"""Narration finishing: a pedalboard voice chain baked to a cached WAV, and pyloudnorm metering.

    from faceless_champ.voice import VoiceChain, loudness, process_voice

    clean = process_voice("audio.mp3")                          # narration preset, -16 LUFS
    clean = process_voice("audio.mp3", VoiceChain.named("broadcast"))
    scene.add_audio(clean, start=0, role="voice")
    loudness(clean)                                             # integrated LUFS (BS.1770)

The chain runs a 24 dB/octave high-pass, level match, optional gate, mud/presence/air EQ,
compressor, split-band de-esser, loudness normalization and a look-ahead peak limiter. Output is
48 kHz 24-bit WAV, written once per (file, chain) to the cache (``FC_CACHE_DIR`` or
``~/.cache/faceless_champ/voice``), so scenes can call ``process_voice`` on every run.
Needs ``faceless-champ[audio]``.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from .components import finite

__all__ = ["PRESETS", "VoiceChain", "cache_root", "loudness", "process_voice"]

RATE = 48000
LEVEL = -24.0  # LUFS the chain sees before its gate, de-esser and compressor, so thresholds mean the same for any take


def _require():
    try:
        import numpy as np
        import pedalboard
        import pyloudnorm
        from scipy import ndimage, signal
    except ImportError as exc:
        raise RuntimeError("Voice processing needs faceless-champ[audio] (pedalboard, pyloudnorm, scipy)") from exc
    return np, pedalboard, pyloudnorm, ndimage, signal


@dataclass(frozen=True)
class VoiceChain:
    """Voice processing settings. Gains and thresholds in dB, frequencies in Hz, times in ms."""

    highpass: float = 80.0
    gate: float | None = None  # noise gate threshold; None leaves room tone alone
    de_ess: float = 6.0  # most the sibilance band may be reduced; 0 disables
    de_ess_frequency: float = 5500.0
    mud: float = -2.0  # bell at 250 Hz
    presence: float = 2.0  # bell at 3.5 kHz
    air: float = 1.5  # shelf above 10 kHz
    threshold: float = -30.0  # compressor, relative to a -24 LUFS take
    ratio: float = 3.0
    attack: float = 5.0
    release: float = 90.0
    loudness: float = -16.0  # integrated LUFS of the finished voice
    ceiling: float = -1.5  # limiter, dBFS

    def __post_init__(self):
        finite(self.highpass, "highpass", 20)
        finite(self.de_ess, "de_ess", 0)
        finite(self.de_ess_frequency, "de_ess_frequency", 2000)
        finite(self.ratio, "ratio", 1)
        finite(self.attack, "attack", 0.1)
        finite(self.release, "release", 1)
        for name in ("mud", "presence", "air", "threshold", "loudness", "ceiling"):
            finite(getattr(self, name), name)
        if self.gate is not None:
            finite(self.gate, "gate")
        if not -40 <= self.loudness <= -5:
            raise ValueError("loudness must be between -40 and -5 LUFS")
        if self.ceiling > 0:
            raise ValueError("ceiling must be <= 0 dBFS")

    @classmethod
    def named(cls, name: str, **overrides) -> VoiceChain:
        if name not in PRESETS:
            raise ValueError(f"Unknown voice preset {name!r}; choose from {', '.join(PRESETS)}")
        return replace(PRESETS[name], **overrides)


PRESETS = {
    "narration": VoiceChain(),
    "warm": VoiceChain(highpass=70.0, mud=-1.0, presence=1.0, air=0.5, ratio=2.5, de_ess=4.0),
    "broadcast": VoiceChain(gate=-50.0, presence=3.0, air=2.0, threshold=-34.0, ratio=4.0, de_ess=8.0),
    "clean": VoiceChain(de_ess=0.0, mud=0.0, presence=0.0, air=0.0, ratio=1.0),
}


def cache_root() -> Path:
    return Path(os.environ.get("FC_CACHE_DIR") or Path.home() / ".cache" / "faceless_champ") / "voice"


def _read(path: Path):
    from pedalboard.io import AudioFile

    with AudioFile(str(path)).resampled_to(RATE) as source:
        return source.read(source.frames)  # (channels, samples) float32


def _lufs(np, pyloudnorm, audio) -> float:
    meter = pyloudnorm.Meter(RATE)
    value = meter.integrated_loudness(audio.T.astype(np.float64))
    return float(value)


def _gain(np, audio, db):
    return (audio * np.float32(10 ** (db / 20))).astype(np.float32)


def _de_ess(np, ndimage, signal, audio, chain):
    """Turn the band above ``de_ess_frequency`` down where it carries most of the energy (an "s")."""
    sos = signal.butter(4, chain.de_ess_frequency, "highpass", fs=RATE, output="sos")
    band = signal.sosfiltfilt(sos, audio, axis=-1).astype(np.float32)  # zero phase, so subtracting it cancels
    window = int(0.005 * RATE)
    full_power = ndimage.uniform_filter1d(np.square(audio).mean(axis=0), window)
    band_power = ndimage.uniform_filter1d(np.square(band).mean(axis=0), window)
    allowed = 10 ** (-9 / 10)  # band may hold up to -9 dB of the total
    gain = np.sqrt(np.clip(allowed * full_power / np.maximum(band_power, 1e-12), 0, 1))
    gain = np.maximum(gain, 10 ** (-chain.de_ess / 20)).astype(np.float32)
    gain = ndimage.uniform_filter1d(gain, 2 * window)
    return audio - band * (1 - gain)  # exact input wherever no reduction is needed


def _process(audio, chain: VoiceChain):
    np, pedalboard, pyloudnorm, ndimage, signal = _require()
    # 24 dB/octave: pedalboard's HighpassFilter is first order and leaves most rumble in.
    audio = signal.sosfilt(signal.butter(4, chain.highpass, "highpass", fs=RATE, output="sos"), audio, axis=-1)
    audio = audio.astype(np.float32)
    measured = _lufs(np, pyloudnorm, audio)
    if not np.isfinite(measured):
        return audio  # silence: nothing to shape or normalize
    audio = _gain(np, audio, LEVEL - measured)
    if chain.gate is not None:
        audio = pedalboard.NoiseGate(threshold_db=chain.gate, ratio=4, release_ms=150)(audio, RATE)
    board = pedalboard.Pedalboard(
        [
            pedalboard.PeakFilter(250, chain.mud, 1.0),
            pedalboard.PeakFilter(3500, chain.presence, 0.9),
            pedalboard.HighShelfFilter(10000, chain.air, 0.7),
            pedalboard.Compressor(chain.threshold, chain.ratio, chain.attack, chain.release),
        ]
    )
    audio = board(audio, RATE)
    if chain.de_ess:  # after the compressor, which would otherwise squeeze the reduction back out
        audio = _de_ess(np, ndimage, signal, audio, chain)
    audio = _gain(np, audio, chain.loudness - _lufs(np, pyloudnorm, audio))
    return _limit(np, ndimage, audio, chain.ceiling)


def _limit(np, ndimage, audio, ceiling):
    """Look-ahead sample-peak limiter without make-up gain (pedalboard's Limiter adds make-up gain)."""
    window = int(0.005 * RATE)
    peak = np.abs(audio).max(axis=0)
    needed = np.minimum(1.0, np.float32(10 ** (ceiling / 20)) / np.maximum(peak, 1e-9)).astype(np.float32)
    # Averaging a minimum over twice the window never rises above the gain any sample needs.
    gain = ndimage.uniform_filter1d(ndimage.minimum_filter1d(needed, 2 * window + 1), window)
    return (audio * gain).astype(np.float32)


def process_voice(
    path: str | Path,
    chain: VoiceChain | str | None = None,
    *,
    output: str | Path | None = None,
    **overrides,
) -> Path:
    """Run ``chain`` (a VoiceChain, a preset name or None for "narration") over ``path``.

    Keyword overrides adjust the chain (``loudness=-18``). Returns ``output`` or a cached WAV path.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")
    chain = VoiceChain.named(chain or "narration") if not isinstance(chain, VoiceChain) else chain
    chain = replace(chain, **overrides) if overrides else chain
    stat = path.stat()
    key = hashlib.sha256(repr((str(path.resolve()), stat.st_mtime_ns, stat.st_size, asdict(chain))).encode())
    target = Path(output) if output is not None else cache_root() / f"{path.stem}-{key.hexdigest()[:16]}.wav"
    if output is None and target.is_file():
        return target
    _, pedalboard, *_ = _require()
    audio = _process(_read(path), chain)
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(f".{target.stem}.partial.wav")
    with pedalboard.io.AudioFile(str(partial), "w", RATE, audio.shape[0], bit_depth=24) as sink:
        sink.write(audio)
    partial.replace(target)
    return target


def loudness(path: str | Path) -> float:
    """Integrated loudness of an audio file in LUFS (ITU-R BS.1770 via pyloudnorm); -inf for silence."""
    np, _, pyloudnorm, *_ = _require()
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")
    return _lufs(np, pyloudnorm, _read(path))
