"""The 2.5D glass card arc (S26, S28): cards on a shallow cylinder, a trucking focus, depth of field.

Each card's content is drawn in card-local design px (0..w, 0..h) through a perspective matrix, so
3D cameras, Typst math and HUD pieces work inside a card unchanged (centre a camera on (w/2, h/2)).
"""

from __future__ import annotations

import contextlib
import math

from fx import card_quad, clamp, ease_io, lerp, quad_matrix

from components import hud


@contextlib.contextmanager
def card_space(fr, quad, w, h):
    """Map card-local (0..w, 0..h) onto ``quad`` for the crisp and the glow canvas alike."""
    m = quad_matrix(w, h, quad)
    fr.c.save()
    fr.c.concat(m)
    fr.g.save()
    fr.g.concat(m)
    try:
        yield
    finally:
        fr.g.restore()
        fr.c.restore()


def header(fr, index, title, alpha, x=40.0, y=58.0, color="w"):
    """Card title: a coloured index and a tracked caps label."""
    fr.text(f"{index:02d}", x, y, "sans", 22, 700, color, alpha, align="left", tracking=0.18)
    fr.text(title, x + 46, y, "sans", 22, 700, "ink", alpha * 0.9, align="left", tracking=0.22)


def draw_arc(
    fr,
    t,
    cards,
    focus,
    w=700.0,
    h=600.0,
    alpha=1.0,
    swing=None,
    spacing=620.0,
    angle=0.5,
    dof=7.0,
    dim=0.3,
    center=(960.0, 560.0),
    collapse=0.0,
    zoom=1.0,
):
    """Draw ``cards`` (callables ``card(fr, t, a, active)``) on an arc around ``focus`` (a float card index).

    swing: optional per-card 0..1 swing-in; collapse 0..1 pulls every card into the centre point.
    The active card is at full alpha and sharp; the others drop to ``dim`` with depth-of-field blur.
    """
    if alpha <= 0.003:
        return
    cx0, cy0 = center
    order = sorted(range(len(cards)), key=lambda i: -abs(i - focus))  # far to near
    for i in order:
        d = i - focus
        ad = min(abs(d), 2.0)
        s = 1.0 if swing is None else swing[i]
        if s <= 0.003:
            continue
        side = 1.0 if d >= 0 else -1.0
        x = cx0 + spacing * d * (1 - 0.1 * ad)
        ang = -angle * clamp(d, -1.6, 1.6)
        ang = lerp(side * 1.45, ang, ease_io(s))  # swings in from edge-on
        x = lerp(x + side * 260, x, ease_io(s))
        scale = (1 - 0.16 * ad) * zoom
        y = cy0 + 14 * ad
        if collapse > 0:
            u = ease_io(collapse)
            x, y, scale = lerp(x, cx0, u), lerp(y, cy0, u), scale * (1 - 0.92 * u)
        near = 1 - min(1.0, abs(d))
        a = alpha * s * lerp(dim, 1.0, near) * (1 - collapse)
        if a <= 0.003 or abs(math.cos(ang)) < 0.05:
            continue
        quad = card_quad(x, y, w, h, ang, scale)
        if max(p[0] for p in quad) < -40 or min(p[0] for p in quad) > 1960:
            continue
        with fr.blurred(dof * (1 - near)), card_space(fr, quad, w, h):
            hud.glass_card(fr, 0, 0, w, h, a, r=22, glow=0.25 * near * a, glow_color="ink")
            cards[i](fr, t, a, near)


def truck(t, stops):
    """Focus index along ``stops`` [(time, index)], eased between consecutive stops (0.7 s moves)."""
    f = stops[0][1]
    for t0, idx in stops[1:]:
        f = lerp(f, idx, ease_io(clamp((t - t0) / 0.7)))
    return f
