"""Digit Lock: a tabular readout whose digits turn lime when they match the target (scene-plan.md §1.4.3).

lock(fr, "2.7167", "2.71828", 960, 700, 64)              # "2.71" lime, "67" muted
lock(fr, s, target, x, y, 64, glint=lin(t, t1, t1 + 0.3))  # one-frame-ish glint on the newest lock
"""

from __future__ import annotations

from faceless_champ.draw import font


def matched(s: str, target: str) -> int:
    """How many leading characters of ``s`` agree with ``target`` (digits only count; '.' rides along)."""
    n = 0
    for a, b in zip(s, target):
        if a != b:
            break
        n += 1
    while n and not s[n - 1].isdigit():
        n -= 1
    return n


def lock(
    fr,
    s,
    target,
    x,
    y,
    size=60.0,
    alpha=1.0,
    align="center",
    glint=0.0,
    family="display",
    weight=600,
    base="muted",
    locked="result",
    force=None,
):
    """Draw ``s`` with fixed-advance digits; matched prefix in ``locked``. Returns (width, x of the last locked digit)."""
    if alpha <= 0.003 or not s:
        return 0.0, None
    f = font(family, size, weight)
    adv = f.measureText("0")
    widths = [adv if ch.isdigit() else f.measureText(ch) for ch in s]
    total = sum(widths)
    cx = x - total / 2 if align == "center" else x - total if align == "right" else x
    n = matched(s, target) if force is None else force
    last = None
    for i, (ch, wd) in enumerate(zip(s, widths)):
        off = (wd - f.measureText(ch)) / 2
        on = i < n
        fr.text(
            ch, cx + off, y, family, size, weight, locked if on else base, alpha, align="left", glow=0.35 if on else 0.0
        )
        if on:
            last = cx + wd / 2
        cx += wd
    if last is not None and 0 < glint < 1:
        fr.glint(last, y - size * 0.35, size * 1.2, alpha * (1 - glint))
    return total, last
