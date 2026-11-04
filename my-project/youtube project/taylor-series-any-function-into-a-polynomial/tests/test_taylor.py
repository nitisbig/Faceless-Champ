"""Pins every number of scene-plan.md §5."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest
import sympy as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from components import taylor as T


@pytest.mark.parametrize(
    "f,n,r",
    [("cos", 0, 0.14), ("cos", 2, 0.70), ("cos", 4, 1.40), ("cos", 6, 2.13), ("cos", 8, 2.88), ("cos", 10, 3.62)]
    + [("sin", n, r) for n, r in zip(range(1, 18, 2), (0.39, 1.04, 1.76, 2.50, 3.25, 4.00, 4.75, 5.50, 6.25))],
)
def test_hug_zones(f, n, r):
    assert T.hug_zone(f, n) == pytest.approx(r, abs=0.006)


@pytest.mark.parametrize("n,r", [(1, 0.14), (2, 0.38), (3, 0.68), (4, 1.00), (6, 1.69), (8, 2.41)])
def test_exp_hug_right(n, r):
    assert T.hug_zone("exp", n, side="right") == pytest.approx(r, abs=0.006)


def test_coefficients():
    assert T.coeffs_exact("cos", 4) == (1, 0, sp.Rational(-1, 2), 0, sp.Rational(1, 24))
    assert T.coeffs_exact("sin", 7)[7] == sp.Rational(-1, 5040)
    assert T.coeffs_exact("hill", 6) == (1, 0, -1, 0, 1, 0, -1)
    assert T.derivs_at("cos", 0, 4) == [1, 0, -1, 0, 1]
    assert T.derivs_at("sin", 0, 4) == [0, 1, 0, -1, 0]
    c = T.coeffs("cos", 2, a=1.0)
    assert c[0] == pytest.approx(math.cos(1)) and c[1] == pytest.approx(-math.sin(1))


def test_one_minus_cos():
    assert round(1 - math.cos(1.5), 3) == 0.929


def test_e_partial_sums():
    s = T.e_sums(10)
    assert [round(v, 4) for v in s[:6]] == [1, 2, 2.5, 2.6667, 2.7083, 2.7167]
    assert round(math.e - s[5], 4) == 0.0016
    assert T.correct_decimals(s[9], math.e) == 6  # ten terms, through 1/9!
    assert T.correct_decimals(s[10], math.e) == 7  # through 1/10!: label it n = 10
    assert math.factorial(10) == 3_628_800


def test_sin_half():
    c = T.coeffs("sin", 5)
    t = T.terms(c, 0.5)
    assert round(-t[3], 7) == 0.0208333
    assert round(t[1] + t[3], 7) == 0.4791667
    assert round(t[5], 8) == 0.00026042
    total = T.evaluate(c, 0.5)
    assert round(float(total), 8) == 0.47942708
    assert round(math.sin(0.5), 8) == 0.47942554
    assert abs(total - math.sin(0.5)) == pytest.approx(1.5e-6, abs=1e-7)
    assert T.correct_decimals(float(total), math.sin(0.5)) == 5


def test_horner_program():
    prog = T.ops(T.coeffs("sin", 5), 0.5)
    assert "".join(p["op"] for p in prog) == "××+×+×"
    assert prog[-1]["value"] == pytest.approx(0.47942708, abs=1e-8)


def test_valley():
    assert round(float(T.evaluate(T.coeffs("sin", 3), math.pi / 2)), 3) == 0.925
    assert round(float(T.evaluate(T.coeffs("sin", 5), -math.pi / 2)), 4) == -1.0045


def test_hill():
    s = T.partial_sums(T.coeffs("hill", 10), 0.5)[::2]
    assert [round(v, 5) for v in s] == [1, 0.75, 0.8125, 0.79688, 0.80078, 0.7998]
    assert list(T.partial_sums(T.coeffs("hill", 6), 1.0)[::2]) == [1, 0, 1, 0]
    assert sorted(T.hill_poles(), key=lambda z: z.imag) == [-1j, 1j]
    assert abs(T.hill_poles()[0]) == 1


def test_relativity():
    assert round(T.ke_ratio(0.1), 4) == 1.0076
    assert sp.expand(T.gamma_series(4) - (1 + T.B**2 / 2 + sp.Rational(3, 8) * T.B**4)) == 0


def test_blend_and_evaluate():
    a, b = T.coeffs("cos", 2), T.coeffs("cos", 4)
    assert np.allclose(T.blend(a, b, 1.0), b)
    assert np.allclose(T.evaluate(b, [0.0, 1.0]), [1, 1 - 0.5 + 1 / 24])
