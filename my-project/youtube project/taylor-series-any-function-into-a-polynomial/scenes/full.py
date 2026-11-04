"""The whole video: chapters 0–9 cut back to back on the narration clock, one continuous audio track.

    python render.py --chapter full --preview        # full 720p preview
    python render.py --chapter full --preview --start 250 --end 290   # any range, narration seconds

Chapters join MODULES as each build stage lands (scene-plan.md §6). The last chapter runs to
cues.TOTAL (narration plus the 20 s end-screen hold).
"""

from __future__ import annotations

from importlib import import_module

from cues import AUDIO, ROOT, TOTAL
from theme import THEME

SFX_STEM = ROOT / "sfx" / "sfx_stem.wav"  # python sfx/build_mix.py (cue sheet: sfx/cue_sheet.csv)
VOICE_CHAIN = (
    None  # None keeps the ElevenLabs take as is; a faceless_champ.voice preset name runs that chain (Stage L A/B)
)

MODULES: list[str] = [
    "scenes.ch0_open",
    "scenes.ch1_polynomials",
    "scenes.ch2_copy",
    "scenes.ch3_factorials",
    "scenes.ch4_recipe",
    "scenes.ch5_e",
    "scenes.ch6_sine",
    "scenes.ch7_breaks",
    "scenes.ch8_matters",
    "scenes.ch9_recap",
]  # each chapter joins as its stage lands


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
        voice = AUDIO
        if VOICE_CHAIN:
            from faceless_champ.voice import process_voice

            voice = process_voice(AUDIO, VOICE_CHAIN)
        track.add_audio(voice, start=0, role="voice")
        if SFX_STEM.is_file():
            track.add_audio(SFX_STEM, start=0, role="sfx")
        track.wait_until(total)
        return Layer(video, track, canvas=canvas)


OFFSET = 0.0
DURATION = check_contiguous(chapters())
COMPLETE = abs(DURATION - TOTAL) < 1e-6
STILLS = [0.5, 60.0, 120.0, 200.0, 270.0, 330.0, 420.0, 520.0, 650.0, 720.0, 800.0]
