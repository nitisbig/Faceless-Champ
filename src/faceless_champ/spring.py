"""Analytical, finite-duration spring easing, independent of the timeline.

Scene.play validates recognized spring tracks for position, rotation and safe
scales. Bounded properties use independent conventional easing tracks. A private
time-reversal adapter preserves certified bounds through finite schedules; the
kernel itself has no timeline or renderer dependencies.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from numbers import Real

__all__ = ["Spring"]

_MIN_PARAMETER = 1e-6
_MAX_PARAMETER = 1e6
_MIN_DAMPING_RATIO = 0.02
_MAX_DAMPING_RATIO = 100.0
_MAX_HORIZON = 1e5
_SEARCH_STEPS = 64
_DISPLACEMENT_TOLERANCE = 1e-9
_VELOCITY_TOLERANCE = 1e-7


def _real(value: Real, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number (not a boolean)")
    try:
        result = float(value)
    except OverflowError:
        raise ValueError(f"{name} must be finite") from None
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _settling_horizon(decay_rate: float, root_gap: float) -> float:
    """Certify analytical tail envelopes, never integrate or sample frame times."""

    def settled(time: float) -> bool:
        decay = math.exp(-decay_rate * time)
        # For overdamping, this is the exact positive monotone tail. The loose
        # E<=1 bound would needlessly change the retiming by O(sqrt(zeta-1))
        # near critical damping. Other regimes retain the conservative envelope.
        average = _exponential_average(root_gap * time)
        displacement = (1 + decay_rate * time * average) * decay
        velocity = time * time * decay * average
        # Reserve half the public tolerances for evaluation and endpoint rounding.
        return displacement <= _DISPLACEMENT_TOLERANCE / 2 and velocity <= _VELOCITY_TOLERANCE / 2

    lower = 2 / decay_rate  # Both envelope criteria decrease beyond this point.
    upper = min(lower, _MAX_HORIZON)
    for _ in range(_SEARCH_STEPS):
        if upper >= lower and settled(upper):
            break
        if upper >= _MAX_HORIZON:
            raise ValueError("Spring cannot certify a settling horizon within the supported limit")
        lower, upper = upper, min(2 * upper, _MAX_HORIZON)
    else:
        raise ValueError("Spring settling horizon search exceeded its supported limit")

    for _ in range(_SEARCH_STEPS):
        middle = lower + (upper - lower) / 2
        if settled(middle):
            upper = middle
        else:
            lower = middle
    return upper


def _sinc(value: float) -> float:
    """sin(x)/x with a regular limit; omitted term below 1e-4 is < 2e-28."""
    if abs(value) < 1e-4:
        squared = value * value
        return 1 + squared * (-1 / 6 + squared / 120)
    return math.sin(value) / value


def _exponential_average(value: float) -> float:
    """(1-exp(-x))/x, including the repeated-root limit at zero."""
    return -math.expm1(-value) / value if value else 1.0


@dataclass(frozen=True, slots=True)
class Spring:
    """Zero-initial-velocity spring response retimed to normalized progress.

    ``Spring(stiffness=180, damping=23, mass=1)(u)`` evaluates at arbitrary finite
    real progress. Values at/before zero and at/after one are exactly 0 and 1.
    The interior may overshoot one for underdamped settings. No state advances
    between calls, and evaluation order and frame rate cannot change the curve.

    All parameters must be finite real numbers in [1e-6, 1e6], with derived
    damping ratio ``damping / (2*sqrt(stiffness*mass))`` in [0.02, 100]. Booleans
    and strings are rejected. Parameters and cached coefficients are immutable.

    A conservative settling horizon is computed once. At the left-hand terminal
    limit, displacement error is at most 1e-9 of travel and speed is at most
    1e-7 in normalized-progress units. These are not pixel or seconds units.
    Equal damping ratios give equal normalized shapes within floating-point
    tolerance; the consuming animation's run_time determines on-screen speed.
    This is finite-duration easing, without retargeting or velocity handoff.
    """

    stiffness: float = 180.0
    damping: float = 23.0
    mass: float = 1.0
    _angular_frequency: float = field(init=False, repr=False, compare=False)
    _damping_ratio: float = field(init=False, repr=False, compare=False)
    _decay_rate: float = field(init=False, repr=False, compare=False)
    _oscillation_frequency: float = field(init=False, repr=False, compare=False)
    _root_gap: float = field(init=False, repr=False, compare=False)
    _horizon: float = field(init=False, repr=False, compare=False)
    _progress_bounds: tuple[float, float] = field(init=False, repr=False, compare=False)
    _origin_coefficients: tuple[float, ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        for name in ("stiffness", "damping", "mass"):
            value = _real(getattr(self, name), name)
            if not _MIN_PARAMETER <= value <= _MAX_PARAMETER:
                raise ValueError(f"{name} must be in [{_MIN_PARAMETER:g}, {_MAX_PARAMETER:g}]")
            object.__setattr__(self, name, value)

        omega = math.sqrt(self.stiffness / self.mass)
        zeta = self.damping / (2 * math.sqrt(self.stiffness * self.mass))
        if not _MIN_DAMPING_RATIO <= zeta <= _MAX_DAMPING_RATIO:
            raise ValueError(f"Spring damping ratio must be in [{_MIN_DAMPING_RATIO:g}, {_MAX_DAMPING_RATIO:g}]")
        frequency = math.sqrt((1 - zeta) * (1 + zeta)) if zeta < 1 else 0.0
        root = math.sqrt((zeta - 1) * (zeta + 1)) if zeta > 1 else 0.0
        decay_rate = 1 / (zeta + root) if zeta > 1 else zeta
        # A reciprocal computes the slow overdamped root without cancellation.
        # Twice the discriminant root avoids subtracting nearly equal roots.
        bounds = (0.0, 1.0)
        if zeta < 1:
            peak = 1 + math.exp(-math.pi * zeta / frequency)
            bounds = (0.0, math.nextafter(peak, math.inf))

        object.__setattr__(self, "_angular_frequency", omega)
        object.__setattr__(self, "_damping_ratio", zeta)
        object.__setattr__(self, "_decay_rate", decay_rate)
        object.__setattr__(self, "_oscillation_frequency", frequency)
        object.__setattr__(self, "_root_gap", 2 * root)
        object.__setattr__(self, "_horizon", _settling_horizon(decay_rate, 2 * root))
        object.__setattr__(self, "_progress_bounds", bounds)
        object.__setattr__(
            self,
            "_origin_coefficients",
            (
                1 / 2,
                -zeta / 3,
                (4 * zeta**2 - 1) / 24,
                zeta * (1 - 2 * zeta**2) / 30,
                (16 * zeta**4 - 12 * zeta**2 + 1) / 720,
                zeta * (-32 * zeta**4 + 32 * zeta**2 - 6) / 5040,
                (64 * zeta**6 - 80 * zeta**4 + 24 * zeta**2 - 1) / 40320,
            ),
        )

    def __call__(self, u: float) -> float:
        u = _real(u, "progress")
        if u <= 0:
            return 0.0
        if u >= 1:
            return 1.0
        return self._sample(self._horizon * u)[0]

    def _sample(self, time: float) -> tuple[float, float]:
        """Return progress and d(progress)/ds at dimensionless reference time s."""
        zeta = self._damping_ratio
        if time * max(1, zeta) <= 0.01:
            # Degree-eight analytical origin limit. The scaled argument is at
            # most .02; truncation is below double-precision rounding. Computing
            # progress directly preserves tiny starts that 1-error would lose.
            progress = velocity = 0.0
            for power in range(8, 1, -1):
                coefficient = self._origin_coefficients[power - 2]
                progress = coefficient + time * progress
                velocity = power * coefficient + time * velocity
            return time * time * progress, time * velocity

        exponent = self._decay_rate * time
        decay = math.exp(-exponent)
        if zeta < 1:
            angle = self._oscillation_frequency * time
            sinc = _sinc(angle)
            # 1-cos(angle) = 2*sin(angle/2)^2 also preserves small angles.
            progress = -math.expm1(-exponent) + decay * (2 * math.sin(angle / 2) ** 2 - exponent * sinc)
            return progress, decay * time * sinc
        if zeta == 1:
            return -math.expm1(-time) - time * decay, time * decay
        average = _exponential_average(self._root_gap * time)
        return -math.expm1(-exponent) - decay * exponent * average, decay * time * average


@dataclass(frozen=True, slots=True)
class _ReversedSpring:
    """Time reversal, retaining the original kernel and outward progress bounds."""

    spring: Spring
    _progress_bounds: tuple[float, float] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.spring, Spring):
            raise TypeError("Reversed spring requires a Spring")
        lower, upper = _spring_progress_bounds(self.spring)
        object.__setattr__(self, "_progress_bounds", (1 - upper, 1 - lower))

    def __call__(self, u: float) -> float:
        u = _real(u, "progress")
        if u <= 0:
            return 0.0
        if u >= 1:
            return 1.0
        return 1 - self.spring(1 - u)


def _spring_progress_bounds(easing) -> tuple[float, float] | None:
    """Recognize only engine spring callables, with numerical padding once."""
    if isinstance(easing, _ReversedSpring):
        return easing._progress_bounds
    if isinstance(easing, Spring):
        lower, upper = easing._progress_bounds
        if easing._damping_ratio < 1:
            upper += 32 * math.ulp(upper)
        return lower, upper
    return None
