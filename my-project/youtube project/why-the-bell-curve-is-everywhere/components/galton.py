"""The Galton Board: the single source of truth for pegs, paths, pours and counts (scene-plan.md §1.6).

Every ball's route is a seeded row of left/right bits. Positions are evaluated analytically at any
sim time (parabolic hops between pegs, then a short fall onto a hex-packed stack in its bin), so a
frame never depends on the previous one: previews, finals and Kaggle chunks are identical.

    board = Board(rows=12, n=1000, seed=SEED_POUR)
    board.draw(fr, s)                         # s = sim seconds (scenes warp narration time into sim time)
    board.draw_path(fr, board.bits[i], u)     # one route, teal left steps and orange right steps
    board.draw_path_light(fr, alpha)          # every route at once: brightness = share of paths
    board.exact_counts()                      # C(rows, k), never typed
"""

from __future__ import annotations

import math

import numpy as np
import skia
from fx import smooth

# Locked in Stage A by searching seeds 0-19,999 (stage_a_test.seed_report): the 12-row, 1,000-ball pour is
# within 0.4 percentage points of the binomial in every bin, rises monotonically to the centre and is
# mirror-symmetric to within 2 balls: [0, 3, 17, 52, 119, 195, 226, 195, 117, 53, 19, 4, 0].
SEED_POUR = 16205


def binom_row(n: int) -> np.ndarray:
    row = np.ones(1, dtype=np.int64)
    for _ in range(n):
        row = np.convolve(row, [1, 1])
    return row


