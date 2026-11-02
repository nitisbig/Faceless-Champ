"""The two dials of the normal distribution: μ (gold) slides the bell, σ (violet) stretches it.

    knob(fr, cx, cy, value, "mu", "bell")            # value in -1..1 turns the indicator ±135°
    dial_pair(fr, cx, cy, mu, sigma, alpha)          # both knobs side by side, values shown live
"""

from __future__ import annotations

import math

import skia
import typmath

from components import hud

SWEEP = math.radians(135)


def knob(fr, cx, cy, value, symbol, color, alpha=1.0, r=46.0, readout=None, active=0.0):
    """A glass knob: track arc, a lit arc from 12 o'clock to the indicator, the symbol below, a live value."""
    if alpha <= 0.003:
        return
    hud.glass_card(fr, cx - r - 14, cy - r - 14, 2 * r + 28, 2 * r + 28, alpha, r=int(r + 14),
                   glow=0.5 * active, glow_color=color)
    rect = skia.Rect.MakeLTRB(cx - r, cy - r, cx + r, cy + r)
    track = skia.Path()
    track.addArc(rect, -90 - math.degrees(SWEEP), 2 * math.degrees(SWEEP))
    fr.path_stroke(track, "line", 3.0, alpha)
    v = max(-1.0, min(1.0, value))
    lit = skia.Path()
    lit.addArc(rect, -90, math.degrees(SWEEP) * v)
    fr.path_stroke(lit, color, 3.4, alpha, glow=0.6 + 0.6 * active)
    ang = -math.pi / 2 + SWEEP * v
    fr.line(cx + 0.25 * r * math.cos(ang), cy + 0.25 * r * math.sin(ang), cx + 0.78 * r * math.cos(ang),
            cy + 0.78 * r * math.sin(ang), color, 3.2, alpha, glow=0.5)
    fr.circle(cx, cy, 4.0, color, alpha=alpha, fill=True)
    typmath.draw(fr, symbol, cx, cy + r + 46, 40, color=color, alpha=alpha, glow=0.3 * active)
    if readout is not None:
        hud.tabular(fr, readout, cx, cy + r + 98, 24, "muted", alpha)


def dial_pair(fr, cx, cy, mu=0.0, sigma=1.0, alpha=1.0, gap=260.0, mu_range=2.0, sigma_range=(0.5, 2.0),
              active_mu=0.0, active_sigma=0.0, readouts=True):
    """μ knob on the left, σ knob on the right. Knob angle maps μ in ±mu_range and σ in sigma_range."""
    lo, hi = sigma_range
    s_val = (sigma - 1.0) / (hi - 1.0) if sigma >= 1.0 else (sigma - 1.0) / (1.0 - lo)
    knob(fr, cx - gap / 2, cy, mu / mu_range, "mu", "bell", alpha, readout=f"{mu:+.2f}" if readouts else None,
         active=active_mu)
    knob(fr, cx + gap / 2, cy, s_val, "sigma", "sigma", alpha, readout=f"{sigma:.2f}" if readouts else None,
         active=active_sigma)
