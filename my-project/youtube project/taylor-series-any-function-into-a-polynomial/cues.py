"""Word-cue timing on the narration source clock.

The SRT has ASR errors and digits for spoken numbers (scene-plan.md §2): anchor those words with
``cue(n)``, never ``word()``. Two stretches were collapsed by the aligner and are hand-timed in
``OVERRIDES`` from a 20 ms loudness envelope of audio.mp3 (speech above −30 dB):

    #693–700  "Notice the pattern. Two is two times one."   speech 254.12–254.98, 255.46–257.18
    #1118–1129 "plus one over one hundred twenty, 2.7167. The true value of e is 2.71828"
               speech 415.82–417.44, 417.84–419.60, 420.28–424.02
"""

from pathlib import Path

from faceless_champ.draw import CueClock

ROOT = Path(__file__).resolve().parent
AUDIO = ROOT / "audio.mp3"
AUDIO_DURATION = 817.008
END_SCREEN = 20.0
TOTAL = AUDIO_DURATION + END_SCREEN

OVERRIDES = {
    694: 254.58,  # the
    695: 254.70,  # pattern.
    696: 255.46,  # Two
    697: 255.86,  # is
    698: 256.26,  # two
    699: 256.55,  # times
    700: 256.90,  # one.
    1118: 415.82,  # plus
    1119: 416.20,  # one
    1120: 416.50,  # over
    1121: 416.75,  # one hundred twenty,
    1122: 417.84,  # 2.7167.
    1123: 420.28,  # The
    1124: 420.45,  # true
    1125: 420.70,  # value
    1126: 420.95,  # of
    1127: 421.10,  # e
    1128: 421.30,  # is
    1129: 421.56,  # 2.71828.
}


class _Clock(CueClock):
    def cue(self, index: int) -> float:
        if index in OVERRIDES:
            return OVERRIDES[index]
        return super().cue(index)


CLOCK = _Clock(ROOT / "cue-per-word.srt")


def track():
    return CLOCK.track


def cue(index: int) -> float:
    """Start time (s) of a one-based word cue (hand-timed where the aligner collapsed)."""
    return CLOCK.cue(index)


def beat(index: int, lead: float = 0.15) -> float:
    """When a visual beat lands: ``lead`` seconds before its word cue (scene-plan.md)."""
    return CLOCK.beat(index, lead)


def word(text: str, after: float = 0.0) -> float:
    """Start time of the first cue matching ``text`` at or after ``after`` seconds."""
    return CLOCK.word(text, after)
