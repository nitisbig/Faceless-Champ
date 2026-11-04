"""Derivative Ladder: a glass card of rows f(0), f′(0), f″(0) … filled one at a time (scene-plan.md §1.6.3).

    lad = Ladder(x=1300, y=200, rows=5, name="cos")
    lad.draw(fr, t, fills=[(t1, 1), (t2, 0), (t3, -1)], struck={1: t4})

Values are exact (``taylor.derivs_at``); +1 is orange, −1 teal, 0 muted. A struck row fades to a ghost with a hairline.
"""

from __future__ import annotations

import sympy as sp

from faceless_champ.draw import back, ease_out, hud, lin
from faceless_champ.draw import mathtype as typmath

ROW = 64.0
PRIMES = ["", "′", "″", "‴"]


def label(k: int, at: str = "0", name: str = "f") -> str:
    """Typst for the k-th derivative at a point: f(0), f'(0), f''(0), f'''(0), f^((4))(0)."""
    if k < 4:
        return f"{name}{"'" * k}({at})"
    return f"{name}^(({k}))({at})"


def value_token(v) -> tuple[str, str]:
    """(typst, color token) for a ladder value."""
    v = sp.nsimplify(v)
    if v == 0:
        return "0", "muted"
    if v > 0:
        return f"+{v}", "plus"
    return f"−{-v}", "minus"


class Ladder:
    def __init__(self, x=1280.0, y=180.0, rows=5, name="f", at="0", w=440.0, title=None):
        self.x, self.y, self.rows, self.name, self.at, self.w = x, y, rows, name, at, w
        self.title = title

    @property
    def h(self):
        return 40 + ROW * self.rows + (52 if self.title else 0)

    def row_y(self, k: int) -> float:
        return self.y + (52 if self.title else 0) + 20 + ROW * (k + 0.5)

    def draw(self, fr, t, fills=(), struck=None, alpha=1.0, rows_shown=None, focus=None, card=True):
        """``fills``: [(time, value)] in row order; ``struck``: {row: time}; ``focus``: a row to rim in gold;
        ``card=False`` floats the rows on the stage with no glass card."""
        if alpha <= 0.003:
            return
        if card:
            hud.glass_card(fr, self.x, self.y, self.w, self.h, alpha)
        if self.title:
            fr.text(self.title, self.x + 32, self.y + 50, "sans", 22, 700, "muted", alpha, align="left", tracking=0.22)
        struck = struck or {}
        n = self.rows if rows_shown is None else rows_shown
        for k in range(n):
            yk = self.row_y(k)
            ghost = 1.0 - 0.75 * ease_out(lin(t, struck[k], struck[k] + 0.4)) if k in struck else 1.0
            ra = alpha * ghost
            if focus == k:
                fr.rrect(
                    self.x + 14,
                    yk - ROW / 2 + 6,
                    self.w - 28,
                    ROW - 12,
                    10,
                    stroke="copy",
                    width=1.2,
                    alpha=alpha * 0.8,
                )
            typmath.draw(fr, label(k, self.at, self.name), self.x + 40, yk, 34, "ink", ra * 0.92, align="left")
            fr.line(self.x + 40, yk + ROW / 2, self.x + self.w - 40, yk + ROW / 2, "line", 1.0, 0.6 * alpha)
            if k < len(fills):
                tk, v = fills[k]
                u = lin(t, tk, tk + 0.5)
                if u > 0:
                    s, colr = value_token(v)
                    sc = back(u) if u < 1 else 1.0
                    typmath.draw(
                        fr,
                        s,
                        self.x + self.w - 56,
                        yk,
                        36 * (0.6 + 0.4 * sc),
                        colr,
                        ra * min(1, u * 2),
                        glow=0.4 * (1 - u) + 0.15,
                        align="right",
                    )
            if k in struck:
                su = ease_out(lin(t, struck[k], struck[k] + 0.35))
                if su > 0:
                    fr.line(self.x + 32, yk, self.x + 32 + (self.w - 64) * su, yk, "frame", 1.2, alpha * 0.8)


def float_rows(fr, x, y, rows, alpha=1.0, w=440.0, size=34.0, row_h=ROW, rail=True):
    """Ladder rows on the bare stage (no card). ``rows``: [(label, value or None, row alpha, gold mark 0..1)];
    labels and values are Typst, colored with ``tc`` where they need a role."""
    if alpha <= 0.003 or not rows:
        return
    if rail:
        fr.line(x + 12, y + 6, x + 12, y + row_h * len(rows) - 6, "line", 1.0, 0.7 * alpha)
    for k, (lab, val, ra, mark) in enumerate(rows):
        yk = y + row_h * (k + 0.5)
        a = alpha * ra
        if a > 0.003:
            typmath.draw(fr, lab, x + 40, yk, size, None, a * 0.92, align="left")
            fr.line(x + 40, yk + row_h / 2, x + w - 40, yk + row_h / 2, "line", 1.0, 0.6 * a)
            if val is not None:
                typmath.draw(fr, val, x + w - 56, yk, size * 1.06, None, a, glow=0.15, align="right")
        if mark > 0.003:
            fr.glow_dot(x + 12, yk, 5.0, "copy", alpha * mark, 1.0)
