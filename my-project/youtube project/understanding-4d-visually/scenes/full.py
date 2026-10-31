"""The whole video: chapters 0-7 cut back to back on the narration clock, one continuous audio track.

    python render.py --chapter full --preview        # full 720p preview
    python render.py --chapter full --final          # full 1080p final
    python render.py --chapter full --preview --start 150 --end 210   # any range, narration seconds

Chapters join this list as each build stage lands (scene-plan.md §4). The last chapter runs to
cues.TOTAL (narration plus the 20 s end-screen hold).
"""

from __future__ import annotations

from importlib import import_module

from cues import AUDIO, TOTAL
from theme import THEME

MODULES: list[str] = [  # add the next chapter as each stage lands
    "scenes.ch0_intro",
    "scenes.ch1_dimension",
    "scenes.ch2_build",
    "scenes.ch3_slices",
    "scenes.ch4_shadows",
    "scenes.ch5_rotation",
    "scenes.ch6_matters",
    "scenes.ch7_recap",
]


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
    if not mods:
        raise ValueError("no chapters built yet: add modules to scenes/full.py MODULES")
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
COMPLETE = abs(DURATION - TOTAL) < 1e-6
STILLS = [0.6, 30.0, 100.0, 170.0, 245.0, 310.0, 400.0, 450.0, 480.0, 520.0]
