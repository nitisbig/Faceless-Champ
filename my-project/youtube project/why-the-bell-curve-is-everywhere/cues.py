"""Word-cue timing helpers on the narration source clock.

The SRT text has ASR errors and digits for spoken numbers (see scene-plan.md): anchor those words with
``cue(n)``, never ``word()``.
"""

import re
from functools import lru_cache
from pathlib import Path

from faceless_champ import SubtitleTrack

ROOT = Path(__file__).resolve().parent
AUDIO = ROOT / "audio.mp3"
AUDIO_DURATION = 441.576
END_SCREEN = 20.0
TOTAL = AUDIO_DURATION + END_SCREEN


@lru_cache(maxsize=1)
def track():
    return SubtitleTrack.from_srt(ROOT / "cue-per-word.srt", overlap_tolerance=0.001)


def cue(index: int) -> float:
    """Start time (s) of a one-based word cue."""
    return track().cue(index).start


def beat(index: int, lead: float = 0.15) -> float:
    """When a visual beat lands: ``lead`` seconds before its word cue (scene-plan.md)."""
    return max(0.0, cue(index) - lead)


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def word(text: str, after: float = 0.0) -> float:
    """Start time of the first cue matching ``text`` at or after ``after`` seconds."""
    target = _norm(text)
    for c in track().cues:
        if c.start >= after - 1e-6 and _norm(c.text) == target:
            return c.start
    raise KeyError(f"word {text!r} not found after {after}")
