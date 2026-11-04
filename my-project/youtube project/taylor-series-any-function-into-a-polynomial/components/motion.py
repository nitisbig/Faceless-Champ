"""The film's shared motion curves (scene-plan.md §1.4).

u = spring(t, t0)            # the hug: 0 → 1 in 0.7 s with one ~4 % overshoot
p = settle(t, t0)            # 0..1 pulse that peaks just after the spring lands (glow, sweep)
"""

from __future__ import annotations

import math

from faceless_champ.draw import clamp, ease_out, lin

HUG = 0.7  # seconds from n_from to n_to
OVERSHOOT = 0.04

_Z = -math.log(OVERSHOOT) / math.sqrt(math.pi**2 + math.log(OVERSHOOT) ** 2)  # damping ratio for the overshoot
_W = 4.6 / (_Z * HUG)  # natural frequency: inside 1 % by HUG seconds
_WD = _W * math.sqrt(1 - _Z * _Z)


def spring(t: float, t0: float) -> float:
    """Under-damped step response starting at ``t0``: peaks at 1 + OVERSHOOT, settles by ``t0 + HUG``."""
    tau = t - t0
    if tau <= 0:
        return 0.0
    if tau >= HUG * 1.6:
        return 1.0
    e = math.exp(-_Z * _W * tau)
    return 1 - e * (math.cos(_WD * tau) + _Z / math.sqrt(1 - _Z * _Z) * math.sin(_WD * tau))


def settle(t: float, t0: float, width: float = 0.9) -> float:
    """A soft pulse that rises as the spring lands (``t0 + 0.55 HUG``) and fades over ``width`` s."""
    a = t0 + 0.55 * HUG
    if t < a or t > a + width:
        return 0.0
    u = (t - a) / width
    return math.sin(math.pi * u) ** 1.5


def enter(t: float, t0: float, dur: float = 0.55) -> float:
    """Aion entrance: ease-out over 0.45–0.7 s."""
    return ease_out(lin(t, t0, t0 + dur))


def leave(t: float, t0: float, dur: float = 0.3) -> float:
    """Aion exit: 1 → 0, accelerating, 0.3 s."""
    u = clamp((t - t0) / dur)
    return 1 - u * u
