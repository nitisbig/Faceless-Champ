"""Mathematical model of a non-rotating (Schwarzschild) black hole.

Geometric units throughout: G = c = M = 1, so the Schwarzschild radius is rs = 2.

Light
    A photon in the equatorial plane of its own orbit obeys the Binet equation

        d²u/dφ² + u = 3 M u²,        u = 1/r.

    The same orbit is produced by the flat-space Cartesian ODE

        d²x/dλ² = -3 M h² x / r⁵,    h = |x × dx/dλ| (conserved),

    because a central force f(r) gives u'' + u = f / (h² u²), and f = 3 M h² u⁵
    returns exactly 3 M u². The GPU engine integrates this form per pixel; this
    module integrates it on the CPU for diagrams and to check the shader.

Matter
    Thin Keplerian disk from the innermost stable circular orbit (r = 6M).
    Orbital angular velocity Ω = sqrt(M / r³); emitter 4-velocity u^t = 1/sqrt(1 - 3M/r).
    Zero-torque Shakura–Sunyaev temperature T⁴ ∝ r⁻³ (1 - sqrt(r_isco / r)).

Observed light
    Frequency ratio g = ν_obs / ν_emit = sqrt(1 - 3M/r) / (1 - Ω λ), where
    λ = L_z / E is the photon's conserved angular momentum about the disk axis.
    I_ν / ν³ is invariant, so a blackbody at T is seen as a blackbody at g·T and
    its bolometric intensity scales as g⁴.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

M = 1.0
RS = 2.0 * M  # event horizon
R_PHOTON = 3.0 * M  # unstable circular photon orbit
R_ISCO = 6.0 * M  # innermost stable circular orbit
B_CRIT = 3.0 * math.sqrt(3.0) * M  # critical impact parameter (shadow radius)


# --------------------------------------------------------------------------- metric


def clock_rate(r: float) -> float:
    """dτ/dt of a static observer at radius r."""
    return math.sqrt(max(0.0, 1.0 - RS / r))


def orbital_omega(r: float) -> float:
    """Keplerian angular velocity dφ/dt seen from infinity."""
    return math.sqrt(M / r**3)


def orbital_ut(r: float) -> float:
    """u^t for a circular geodesic (diverges at the photon sphere)."""
    return 1.0 / math.sqrt(1.0 - 3.0 * M / r)


def orbital_speed(r: float) -> float:
    """Orbital speed measured by a local static observer, as a fraction of c."""
    return math.sqrt(M / (r - RS))


def shadow_angular_radius(r_obs: float) -> float:
    """Angular radius (rad) of the shadow seen by a static observer at r_obs."""
    return math.asin(min(1.0, B_CRIT / r_obs * math.sqrt(1.0 - RS / r_obs)))


def redshift(r: float, lam: float) -> float:
    """g = ν_obs/ν_emit for disk emission at r reaching infinity with λ = L/E."""
    return math.sqrt(1.0 - 3.0 * M / r) / (1.0 - orbital_omega(r) * lam)


# --------------------------------------------------------------------------- disk


def disk_temperature(r: np.ndarray | float) -> np.ndarray | float:
    """Relative Shakura–Sunyaev temperature, normalized to 1 at its peak."""
    r = np.asarray(r, dtype=float)
    t4 = np.where(r > R_ISCO, r**-3.0 * (1.0 - np.sqrt(R_ISCO / np.maximum(r, R_ISCO))), 0.0)
    return (t4 / _T4_PEAK) ** 0.25


R_TPEAK = 49.0 / 36.0 * R_ISCO  # d/dr[r⁻³(1 - sqrt(6/r))] = 0
_T4_PEAK = R_TPEAK**-3.0 * (1.0 - math.sqrt(R_ISCO / R_TPEAK))


# --------------------------------------------------------------------------- geodesics


@dataclass(frozen=True)
class Ray:
    points: np.ndarray  # (n, 2) positions in units of M
    captured: bool


def trace_planar_ray(b: float, start_x: float = -30.0, max_r: float = 40.0, steps: int = 6000) -> Ray:
    """Integrate a photon arriving from -x with impact parameter b (velocity-Verlet, adaptive step)."""
    x = np.array([start_x, b], dtype=float)
    v = np.array([1.0, 0.0])
    h2 = (x[0] * v[1] - x[1] * v[0]) ** 2
    out = [x.copy()]
    for _ in range(steps):
        r = math.hypot(*x)
        if r <= RS * 1.001:
            return Ray(np.array(out), True)
        if r > max_r and x @ v > 0:
            break
        dl = min(0.5, 0.02 * (r - RS) + 0.004)
        a = -3.0 * M * h2 * x / r**5
        v_half = v + 0.5 * dl * a
        x = x + dl * v_half
        r = math.hypot(*x)
        v = v_half + 0.5 * dl * (-3.0 * M * h2 * x / r**5)
        out.append(x.copy())
    return Ray(np.array(out), False)


def deflection_angle(b: float) -> float:
    """Total bending angle (rad) of an escaping photon; the weak-field limit is 4M/b."""
    ray = trace_planar_ray(b, start_x=-400.0, max_r=400.0, steps=60000)
    if ray.captured:
        return math.inf
    d = ray.points[-1] - ray.points[-2]
    return math.atan2(-d[1], d[0])


# --------------------------------------------------------------------------- color


def _cie_xyz(wl_nm: np.ndarray) -> np.ndarray:
    """CIE 1931 2° colour matching functions, multi-lobe fit (Wyman, Sloan & Shirley 2013)."""

    def g(x, mu, s1, s2):
        return np.exp(-0.5 * ((x - mu) / np.where(x < mu, s1, s2)) ** 2)

    x = 1.056 * g(wl_nm, 599.8, 37.9, 31.0) + 0.362 * g(wl_nm, 442.0, 16.0, 26.7) - 0.065 * g(wl_nm, 501.1, 20.4, 26.2)
    y = 0.821 * g(wl_nm, 568.8, 46.9, 40.5) + 0.286 * g(wl_nm, 530.9, 16.3, 31.1)
    z = 1.217 * g(wl_nm, 437.0, 11.8, 36.0) + 0.681 * g(wl_nm, 459.0, 26.0, 13.8)
    return np.stack([x, y, z], axis=-1)


XYZ_TO_LINEAR_SRGB = np.array(
    [[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.2040, 1.0570]],
)

LUT_T_MIN, LUT_T_MAX = 1000.0, 40000.0


def blackbody_lut(size: int = 256) -> np.ndarray:
    """Linear-sRGB chromaticity of a blackbody, log-spaced in temperature, luminance Y = 1.

    Index i covers T = T_MIN · (T_MAX/T_MIN)^(i/(size-1)). Out-of-gamut negatives are
    clipped; brightness is applied separately from the flux model.
    """
    wl = np.linspace(380.0, 780.0, 401)
    cmf = _cie_xyz(wl)
    temps = LUT_T_MIN * (LUT_T_MAX / LUT_T_MIN) ** np.linspace(0, 1, size)
    lam = wl * 1e-9
    c2 = 1.4387769e-2
    planck = 1.0 / (lam[None, :] ** 5 * np.expm1(c2 / (lam[None, :] * temps[:, None])))
    xyz = planck @ cmf
    xyz /= xyz[:, 1:2]
    rgb = np.clip(xyz @ XYZ_TO_LINEAR_SRGB.T, 0.0, None)
    return rgb.astype("f4")


if __name__ == "__main__":
    # Sanity checks of the model against closed-form results.
    print(f"shadow radius b_c = {B_CRIT:.4f} M")
    for b in (B_CRIT - 0.01, B_CRIT + 0.01):
        print(f"b = {b:.3f}: captured = {trace_planar_ray(b, steps=20000).captured}")
    for b in (20.0, 50.0):
        print(f"b = {b}: deflection {deflection_angle(b):.4f} rad, weak field 4M/b = {4 / b:.4f}")
    print(f"ISCO orbital speed {orbital_speed(R_ISCO):.3f} c, peak T at r = {R_TPEAK:.2f} M")
