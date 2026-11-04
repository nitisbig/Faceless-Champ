"""Taylor math: coefficients, Horner evaluation, hug zones, partial sums and the × / + program.

Pure math, no drawing (scene-plan.md §1.6.1). Every number the film shows comes from here or from SymPy,
and ``tests/test_taylor.py`` pins the values of §5.

    c = coeffs("sin", 7)                 # [0, 1, 0, -1/6, 0, 1/120, 0, -1/5040] as floats
    y = evaluate(c, xs)                  # Horner, vectorised
    hug_zone("cos", 4)                   # 1.40: |cos − P4| < 0.01 on [−1.40, 1.40]
    ops(c[:6])                           # the 4 ×, 2 + program a chip runs for x − x³/6 + x⁵/120
"""

from __future__ import annotations

import math
from functools import cache

import numpy as np
import sympy as sp

X = sp.Symbol("x", real=True)
B = sp.Symbol("beta", positive=True)

FUNCS = {
    "cos": sp.cos(X),
    "sin": sp.sin(X),
    "exp": sp.exp(X),
    "hill": 1 / (1 + X**2),
}


def expr(f) -> sp.Expr:
    return FUNCS[f] if isinstance(f, str) else sp.sympify(f)


@cache
def _numeric(f):
    return sp.lambdify(X, expr(f), "numpy")


def fn(f):
    """The true function as a numpy callable."""
    return _numeric(f)


@cache
def coeffs_exact(f, n: int, a=0) -> tuple:
    """Exact Taylor coefficients c0..cn of ``f`` about ``a`` (in powers of (x − a))."""
    s = sp.series(expr(f), X, a, n + 1).removeO()
    poly = sp.Poly(sp.expand(s.subs(X, X + a)), X) if a else sp.Poly(s, X)
    out = [sp.Integer(0)] * (n + 1)
    for (k,), v in poly.terms():
        if k <= n:
            out[k] = sp.nsimplify(v)
    return tuple(out)


def coeffs(f, n: int, a=0) -> np.ndarray:
    """Float Taylor coefficients c0..cn of ``f`` about ``a``."""
    return np.array([float(v) for v in coeffs_exact(f, n, a)])


def derivs_at(f, a=0, k: int = 6) -> list:
    """f(a), f′(a), …, f⁽ᵏ⁾(a) as exact SymPy values (the Derivative Ladder)."""
    e = expr(f)
    return [sp.simplify(sp.diff(e, X, j).subs(X, a)) for j in range(k + 1)]


def evaluate(c, xs, a: float = 0.0):
    """Horner evaluation of Σ cₖ (x − a)ᵏ for coefficient arrays of any length."""
    xs = np.asarray(xs, dtype=float) - a
    acc = np.zeros_like(xs) + c[-1]
    for ck in c[-2::-1]:
        acc = acc * xs + ck
    return acc


def blend(c_from, c_to, u: float) -> np.ndarray:
    """Coefficients of the in-between copy while P_from springs into P_to (``u`` may overshoot past 1)."""
    m = max(len(c_from), len(c_to))
    a = np.pad(np.asarray(c_from, float), (0, m - len(c_from)))
    b = np.pad(np.asarray(c_to, float), (0, m - len(c_to)))
    return a + (b - a) * u


def hug_zone(f, n: int, tol: float = 0.01, side: str = "both", a: float = 0.0, reach: float = 12.0) -> float:
    """Largest r with |f − Pₙ| < tol on the whole stretch around ``a`` (``side`` = "both", "right", "left")."""
    c, g = coeffs(f, n, a), fn(f)
    dx = 1e-3
    steps = np.arange(1, int(reach / dx) + 1) * dx
    for sgn in {"both": (1, -1), "right": (1,), "left": (-1,)}[side]:
        xs = a + sgn * steps
        bad = np.nonzero(np.abs(g(xs) - evaluate(c, xs, a)) >= tol)[0]
        r = steps[bad[0] - 1] if len(bad) and bad[0] else (0.0 if len(bad) else reach)
        reach = min(reach, r)
    return float(reach)


def partial_sums(c, x: float) -> np.ndarray:
    """Running sums S₀, S₁, … of Σ cₖ xᵏ at one point (zero terms included)."""
    return np.cumsum(np.asarray(c, float) * float(x) ** np.arange(len(c)))


def terms(c, x: float) -> np.ndarray:
    return np.asarray(c, float) * float(x) ** np.arange(len(c))


def ops(c, x: float | None = None) -> list[dict]:
    """The × / + program a chip runs to evaluate Σ cₖ xᵏ by Horner's rule.

    An odd or even polynomial is evaluated in u = x² (one extra × up front, and one × by x at the end for odd).
    Each step is ``{"op": "×" or "+", "a": str, "b": str, "value": float | None}``.
    """
    c = [float(v) for v in c]
    while c and c[-1] == 0:
        c.pop()
    nz = [k for k, v in enumerate(c) if v]
    parity = {k % 2 for k in nz}
    prog = []
    xv = None if x is None else float(x)

    def step(op, a, b, v):
        prog.append({"op": op, "a": a, "b": b, "value": v})
        return v

    if len(parity) == 1 and len(nz) > 1:
        odd = parity == {1}
        u = step("×", "x", "x", None if xv is None else xv * xv)
        sub = [c[k] for k in range(nz[0], nz[-1] + 1, 2)]  # coefficients of 1, u, u², … (after the x for odd)
        acc = sub[-1]
        accs = _fmt(acc)
        for ck in sub[-2::-1]:
            acc = step("×", accs, "x²", None if u is None else acc * u)
            accs = "·"
            acc = step("+", "·", _fmt(ck), None if acc is None else acc + ck)
        if odd:
            step("×", "·", "x", None if acc is None else acc * xv)
        return prog
    acc = c[-1]
    accs = _fmt(acc)
    for ck in c[-2::-1]:
        acc = step("×", accs, "x", None if xv is None else acc * xv)
        accs = "·"
        if ck:
            acc = step("+", "·", _fmt(ck), None if acc is None else acc + ck)
    return prog


def _fmt(v: float) -> str:
    fr = sp.nsimplify(v, rational=True)
    return str(fr).replace("-", "−")


# ------------------------------------------------------------- named results (scene-plan.md §5)


def e_sums(n: int) -> np.ndarray:
    """Partial sums of Σ 1/k! for k = 0..n."""
    return np.cumsum([1 / math.factorial(k) for k in range(n + 1)])


def correct_decimals(value: float, truth: float, most: int = 12) -> int:
    """How many decimals of ``value`` agree with ``truth`` after truncation."""
    for d in range(most + 1):
        if math.floor(value * 10**d) != math.floor(truth * 10**d):
            return d - 1
    return most


def gamma_series(order: int = 4) -> sp.Expr:
    """(1 − β²)^(−1/2) expanded in β up to β^order (S45C)."""
    return sp.series((1 - B**2) ** sp.Rational(-1, 2), B, 0, order + 1).removeO()


def ke_ratio(beta: float) -> float:
    """Relativistic kinetic energy over Newton's ½mv² at speed β = v/c."""
    g = 1 / math.sqrt(1 - beta * beta)
    return (g - 1) / (0.5 * beta * beta)


def hill_poles() -> list[complex]:
    z = sp.Symbol("z")
    return [complex(r) for r in sp.solve(1 + z**2, z)]
