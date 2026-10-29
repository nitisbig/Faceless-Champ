"""The whole video: chapters 0-6 cut back to back on the narration clock, one continuous audio track.

    python render.py --chapter 9 --preview        # full 720p preview
    python render.py --chapter 9 --final          # full 1080p final (long on this machine)
    python render.py --chapter 9 --preview --start 150 --end 210   # any range, narration seconds
"""

from __future__ import annotations

from importlib import import_module

from cues import AUDIO
from theme import THEME

MODULES = ["scenes.ch0_intro", "scenes.ch1_sliding", "scenes.ch2_dice", "scenes.ch3_smooth",
           "scenes.ch4_images", "scenes.ch5_fourier", "scenes.ch6_recap"]


def chapters():
    return [import_module(m) for m in MODULES]


def check_contiguous(mods):
    t = 0.0
    for m in mods:
        start = getattr(m, "OFFSET", 0.0)
        if abs(start - t) > 1e-6:
            raise ValueError(f"{m.__name__} starts at {start:.3f}s but the previous chapter ends at {t:.3f}s")
        t = start + m.DURATION
    return t


def build(audio: bool = True):
    from faceless_champ import Canvas, Layer, Scene, Sequence

    mods = chapters()
    total = check_contiguous(mods)
    with THEME.use():
        canvas = THEME.canvas()
        parts = [m.build(audio=False) for m in mods]
        video = Sequence(*parts, canvas=canvas)
        if not audio:
            return video
        track = Scene(Canvas(canvas.width, canvas.height, "#00000000"))  # transparent: audio only
        track.add_audio(AUDIO, start=0)
        track.wait_until(total)
        return Layer(video, track, canvas=canvas)


OFFSET = 0.0
DURATION = check_contiguous(chapters())
STILLS = [0.6, 30.0, 100.0, 166.6, 243.2, 305.0, 370.0, 438.9, 456.0]
