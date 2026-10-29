"""Analytical, constant-mass teaching models in SI units.

World and body frames are right handed: X forward, Y left, Z up. The
experiments reset independently. No CFD, Tesla telemetry or flight-controller
identification is claimed. Display-time stretching never changes these states.
"""

from dataclasses import dataclass
from math import cos, pi, sin, sqrt

import numpy as np

MASS = 1700.0
G = 9.81
WEIGHT = MASS * G
SUCTION = 2 * WEIGHT
AREA = 2.0
RADIUS = 12.0
SPEED = 12.0
INERTIA = 800.0
ROLL_TIME = 1.6
ALPHA = 4 * pi / ROLL_TIME**2
TORQUE = INERTIA * ALPHA
SEPARATION = 1.5
VEFF = 600.0
GAS = 250.0
CG_HEIGHT = 0.70


def clamp(value, lower=0.0, upper=1.0):
    return min(upper, max(lower, value))


def progress(time, start, end):
    return clamp((time - start) / (end - start))


def smooth(value):
    value = clamp(value)
    return value * value * (3 - 2 * value)


def incline(angle, suction=0.0, mu=1.0):
    """Demand/capacity for a straight incline; no centripetal force is added."""
    normal = WEIGHT * cos(angle) + suction
    downhill = WEIGHT * sin(angle)
    capacity = mu * max(0.0, normal)
    return {
        "normal": normal,
        "downhill": downhill,
        "capacity": capacity,
        "friction": min(downhill, capacity),
        "sliding": downhill > capacity + 1e-8,
    }


def loop(angle, speed=SPEED, radius=RADIUS, suction=SUCTION):
    """Angle runs from the bottom (0) to the inside-loop apex (pi)."""
    center = np.array((0.0, 0.0, radius + CG_HEIGHT))
    inward = np.array((-sin(angle), 0.0, cos(angle)))
    position = center - radius * inward
    tangent = np.array((cos(angle), 0.0, sin(angle)))
    normal = suction + MASS * speed**2 / radius + WEIGHT * cos(angle)
    return {
        "position": position,
        "rotation": np.array((0.0, -angle * 180 / pi, 0.0)),
        "inward": inward,
        "tangent": tangent,
        "normal": normal,
        "suction": suction,
        "friction": WEIGHT * sin(angle),
        "centripetal": speed**2 / radius,
        "velocity": tangent * speed,
    }


def roll(time, duration=ROLL_TIME):
    """Incremental half-roll, beginning inverted, ending upright and at rest."""
    t = clamp(time, 0, duration)
    alpha = 4 * pi / duration**2
    if t < duration / 2:
        theta, omega, acceleration = 0.5 * alpha * t * t, alpha * t, alpha
    elif t < duration:
        remaining = duration - t
        theta, omega, acceleration = pi - 0.5 * alpha * remaining**2, alpha * remaining, -alpha
    else:
        theta, omega, acceleration = pi, 0.0, 0.0
    return {
        "theta": theta,
        "omega": omega,
        "alpha": acceleration,
        "torque": INERTIA * acceleration,
        "force": INERTIA * abs(acceleration) / SEPARATION,
    }


def landing(time, height=20.0, assisted=True):
    """Height is clearance above the center-of-mass height at wheel contact.

    A 2mg brake starts after half the drop. An uncontrolled impact is modeled as
    an inelastic stop; its incoming speed is retained separately for annotation.
    """
    t = max(0.0, time)
    switch = sqrt(height / G)
    if not assisted:
        end = sqrt(2 * height / G)
        q = min(t, end)
        return {
            "height": max(0.0, height - 0.5 * G * q * q),
            "velocity": -G * q if t < end else 0.0,
            "impact_velocity": -G * end,
            "acceleration": -G if t < end else 0.0,
            "thrust": 0.0,
            "contact": t >= end,
            "impact": t >= end,
            "end": end,
            "switch": switch,
        }
    end = 2 * switch
    if t < switch:
        h, v, a, thrust = height - 0.5 * G * t * t, -G * t, -G, 0.0
    elif t < end:
        q = t - switch
        h = height / 2 - G * switch * q + 0.5 * G * q * q
        v, a, thrust = -G * switch + G * q, G, 2 * WEIGHT
    else:
        h, v, a, thrust = 0.0, 0.0, 0.0, 0.0
    return {
        "height": max(0.0, h),
        "velocity": v,
        "acceleration": a,
        "thrust": thrust,
        "contact": t >= end,
        "impact": False,
        "end": end,
        "switch": switch,
    }