class Board:
    def __init__(self, rows=12, cx=960.0, top=130.0, dx=56.0, dy=40.0, peg_r=4.0, ball_r=4.0, n=1000,
                 seed=SEED_POUR, release=None, rate=60.0, hop=0.15, fall=0.32, floor=None, bits=None):
        self.rows, self.cx, self.top, self.dx, self.dy = rows, cx, top, dx, dy
        self.peg_r, self.ball_r, self.hop, self.fall = peg_r, ball_r, hop, fall
        self.floor = floor if floor is not None else top + rows * dy + 400.0
        self.wall_top = top + (rows - 0.35) * dy
        if bits is None:
            bits = np.random.default_rng(seed).integers(0, 2, (n, rows))
        self.bits = np.asarray(bits, np.int64)
        self.n = len(self.bits)
        self.release = np.asarray(release, float) if release is not None else np.arange(self.n) / rate
        self.bin = self.bits.sum(axis=1)
        self.k = np.concatenate([np.zeros((self.n, 1), np.int64), np.cumsum(self.bits, axis=1)], axis=1)
        self._waypoints()
        self._stacks()

    # -- geometry -----------------------------------------------------------
    def peg(self, r, k):
        return self.cx + (k - r / 2) * self.dx, self.top + r * self.dy

    def bin_x(self, k):
        return self.cx + (np.asarray(k) - self.rows / 2) * self.dx

    def contact(self, r, k):
        """Where a ball touches peg (r, k): just above it."""
        x, y = self.peg(r, k)
        return x, y - self.peg_r - self.ball_r

    def _waypoints(self):
        n, R = self.n, self.rows
        wp = np.zeros((n, R + 2, 2))
        wp[:, 0] = (self.cx, self.top - 1.4 * self.dy)  # funnel mouth
        for r in range(R):
            x, y = self.peg(r, self.k[:, r])
            wp[:, r + 1, 0], wp[:, r + 1, 1] = x, y - self.peg_r - self.ball_r
        wp[:, R + 1, 0] = self.bin_x(self.bin)
        wp[:, R + 1, 1] = self.top + R * self.dy - self.ball_r
        self.wp = wp
        self.t_exit = (R + 1) * self.hop

    @property
    def per_layer(self) -> int:
        return max(1, int((self.dx - 6) // (2 * self.ball_r)))

    def stack_pos(self, k, j):
        """Centre of the j-th ball (0-based) stacked in bin k: hex packing, bottom up."""
        m, d = self.per_layer, 2 * self.ball_r
        layer, c = np.divmod(np.asarray(j), m)
        odd = layer % 2
        x = self.bin_x(k) - (m - 1) / 2 * d + c * d + odd * d / 2 - (odd * (c == m - 1)) * d / 2
        y = self.floor - self.ball_r - layer * d * 0.87
        return x, y

    def _stacks(self):
        order = np.lexsort((np.arange(self.n), self.release))
        j = np.zeros(self.n, np.int64)
        seen = np.zeros(self.rows + 1, np.int64)
        for i in order:
            j[i] = seen[self.bin[i]]
            seen[self.bin[i]] += 1
        self.slot = j
        self.rest = np.stack(self.stack_pos(self.bin, j), axis=1)
        self.landed_at = self.release + self.t_exit + self.fall

    # -- motion -------------------------------------------------------------
    def positions(self, s, idx=None):
        """(xy, phase) at sim time ``s``. phase: -1 waiting, 0 in the pegs, 1 falling, 2 landed."""
        idx = np.arange(self.n) if idx is None else np.asarray(idx)
        tau = s - self.release[idx]
        xy = np.zeros((len(idx), 2))
        phase = np.full(len(idx), -1, np.int64)

        hopping = (tau >= 0) & (tau < self.t_exit)
        if hopping.any():
            h = tau[hopping] / self.hop
            seg = np.minimum(h.astype(np.int64), self.rows)
            u = h - seg
            rows = idx[hopping]
            p0 = self.wp[rows, seg]
            p1 = self.wp[rows, seg + 1]
            first = seg == 0  # the funnel drop is a straight fall
            ux = np.where(first, 0.0, 1 - (1 - u) ** 2)
            bounce = np.where(first, 0.0, 0.28 * self.dy * np.sin(np.pi * np.minimum(u * 1.25, 1.0)))
            xy[hopping, 0] = p0[:, 0] + (p1[:, 0] - p0[:, 0]) * np.where(first, u, ux)
            xy[hopping, 1] = p0[:, 1] + (p1[:, 1] - p0[:, 1]) * u * u - bounce * (1 - u)
            phase[hopping] = 0

        falling = (tau >= self.t_exit) & (tau < self.t_exit + self.fall)
        if falling.any():
            u = (tau[falling] - self.t_exit) / self.fall
            rows = idx[falling]
            p0, p1 = self.wp[rows, self.rows + 1], self.rest[rows]
            e = u * u
            xy[falling] = p0 + (p1 - p0) * e[:, None]
            phase[falling] = 1

        done = tau >= self.t_exit + self.fall
        xy[done] = self.rest[idx[done]]
        phase[done] = 2
        return xy, phase

    def bin_counts(self, s) -> np.ndarray:
        return np.bincount(self.bin[self.landed_at <= s], minlength=self.rows + 1)

    def exact_counts(self) -> np.ndarray:
        return binom_row(self.rows)

    def pile_top(self, s):
        """Height of each bin's pile in px at sim time ``s`` (for the bell trace over the stack)."""
        c = self.bin_counts(s)
        layers = np.ceil(c / self.per_layer)
        return self.floor - layers * 2 * self.ball_r * 0.87

    # -- drawing ------------------------------------------------------------
    def draw_frame(self, fr, alpha=1.0, rows_shown=None, funnel=True, walls=True, flash=None):
        """Pegs, funnel, bin walls and floor. ``rows_shown`` (float) cascades rows in; ``flash`` {(r, k): a}."""
        if alpha <= 0.003:
            return
        shown = self.rows if rows_shown is None else rows_shown
        for r in range(self.rows):
            a = alpha * smooth(min(1.0, max(0.0, shown - r)))
            if a <= 0.003:
                continue
            for k in range(r + 1):
                x, y = self.peg(r, k)
                f = flash.get((r, k), 0.0) if flash else 0.0
                fr.circle(x, y, self.peg_r, "line", alpha=a, fill=True)
                if f > 0:
                    fr.circle(x, y, self.peg_r * 1.15, "ink", alpha=a * f, fill=True, glow=0.8 * f)
        if funnel:
            fx0, fy = self.cx, self.top - 1.4 * self.dy
            fr.poly([fx0 - 70, fx0 - 9, fx0 - 9], [fy - 60, fy - 6, fy + 6], "line", 2.0, alpha)
            fr.poly([fx0 + 70, fx0 + 9, fx0 + 9], [fy - 60, fy - 6, fy + 6], "line", 2.0, alpha)
        if walls:
            wa = alpha * smooth(min(1.0, max(0.0, shown - self.rows + 1)))
            for k in range(self.rows + 2):
                x = self.cx + (k - 0.5 - self.rows / 2) * self.dx
                fr.line(x, self.wall_top, x, self.floor, "grid", 1.4, wa)
            x0 = self.cx - (self.rows / 2 + 0.5) * self.dx
            fr.line(x0 - 10, self.floor, x0 + (self.rows + 1) * self.dx + 10, self.floor, "line", 2.0, wa)

    def draw_balls(self, fr, s, alpha=1.0, color="ball", landed_alpha=0.82, glow=0.5, skip=()):
        """All balls at sim time ``s``: landed ones as one batched path, moving ones with a soft glow."""
        if alpha <= 0.003:
            return
        xy, phase = self.positions(s)
        r = self.ball_r
        rest = skia.Path()
        for x, y in xy[phase == 2]:
            rest.addCircle(float(x), float(y), r)
        fr.path_fill(rest, color, alpha * landed_alpha)
        moving = np.flatnonzero((phase == 0) | (phase == 1))
        skip = set(skip)
        path = skia.Path()
        for i in moving:
            if i not in skip:
                path.addCircle(float(xy[i, 0]), float(xy[i, 1]), r)
        fr.path_fill(path, color, alpha, glow=glow)

    def draw(self, fr, s, alpha=1.0, **kw):
        self.draw_frame(fr, alpha, **kw)
        self.draw_balls(fr, s, alpha)

    def draw_hero(self, fr, i, s, alpha=1.0, trail=0.35, color="ball", size=1.6):
        """One highlighted ball with a fading trail (exact past positions)."""
        if alpha <= 0.003 or s < self.release[i]:
            return
        steps = 14
        ts = s - trail * np.linspace(1, 0, steps)
        pts = np.array([self.positions(t, [i])[0][0] for t in ts])
        live = ts >= self.release[i]
        pts = pts[live]
        for k in range(1, len(pts)):
            a = alpha * (k / len(pts)) ** 2 * 0.7
            fr.line(pts[k - 1, 0], pts[k - 1, 1], pts[k, 0], pts[k, 1], color, self.ball_r * 1.3 * k / len(pts), a,
                    glow=0.4)
        x, y = pts[-1]
        fr.glow_dot(x, y, self.ball_r * size, color, alpha, strength=1.2)

    def hit_flash(self, i, s, width=0.18):
        """{(row, peg): strength} for the peg ball ``i`` is touching around sim time ``s``."""
        tau = s - self.release[i]
        out = {}
        for r in range(self.rows):
            dt = tau - (r + 1) * self.hop
            if -0.02 < dt < width:
                out[(r, int(self.k[i, r]))] = math.exp(-max(dt, 0.0) / (width / 3))
        return out

    # -- routes ---------------------------------------------------------------
    def route(self, bits):
        """Contact points of a route (bits per row), ending at its bin mouth."""
        bits = np.asarray(bits, np.int64)
        k = np.concatenate([[0], np.cumsum(bits)])
        pts = [self.contact(r, k[r]) for r in range(len(bits))]
        last = len(bits)
        if last == self.rows:
            pts.append((float(self.bin_x(k[-1])), self.top + self.rows * self.dy - self.ball_r))
        else:
            pts.append(self.contact(last, k[-1]))
        return np.array(pts), bits

    def draw_path(self, fr, bits, u=1.0, alpha=1.0, width=3.0, glow=0.6, tint=None):
        """A route drawn step by step: teal for each left step, orange for each right step."""
        if alpha <= 0.003 or u <= 0:
            return
        pts, bits = self.route(bits)
        steps = len(bits)
        done = u * steps
        for r in range(steps):
            f = min(1.0, max(0.0, done - r))
            if f <= 0:
                break
            (x0, y0), (x1, y1) = pts[r], pts[r + 1]
            c = tint or ("right" if bits[r] else "left")
            fr.line(x0, y0, x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, c, width, alpha, glow=glow)

    def _segments(self, rows):
        """Every peg-to-peg segment down to ``rows``: (r, k, b, p0, p1)."""
        for r in range(rows):
            for k in range(r + 1):
                p0 = self.contact(r, k)
                for b in (0, 1):
                    p1 = self.contact(r + 1, k + b) if r + 1 < self.rows else (
                        float(self.bin_x(k + b)), self.top + self.rows * self.dy - self.ball_r)
                    yield r, k, b, p0, p1

    def draw_path_light(self, fr, alpha=1.0, rows=None, color="ball", width=2.4, glow=0.6, gamma=2.2):
        """All 2^rows routes at once. A segment's brightness is the share of routes through it, normalised per
        row, so the bell shows as light before any ball falls (S06A)."""
        if alpha <= 0.003:
            return
        rows = self.rows if rows is None else rows
        for r, k, b, p0, p1 in self._segments(rows):
            row = binom_row(r)
            share = (row[k] / row.max()) ** gamma
            fr.line(p0[0], p0[1], p1[0], p1[1], color, width * (0.6 + 0.6 * share), alpha * (0.05 + 0.95 * share),
                    glow=glow * share)

    def draw_fan(self, fr, r0, k0, alpha=1.0, color="muted", width=1.6):
        """Ghost futures below peg (r0, k0): every reachable segment, weighted by its probability."""
        if alpha <= 0.003:
            return
        for r, k, b, p0, p1 in self._segments(self.rows):
            if r < r0 or k < k0 or k > k0 + (r - r0):
                continue
            row = binom_row(r - r0)
            p = row[k - k0] / row.max()
            fr.line(p0[0], p0[1], p1[0], p1[1], color, width, alpha * (0.15 + 0.85 * p) * 0.6)


def warp(t, keys, ease=0.6):
    """Narration time -> sim time. ``keys`` = [(narration_t, rate), ...] sorted by time.

    Each new rate is eased in over ``ease`` seconds, so a speed ramp ("x20") never jerks.
    Before the first key the first rate applies (negative sim time = balls still waiting).
    """
    t0, r0 = keys[0]
    if t <= t0:
        return (t - t0) * r0
    s = 0.0
    for i, (kt, rate) in enumerate(keys):
        prev = keys[i - 1][1] if i else rate
        nxt = keys[i + 1][0] if i + 1 < len(keys) else math.inf
        end = min(t, nxt)
        u = min(1.0, (end - kt) / ease)
        s += prev * (end - kt) + (rate - prev) * (ease * (u ** 3 - u ** 4 / 2) + max(0.0, end - kt - ease))
        if t <= nxt:
            return s
    return s
