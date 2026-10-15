"""Independent analytical identities and numerical limits for the pure kernel."""

import math
import pickle
import random
from copy import copy, deepcopy
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import pairwise

import pytest

import faceless_champ.spring as spring_module
from faceless_champ.spring import Spring

REGIMES = [0.02, 0.2, 0.6, math.nextafter(1, 0), 1, math.nextafter(1, math.inf), 2, 100]


def reference_ode(zeta, time, terms=100):
    """80-digit ODE power series, independent of the kernel's closed forms.

    Recurrence follows p''+2*zeta*p'+p=1. Tests limit scaled time to .02,
    except near critical damping where s<=20. Default truncation is far below
    float precision there; optional terms checks the origin-series remainder.
    """
    with localcontext() as context:
        context.prec = 80
        zeta, time = Decimal.from_float(zeta), Decimal.from_float(time)
        previous, current = Decimal(0), Decimal("0.5")
        progress, velocity = current * time**2, 2 * current * time
        for n in range(3, terms + 1):
            coefficient = -(2 * zeta * (n - 1) * current + previous) / (n * (n - 1))
            progress += coefficient * time**n
            velocity += n * coefficient * time ** (n - 1)
            previous, current = current, coefficient
        return progress, velocity


def parameter_corners():
    cases = []
    for stiffness in (1e-6, 1e-3, 1, 1e3, 1e6):
        for mass in (1e-6, 1, 1e6):
            for zeta in REGIMES:
                damping = 2 * zeta * math.sqrt(stiffness * mass)
                derived = damping / (2 * math.sqrt(stiffness * mass))
                if 1e-6 <= damping <= 1e6 and 0.02 <= derived <= 100:
                    cases.append((stiffness, damping, mass))
    return cases


@pytest.mark.parametrize("name", ["stiffness", "damping", "mass"])
@pytest.mark.parametrize("value", [True, False, "180", None, 1 + 0j, [], object()])
def test_parameters_require_real_numbers(name, value):
    with pytest.raises(TypeError, match=name):
        Spring(**{name: value})


@pytest.mark.parametrize("name", ["stiffness", "damping", "mass"])
@pytest.mark.parametrize("value", [0, -1, math.inf, -math.inf, math.nan, 1e-7, 1e7, 10**400])
def test_parameters_reject_nonfinite_and_out_of_domain_values(name, value):
    with pytest.raises(ValueError, match=name):
        Spring(**{name: value})


@pytest.mark.parametrize("damping", [0.039, 201, math.nextafter(0.04, 0), math.nextafter(200, math.inf)])
def test_damping_ratio_limits_are_strict(damping):
    with pytest.raises(ValueError, match="damping ratio"):
        Spring(stiffness=1, damping=damping, mass=1)


def test_valid_real_parameters_defaults_and_immutable_derived_values():
    default = Spring()
    assert (default.stiffness, default.damping, default.mass) == (180, 23, 1)
    assert default._angular_frequency == math.sqrt(180)
    assert default._damping_ratio == 23 / (2 * math.sqrt(180))
    rational = Spring(Fraction(9), Fraction(3), Fraction(1))
    assert rational == Spring(9, 3, 1)
    assert hash(rational) == hash(Spring(9, 3, 1))
    assert repr(rational) == "Spring(stiffness=9.0, damping=3.0, mass=1.0)"
    for name in ("stiffness", "damping", "mass", "_horizon", "_progress_bounds"):
        with pytest.raises(FrozenInstanceError):
            setattr(default, name, 10)
    with pytest.raises(FrozenInstanceError):
        del default.mass
    assert not hasattr(default, "__dict__")
    assert replace(default, damping=12) == Spring(damping=12)


@pytest.mark.parametrize("value", [True, False, "0.5", None, 1 + 0j, [], object()])
def test_progress_rejects_nonreal_values(value):
    with pytest.raises(TypeError, match="progress"):
        Spring()(value)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, 10**400])
def test_progress_rejects_nonfinite_values_before_endpoint_checks(value):
    with pytest.raises(ValueError, match="progress"):
        Spring()(value)


