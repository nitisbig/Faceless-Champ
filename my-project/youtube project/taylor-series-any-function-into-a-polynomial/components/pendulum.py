"""Two pendulums: the exact swing (solve_ivp, rtol 1e-10) and the small-angle one (sin θ ≈ θ), scene-plan.md S34.

pend = Pendulums(theta0=0.35)
th_exact, th_small = pend.angles(t)
draw_pendulum(fr, (960, 260), 420, th_exact, "original")
"""

from __future__ import annotations

import math
from functools import cached_property

from scipy.integrate import solve_ivp


class Pendulums:
    def __init__(self, theta0=0.35, length=1.0, g=9.81, horizon=60.0, slow=1.0):
        self.theta0, self.length, self.g, self.horizon, self.slow = theta0, length, g, horizon, slow
        self.w = math.sqrt(g / length)

    @cached_property
    def _exact(self):
        sol = solve_ivp(
            lambda t, y: [y[1], -(self.w**2) * math.sin(y[0])],
            (0.0, self.horizon),
            [self.theta0, 0.0],
            rtol=1e-10,
            atol=1e-12,
            dense_output=True,
        )
        return sol.sol

    def exact(self, t):
        return float(self._exact(min(max(t * self.slow, 0.0), self.horizon))[0])

    def small(self, t):
        return self.theta0 * math.cos(self.w * t * self.slow)

    def angles(self, t):
        return self.exact(t), self.small(t)


def bob(pivot, length_px, theta):
    return pivot[0] + length_px * math.sin(theta), pivot[1] + length_px * math.cos(theta)


def draw_pendulum(fr, pivot, length_px, theta, color="original", alpha=1.0, r=18.0, glow=0.5, rod=2.0):
    if alpha <= 0.003:
        return
    x, y = bob(pivot, length_px, theta)
    fr.line(pivot[0], pivot[1], x, y, color, rod, alpha)
    fr.circle(pivot[0], pivot[1], 5, "frame", alpha=alpha, fill=True)
    fr.glow_dot(x, y, r, color, alpha, glow)


def trail(fr, pivot, length_px, thetas, color="circle", alpha=1.0, width=2.0):
    """A fading arc of recent bob positions (oldest first)."""
    pts = [bob(pivot, length_px, th) for th in thetas]
    n = len(pts)
    for i in range(1, n):
        a = alpha * (i / n) ** 1.5
        fr.line(*pts[i - 1], *pts[i], color, width, a)
