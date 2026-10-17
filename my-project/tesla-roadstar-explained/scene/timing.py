"""Forty production shots anchored to unchanged one-based word cue indices."""

from bisect import bisect_right
from dataclasses import dataclass

from faceless_champ import SubtitleTrack

from . import END, ROOT

TITLES = (
    "THE IMPOSSIBLE MANEUVER",
    "ENGINEERING RECONSTRUCTION",
    "THE LIMIT OF GRIP",
    "PRESSURE BECOMES GRIP",
    "DRIVING UPSIDE DOWN",
    "MOMENTUM ON DEMAND",
    "A CONTROLLED HALF-ROLL",
    "SIX DEGREES OF FREEDOM",
    "THE MATHEMATICS OF LANDING",
    "THE COMPLETE PHYSICS",
)
SUBTITLES = (
    "A mathematical reconstruction",
    "One vehicle. Two force systems.",
    "Gravity · normal load · friction",
    "Four fans. A pressure difference.",
    "Suction · gravity · local curvature",
    "Stored gas → exhaust momentum → thrust",
    "Torque · inertia · angular motion",
    "State → requested wrench → nozzle commands",
    "Height · velocity · braking distance",
    "Pressure. Momentum. Controlled forces.",
)

START_CUES = (
    1,
    16,
    39,
    57,
    135,
    160,
    184,
    225,
    264,
    324,
    354,
    394,
    464,
    486,
    542,
    624,
    736,
    789,
    828,
    882,
    963,
    1020,
    1061,
    1100,
    1143,
    1209,
    1279,
    1329,
    1430,
    1483,
    1521,
    1552,
    1571,
    1633,
    1693,
    1755,
    1824,
    1848,
    1885,
    1944,
)
NAMES = (
    "Roadster reveal",
    "Climb and inversion",
    "Rotation and landing",
    "Three physical questions",
    "Blueprint and assembly",
    "Fans versus thrusters",
    "Mass and weight",
    "Contact reaction",
    "Resolve gravity",
    "Tire contact",
    "Derive the grip limit",
    "The vertical limit",
    "Underbody fans",
    "Pressure field",
    "Pressure calculation",
    "Powered wall climb",
    "Static ceiling contact",
    "Curved motion",
    "Radial force balance",
    "Curvature calculation",
    "Release and pressure vessels",
    "Nozzle momentum",
    "Thrust and mass flow",
    "Finite gas budget",
    "Force versus torque",
    "Inertia and two phases",
    "Angular acceleration",
    "The torque couple",
    "Translational and angular state",
    "The feedback loop",
    "Control allocation",
    "Landing alignment",
    "Free-fall experiment",
    "Hovering is not braking",
    "Braking distance",
    "Controlled touchdown",
    "One complete system",
    "Coordinated replay",
    "Physical limitations",
    "Mathematics brought to life",
)

# Read at import; never rewrite cues to make a layout fit.
TRACK = SubtitleTrack.from_srt(ROOT / "cue-per-word.srt", overlap_tolerance=0.001)
CONTEXT = SubtitleTrack.from_srt(ROOT / "normal-subtitle.srt", overlap_tolerance=0.001)


@dataclass(frozen=True)
class Shot:
    index: int
    chapter: int
    letter: str
    cue: int
    end_cue: int
    start: float
    end: float
    name: str

    @property
    def id(self):
        return f"{self.chapter:02d}{self.letter}"


SHOTS = tuple(
    Shot(
        i,
        i // 4 + 1,
        "ABCD"[i % 4],
        cue,
        START_CUES[i + 1] - 1 if i + 1 < len(START_CUES) else TRACK.cues[-1].index,
        TRACK.cue(cue).start if i else 0.0,
        TRACK.cue(START_CUES[i + 1]).start if i + 1 < len(START_CUES) else END,
        NAMES[i],
    )
    for i, cue in enumerate(START_CUES)
)
STARTS = tuple(s.start for s in SHOTS)
CHAPTERS = tuple((SHOTS[i * 4].start, SHOTS[i * 4 + 3].end) for i in range(10))
PREVIEWS = (
    (0, 23.56),
    (74.5, 86.5),
    (132.96, 144.96),
    (208.2, 220.2),
    (321.4, 333.4),
    (394.8, 406.8),
    (509.92, 521.92),
    (550.4, 562.4),
    (654.21, 666.21),
    (687, 699),
)


def shot_at(time):
    return SHOTS[min(39, max(0, bisect_right(STARTS, time) - 1))]


def cue_time(index):
    return TRACK.cue(index).start


def transcript(shot):
    return " ".join(c.text for c in TRACK.cues if shot.cue <= c.index <= shot.end_cue)