@pytest.mark.parametrize("zeta", REGIMES)
def test_exact_endpoints_and_finite_out_of_range_progress(zeta):
    spring = Spring(1, 2 * zeta, 1)
    for value in (-1e300, -1, -0.0, 0, Fraction(0)):
        assert spring(value) == 0.0
    for value in (1, Fraction(1), 2, 1e300):
        assert spring(value) == 1.0
    assert spring(Fraction(1, 2)) == spring(0.5)


@pytest.mark.parametrize("time", [1e-25, 0.01, 0.5, 1, 3, 10])
def test_critical_response_matches_independent_exact_solution(time):
    spring = Spring(1, 2, 1)
    with localcontext() as context:
        context.prec = 80
        s = Decimal.from_float(time)
        decay = (-s).exp()
        expected = float(1 - (1 + s) * decay)
        expected_velocity = float(s * decay)
    progress, velocity = spring._sample(time)
    assert progress == pytest.approx(expected, rel=3e-14, abs=0)
    assert velocity == pytest.approx(expected_velocity, rel=3e-15, abs=0)
    assert spring(time / spring._horizon) == pytest.approx(expected, rel=3e-14, abs=0)


@pytest.mark.parametrize("time", [0.0001, 0.01, 0.5, 1, 3, 10])
def test_overdamped_response_matches_independent_real_roots(time):
    # zeta=1.25 gives exact distinct roots -0.5 and -2, coefficients 4/3,-1/3.
    spring = Spring(1, 2.5, 1)
    with localcontext() as context:
        context.prec = 80
        s = Decimal.from_float(time)
        slow, fast = (-s / 2).exp(), (-2 * s).exp()
        expected = float(1 - (4 * slow - fast) / 3)
        expected_velocity = float(2 * (slow - fast) / 3)
    progress, velocity = spring._sample(time)
    assert progress == pytest.approx(expected, rel=4e-14, abs=0)
    assert velocity == pytest.approx(expected_velocity, rel=4e-15, abs=0)


def test_underdamped_extrema_and_zero_crossings_match_analytical_identities():
    spring = Spring(1, 1.2, 1)  # zeta=.6, damped frequency=.8.
    for n in range(1, 7):
        time = n * math.pi / 0.8
        expected = 1 - (-1) ** n * math.exp(-0.6 * time)
        assert spring(time / spring._horizon) == pytest.approx(expected, rel=2e-15, abs=0)
        assert abs(spring._sample(time)[1]) < 2e-16
    first_peak = math.pi / 0.8
    peak = spring(first_peak / spring._horizon)
    assert peak > 1.09
    assert spring((first_peak - 0.1) / spring._horizon) < peak
    assert spring((first_peak + 0.1) / spring._horizon) < peak
    for n in range(5):
        crossing = (math.pi - math.atan(0.8 / 0.6) + n * math.pi) / 0.8
        assert spring(crossing / spring._horizon) == pytest.approx(1, abs=3e-16)


@pytest.mark.parametrize("zeta", [1, math.nextafter(1, math.inf), 1.000001, 2, 10, 100])
def test_nonoscillatory_responses_are_monotone_and_bounded(zeta):
    spring = Spring(1, 2 * zeta, 1)
    samples = [spring(i / 2000) for i in range(2001)]
    assert all(0 <= value <= 1 for value in samples)
    assert all(left <= right for left, right in pairwise(samples))


@pytest.mark.parametrize("zeta", REGIMES)
@pytest.mark.parametrize("scaled_time", [1e-150, 1e-25, 1e-10, 0.009999, 0.01, 0.010001, 0.02])
def test_small_starts_and_series_join_against_high_precision_ode(zeta, scaled_time):
    spring = Spring(1, 2 * zeta, 1)
    time = scaled_time / max(1, zeta)
    expected, expected_velocity = map(float, reference_ode(zeta, time))
    progress, velocity = spring._sample(time)
    assert progress > 0
    assert progress == pytest.approx(expected, rel=6e-14, abs=0)
    assert velocity == pytest.approx(expected_velocity, rel=3e-15, abs=0)
    assert spring(time / spring._horizon) == pytest.approx(expected, rel=6e-14, abs=0)


