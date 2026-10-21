"""Analytic mechanics and vector fields, driven by one absolute scene clock."""

import numpy as np
from manim import (
    Arrow,
    Circle,
    Dot,
    Line,
    ManimColor,
    RoundedRectangle,
    Scene,
    ValueTracker,
    VGroup,
    VMobject,
    config,
    interpolate_color,
    linear,
)

DURATION = 45.0
CYAN, GOLD, PINK = map(ManimColor, ("#55DDEB", "#FFD166", "#F783AC"))
MUTED = "#334759"
OMEGA = 1.25


def point(x, y):
    return np.array([x, y, 0.0])


def curve(points, color, width=2):
    return VMobject(color=color, stroke_width=width).set_points_as_corners(points)


def envelope(t, start, end):
    """Short smooth entrances/exits without stretching any physical trajectory."""
    a = np.clip(min((t - start) / 0.8, (end - t) / 0.8), 0, 1)
    return float(a * a * (3 - 2 * a))


def projectile(t):
    return point(-5.2 + 2.6 * t, -2.4 + 3.9 * t - 0.975 * t * t)


def oscillator(t):
    return 1.5 * np.cos(OMEGA * t), -1.5 * OMEGA * np.sin(OMEGA * t)


class PhysicsVectorFields(Scene):
    def construct(self):
        config.background_color = "#000000"
        clock = ValueTracker(0)
        # F(x,y)=(-0.7y,0.7x): exact circular trajectories; speed grows with radius.
        field = VGroup()
        for x in np.arange(-5.5, 5.6, 0.85):
            for y in np.arange(-2.8, 2.9, 0.8):
                p = point(x, y)
                v = point(-0.7 * y, 0.7 * x)
                speed = np.linalg.norm(v)
                if speed < 0.15:
                    continue
                field.add(
                    Arrow(
                        p,
                        p + v / speed * (0.12 + 0.13 * speed),
                        buff=0,
                        color=interpolate_color(CYAN, GOLD, min(speed / 4.4, 1)),
                        stroke_width=2,
                        max_tip_length_to_length_ratio=0.28,
                    )
                )
        rings = VGroup(*[Circle(radius=r, color=MUTED, stroke_width=1) for r in (0.85, 1.5, 2.2, 2.9)])
        particles, trails = VGroup(), VGroup()
        seeds = [(r, angle) for r in (0.85, 1.5, 2.2, 2.9) for angle in (0, 2.1, 4.2)]
        for r, _ in seeds:
            color = interpolate_color(CYAN, GOLD, r / 3)
            particles.add(Dot(radius=0.055, color=color))
            trails.add(VMobject(color=color, stroke_width=3))
        vortex = VGroup(field, rings, trails, particles)

        # Uniform gravity, full ballistic arcs, velocity vectors and vertical components.
        gravity = VGroup(
            *[
                Arrow(point(x, y), point(x, y - 0.38), buff=0, color=MUTED, stroke_width=1.5)
                for x in np.arange(-5.5, 5.6, 1.1)
                for y in np.arange(-1.6, 3, 0.9)
            ]
        )
        ground = Line(point(-5.8, -2.5), point(5.8, -2.5), color=MUTED)
        path = curve([projectile(s) for s in np.linspace(0, 4, 100)], MUTED, 1.5)
        balls, arcs, velocities, verticals = VGroup(), VGroup(), VGroup(), VGroup()
        for color in (GOLD, CYAN, PINK):
            balls.add(Dot(radius=0.09, color=color))
            arcs.add(VMobject(color=color, stroke_width=3))
            velocities.add(Arrow(point(0, 0), point(1, 0), color=color, buff=0))
            verticals.add(Line(point(0, 0), point(0, 1), color=color, stroke_width=2))
        ballistics = VGroup(gravity, ground, path, arcs, verticals, velocities, balls)

        # Left: real-space spring; right: (x,v) phase portrait for x''=-omega²x.
        wall = Line(point(-5.9, -0.9), point(-5.9, 0.9), color=MUTED, stroke_width=4)
        rail = Line(point(-5.9, -0.7), point(-0.7, -0.7), color=MUTED)
        equilibrium = Line(point(-3.2, -1), point(-3.2, 1), color=MUTED, stroke_width=1)
        spring = VMobject(color=CYAN, stroke_width=3)
        mass = RoundedRectangle(width=0.65, height=1, corner_radius=0.12, color=GOLD, fill_opacity=1)
        force = Arrow(point(-3, 1.2), point(-2, 1.2), color=PINK, buff=0)
        phase_center = point(3.3, 0)
        axes = VGroup(
            Line(point(0.8, 0), point(5.8, 0), color=MUTED),
            Line(point(3.3, -2.5), point(3.3, 2.5), color=MUTED),
        )
        phase_field = VGroup()
        for x in np.arange(-1.8, 1.9, 0.6):
            for v in np.arange(-1.8, 1.9, 0.6):
                direction = point(v, -x)
                norm = np.linalg.norm(direction)
                if norm < 0.1:
                    continue
                p = phase_center + point(x, v)
                phase_field.add(Arrow(p, p + direction * 0.18, buff=0, color=CYAN, stroke_width=1.5))
        orbit = Circle(radius=1.95, color=MUTED, stroke_width=1.5).move_to(phase_center)
        phase_trail = VMobject(color=GOLD, stroke_width=3)
        phase_dot = Dot(radius=0.085, color=GOLD)
        harmonic = VGroup(
            wall, rail, equilibrium, spring, mass, force, axes, phase_field, orbit, phase_trail, phase_dot
        )

        fades = [
            (start, end, [(mob, mob.get_fill_opacity(), mob.get_stroke_opacity()) for mob in group.get_family()])
            for group, start, end in ((vortex, 0, 15), (ballistics, 14.2, 29.5), (harmonic, 28.7, 45.8))
        ]

        def update(_):
            t = clock.get_value()
            if t <= 15:
                for index, (r, angle) in enumerate(seeds):
                    theta = angle + 0.7 * t
                    particles[index].move_to(point(r * np.cos(theta), r * np.sin(theta)))
                    samples = np.linspace(max(0, t - 1.1), max(t, 0.001), 32)
                    trails[index].set_points_as_corners(
                        [point(r * np.cos(angle + 0.7 * s), r * np.sin(angle + 0.7 * s)) for s in samples]
                    )
            if 14.2 <= t <= 29.5:
                for i in range(3):
                    s = ((t - 14.2) * 0.65 + i * 1.33) % 4
                    p = projectile(s)
                    balls[i].move_to(p)
                    arcs[i].set_points_as_corners([projectile(u) for u in np.linspace(0, max(s, 0.001), 70)])
                    velocity = point(2.6, 3.9 - 1.95 * s)
                    velocities[i].put_start_and_end_on(p, p + velocity * 0.23)
                    # Keep a nonzero line at the apex; it is visually negligible there.
                    dy = 0.23 * velocity[1]
                    verticals[i].put_start_and_end_on(p, p + point(0, dy if abs(dy) > 1e-5 else 1e-5))
            if t >= 28.7:
                s = t - 28.7
                x, v = oscillator(s)
                center = point(-3.2 + x, 0)
                mass.move_to(center)
                end = center[0] - 0.325
                xs = np.linspace(-5.9, end, 65)
                ys = 0.23 * np.sin(np.linspace(0, 16 * np.pi, 65))
                spring.set_points_as_corners([point(a, b) for a, b in zip(xs, ys)])
                fx = -0.65 * x
                force.put_start_and_end_on(center + point(0, 1), center + point(fx if abs(fx) > 1e-5 else 1e-5, 1))
                phase_dot.move_to(phase_center + point(1.3 * x, 1.3 * v / OMEGA))
                samples = np.linspace(max(0, s - 4), max(s, 0.001), 110)
                phase_trail.set_points_as_corners(
                    [phase_center + point(1.95 * np.cos(OMEGA * u), -1.95 * np.sin(OMEGA * u)) for u in samples]
                )
            for start, end, styles in fades:
                alpha = envelope(t, start, end)
                for mob, fill, stroke in styles:
                    mob.set_fill(opacity=fill * alpha, family=False)
                    mob.set_stroke(opacity=stroke * alpha, family=False)

        graphics = VGroup(vortex, ballistics, harmonic)
        self.add(graphics, clock)
        update(graphics)
        # A mobject updater makes Cairo classify the geometry as moving.
        graphics.add_updater(update)
        self.play(clock.animate.set_value(DURATION), run_time=DURATION, rate_func=linear)
        graphics.remove_updater(update)