def hover_demo(time):
    """A moving fall with T=mg, followed by T=2mg; no frozen-velocity illusion."""
    t = clamp(time, 0, 1.0)
    q = max(0, t - 0.6)
    return {
        "height": 20 - 14 * t + 0.5 * G * q * q,
        "velocity": -14 + G * q,
        "acceleration": G if t > 0.6 else 0.0,
        "thrust": 2 * WEIGHT if t > 0.6 else WEIGHT,
    }


@dataclass(frozen=True)
class ReplayState:
    position: tuple
    rotation: tuple
    velocity: tuple
    phase: str
    normal: float
    suction: float
    thrust: float
    roll_time: float


APPROACH_TIME = 3.0
ARC_TIME = pi * RADIUS / SPEED
RELEASE_TIME = APPROACH_TIME + ARC_TIME
FLIGHT_TIME = 2 * sqrt(2 * RADIUS / G)
REPLAY_TIME = RELEASE_TIME + FLIGHT_TIME


def replay(time):
    """One force-consistent nominal reconstruction, not the recorded trajectory."""
    t = clamp(time, 0, REPLAY_TIME)
    if t < APPROACH_TIME:
        return ReplayState(
            (-18 + 2 * t * t, 0, CG_HEIGHT), (0, 0, 0), (4 * t, 0, 0), "APPROACH", SUCTION + WEIGHT, SUCTION, 0, 0
        )
    if t < RELEASE_TIME:
        angle = (t - APPROACH_TIME) * SPEED / RADIUS
        state = loop(angle)
        return ReplayState(
            tuple(state["position"]),
            tuple(state["rotation"]),
            tuple(state["velocity"]),
            "CONTACT",
            state["normal"],
            SUCTION,
            0,
            0,
        )
    flight = t - RELEASE_TIME
    descent = landing(flight, height=2 * RADIUS)
    turn = roll(flight)
    # Ry(-pi) Rx(phi): the same longitudinal roll axis in an inverted body.
    return ReplayState(
        (-SPEED * flight, 0, CG_HEIGHT + descent["height"]),
        (turn["theta"] * 180 / pi, -180, 0),
        (-SPEED, 0, descent["velocity"]),
        "BRAKING" if descent["thrust"] else ("LANDED" if descent["contact"] else "FLIGHT"),
        WEIGHT if descent["contact"] else 0,
        0,
        descent["thrust"],
        min(flight, ROLL_TIME),
    )


def rotation_matrix(rotation):
    x, y, z = np.radians(rotation)
    rx = np.array(((1, 0, 0), (0, cos(x), -sin(x)), (0, sin(x), cos(x))))
    ry = np.array(((cos(y), 0, sin(y)), (0, 1, 0), (-sin(y), 0, cos(y))))
    rz = np.array(((cos(z), -sin(z), 0), (sin(z), cos(z), 0), (0, 0, 1)))
    return rz @ ry @ rx


def checkpoints():
    return {
        "weight_N": WEIGHT,
        "suction_N": SUCTION,
        "pressure_kPa": SUCTION / AREA / 1000,
        "radial_N": MASS * SPEED * SPEED / RADIUS,
        "apex_normal_N": loop(pi)["normal"],
        "mass_flow_kg_s": 20000 / VEFF,
        "alpha_rad_s2": ALPHA,
        "torque_Nm": TORQUE,
        "couple_each_N": TORQUE / SEPARATION,
        "freefall_speed_m_s": sqrt(2 * G * 20),
        "braking_speed_m_s": sqrt(2 * G * 10),
        "landing_time_s": 2 * sqrt(20 / G),
    }