@pytest.mark.parametrize("zeta", [math.nextafter(1, 0), 1 - 1e-12, 1 + 1e-12, math.nextafter(1, math.inf)])
def test_near_critical_curves_converge_without_unstable_root_division(zeta):
    spring, critical = Spring(1, 2 * zeta, 1), Spring(1, 2, 1)
    for time in (1e-12, 0.01, 0.1, 1, 5, 20):
        p, velocity = spring._sample(time)
        expected, expected_velocity = critical._sample(time)
        assert p == pytest.approx(expected, rel=2e-11, abs=1e-25)
        assert velocity == pytest.approx(expected_velocity, rel=2e-10, abs=1e-25)
        reference_p, reference_velocity = map(float, reference_ode(zeta, time))
        assert p == pytest.approx(reference_p, rel=3e-14, abs=0)
        assert velocity == pytest.approx(reference_velocity, rel=5e-15, abs=0)
    for u in (0.01, 0.1, 0.2, 0.7, 0.999):
        assert spring(u) == pytest.approx(critical(u), rel=3e-11)


@pytest.mark.parametrize("settings", parameter_corners())
def test_domain_corners_are_finite_settled_and_within_analytical_progress_bounds(settings):
    spring = Spring(*settings)
    assert 0 < spring._horizon <= 1e5
    assert spring._angular_frequency > 0 and math.isfinite(spring._angular_frequency)
    mu, horizon = spring._decay_rate, spring._horizon
    assert horizon >= 2 / mu
    if spring._damping_ratio <= 1:
        assert (1 + mu * horizon) * math.exp(-mu * horizon) <= 1e-9
        assert horizon**2 * math.exp(-mu * horizon) <= 1e-7
    else:
        # Independent distinct-root solution certifies the tighter monotone tail.
        with localcontext() as context:
            context.prec = 80
            zeta, s = Decimal.from_float(spring._damping_ratio), Decimal.from_float(horizon)
            discriminant = (zeta * zeta - 1).sqrt()
            a, b = zeta + discriminant, zeta - discriminant
            slow, fast = (-b * s).exp(), (-a * s).exp()
            assert abs((a * slow - b * fast) / (a - b)) <= Decimal("1e-9")
            assert abs(s * (slow - fast) / (a - b)) <= Decimal("1e-7")
    lower, upper = spring._progress_bounds
    for u in [i / 250 for i in range(251)] + [math.nextafter(0, 1), 1e-150, math.nextafter(1, 0)]:
        value = spring(u)
        assert math.isfinite(value)
        assert lower <= value <= upper
    for time in (horizon, 1.01 * horizon, 2 * horizon, 100 * horizon):
        p, velocity = spring._sample(time)
        assert abs(1 - p) <= 1e-9
        assert abs(horizon * velocity) <= 1e-7


@pytest.mark.parametrize("zeta", REGIMES)
def test_terminal_limit_is_settled_without_relying_on_exact_endpoint_return(zeta):
    spring = Spring(1, 2 * zeta, 1)
    before = math.nextafter(1, 0)
    progress, velocity = spring._sample(before * spring._horizon)
    assert abs(1 - progress) <= 1e-9
    assert abs(spring._horizon * velocity) <= 1e-7
    assert spring(before) == progress
    assert spring(1) == 1


@pytest.mark.parametrize("zeta", [0.02, 0.2, 0.6, 1, 2, 100])
def test_retiming_cancels_reference_frequency_for_equal_damping_ratio(zeta):
    original = Spring(1, 2 * zeta, 1)
    faster = Spring(100, 20 * zeta, 1)
    heavier = Spring(4, 8 * zeta, 4)
    assert faster._angular_frequency == 10 * original._angular_frequency
    for i in range(101):
        assert faster(i / 100) == pytest.approx(original(i / 100), abs=2e-15)
        assert heavier(i / 100) == pytest.approx(original(i / 100), abs=2e-15)


