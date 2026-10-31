"""The Matrix Plaque: a glass card holding a matrix with row, column and block highlights.

Entries are Typst math (``"1"``, ``"cos theta"``, ``"-sin theta"``). Live values: pass numbers already formatted,
e.g. f"{math.cos(a):.2f}"; they use the cached digit strip, so they never recompile.
"""

from __future__ import annotations

import skia
import typmath
from fx import col

from components.hud import glass_card
from components.vector_slot import bracket


def layout(rows, cols, cx, cy, cell_w, cell_h):
    """Centre of every cell: grid[r][c] -> (x, y)."""
    x0 = cx - cell_w * (cols - 1) / 2
    y0 = cy - cell_h * (rows - 1) / 2
    return [[(x0 + c * cell_w, y0 + r * cell_h) for c in range(cols)] for r in range(rows)]


def draw_matrix(fr, cx, cy, cells, colors=None, cell_w=120.0, cell_h=76.0, size=42.0, alpha=1.0, card=True,
                entry_alpha=None, glow=None, row_hi=None, col_hi=None, blocks=(), pad=34.0, brackets=1.0):
    """Draw a matrix centred at (cx, cy); returns the cell-centre grid.

    colors / entry_alpha / glow: dicts {(r, c): value}. row_hi / col_hi: {index: (color, strength)}.
    blocks: [((r0, c0, r1, c1), color_a, color_b, strength)], a gradient wash over a sub-block (inclusive).
    """
    if alpha <= 0.003:
        return []
    rows, cols = len(cells), len(cells[0])
    grid = layout(rows, cols, cx, cy, cell_w, cell_h)
    w, h = cell_w * cols, cell_h * rows
    if card:
        glass_card(fr, cx - w / 2 - pad - 18, cy - h / 2 - pad, w + 2 * pad + 36, h + 2 * pad, alpha)
    colors, entry_alpha, glow = colors or {}, entry_alpha or {}, glow or {}
    for (r0, c0, r1, c1), ca, cb, s in blocks:
        if s <= 0.003:
            continue
        x0, y0 = grid[r0][c0][0] - cell_w / 2 + 6, grid[r0][c0][1] - cell_h / 2 + 6
        x1, y1 = grid[r1][c1][0] + cell_w / 2 - 6, grid[r1][c1][1] + cell_h / 2 - 6
        shader = skia.GradientShader.MakeLinear(
            [skia.Point(x0, y0), skia.Point(x1, y1)], [col(ca, 0.20 * s * alpha), col(cb, 0.20 * s * alpha)]
        )
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, y0, x1, y1), 12, 12)
        fr.c.drawRRect(rr, skia.Paint(AntiAlias=True, Shader=shader))
        border = skia.GradientShader.MakeLinear(
            [skia.Point(x0, y0), skia.Point(x1, y1)], [col(ca, 0.9 * s * alpha), col(cb, 0.9 * s * alpha)]
        )
        fr.c.drawRRect(rr, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.6, Shader=border))
    for r, (color, s) in (row_hi or {}).items():
        x0, y = grid[r][0][0] - cell_w / 2 + 4, grid[r][0][1] - cell_h / 2 + 8
        fr.rrect(x0, y, w - 8, cell_h - 16, 10, fill=color, fill_alpha=0.14 * s * alpha, stroke=color,
                 width=1.2, alpha=0.7 * s * alpha)
    for c, (color, s) in (col_hi or {}).items():
        x, y0 = grid[0][c][0] - cell_w / 2 + 8, grid[0][c][1] - cell_h / 2 + 4
        fr.rrect(x, y0, cell_w - 16, h - 8, 10, fill=color, fill_alpha=0.14 * s * alpha, stroke=color,
                 width=1.2, alpha=0.7 * s * alpha)
    for r in range(rows):
        for c in range(cols):
            tex = cells[r][c]
            a = alpha * entry_alpha.get((r, c), 1.0)
            if tex and a > 0.003:
                typmath.term(fr, tex, *grid[r][c], size, colors.get((r, c), "ink"), a, glow=glow.get((r, c), 0.0))
    bracket(fr, cx - w / 2 - 6, cy - h / 2 - 6, cy + h / 2 + 6, -1, "ink", alpha * 0.9, draw=brackets)
    bracket(fr, cx + w / 2 + 6, cy - h / 2 - 6, cy + h / 2 + 6, 1, "ink", alpha * 0.9, draw=brackets)
    return grid


def zw_rotation_cells(angle="theta"):
    """The 4x4 ZW rotation: identity on x, y and the 2x2 rotation in the z-w block."""
    c, s = f"cos {angle}", f"sin {angle}"
    return [
        ["1", "0", "0", "0"],
        ["0", "1", "0", "0"],
        ["0", "0", c, "-" + s],
        ["0", "0", s, c],
    ]