def test_arbitrary_order_repeatability_and_immutable_copies():
    spring = Spring(1, 0.4, 1)
    times = [i / 500 for i in range(501)]
    expected = {time: spring(time) for time in times}
    before = pickle.dumps(spring)
    random.Random(542).shuffle(times)
    for clone in (spring, copy(spring), deepcopy(spring), pickle.loads(before)):
        assert clone == spring
        assert all(clone(time) == expected[time] for time in times + times[::-1])
    assert pickle.dumps(spring) == before


def test_horizon_is_constructed_once_and_failure_is_bounded(monkeypatch):
    original = spring_module._settling_horizon
    calls = []

    def record(decay, root_gap):
        calls.append((decay, root_gap))
        return original(decay, root_gap)

    monkeypatch.setattr(spring_module, "_settling_horizon", record)
    spring = Spring()
    for i in range(100):
        spring(i / 100)
    assert len(calls) == 1
    monkeypatch.setattr(spring_module, "_MAX_HORIZON", 1)
    with pytest.raises(ValueError, match="settling horizon"):
        Spring()


@pytest.mark.parametrize("angle", [0, 1e-12, 1e-6, math.nextafter(1e-4, 0), 1e-4, math.nextafter(1e-4, math.inf)])
def test_sinc_regularization_and_series_error(angle):
    with localcontext() as context:
        context.prec = 80
        x = Decimal.from_float(angle)
        # Independent sin(x)/x series through x^12; next term <= 1e-65 here.
        expected = 1 + sum((-1) ** n * x ** (2 * n) / math.factorial(2 * n + 1) for n in range(1, 7))
        polynomial = 1 - x * x / 6 + x**4 / 120
        assert abs(polynomial - expected) <= Decimal("2e-28")
    assert spring_module._sinc(angle) == pytest.approx(float(expected), rel=2e-16, abs=0)


@pytest.mark.parametrize("value", [0, 1e-150, 1e-12, 1e-4, 0.1, 1, 1000])
def test_exponential_average_regular_limit_and_large_argument(value):
    with localcontext() as context:
        context.prec = 200
        x = Decimal.from_float(value)
        expected = (1 - (-x).exp()) / x if x else Decimal(1)
    assert spring_module._exponential_average(value) == pytest.approx(float(expected), rel=3e-16, abs=0)


@pytest.mark.parametrize("zeta", REGIMES)
def test_origin_series_truncation_is_below_float_precision(zeta):
    time = 0.01 / max(1, zeta)
    expected_p, expected_v = reference_ode(zeta, time)
    polynomial_p, polynomial_v = reference_ode(zeta, time, terms=8)
    with localcontext() as context:
        context.prec = 80
        s = Decimal.from_float(time)
        assert abs(polynomial_p - expected_p) <= Decimal("2e-17") * s * s
        assert abs(polynomial_v - expected_v) <= Decimal("2e-16") * s
    p, v = Spring(1, 2 * zeta, 1)._sample(time)
    assert abs(p - float(expected_p)) <= 3 * math.ulp(float(expected_p))
    assert abs(v - float(expected_v)) <= 3 * math.ulp(float(expected_v))


def test_logarithmic_domain_sweep_includes_analytic_extrema_and_terminal_limits():
    rng = random.Random(6401)
    for _ in range(100):
        zeta = math.exp(math.log(0.02) + rng.random() * math.log(5000))
        spring = Spring(1, 2 * zeta, 1)
        times = [i / 300 for i in range(301)]
        if zeta < 1:
            q = math.sqrt((1 - zeta) * (1 + zeta))
            times.extend(n * math.pi / (q * spring._horizon) for n in range(1, 15) if n * math.pi < q * spring._horizon)
        for u in times:
            value = spring(u)
            assert math.isfinite(value)
            assert spring._progress_bounds[0] <= value <= spring._progress_bounds[1]
        p, v = spring._sample(math.nextafter(1, 0) * spring._horizon)
        assert abs(1 - p) <= 1e-9
        assert abs(spring._horizon * v) <= 1e-7
