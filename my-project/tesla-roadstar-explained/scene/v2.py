"""Premium v2 treatment; shares source clocks and physics with the original film."""

from dataclasses import replace
from math import cos, pi, sin

import numpy as np
import pyvista as pv

from faceless_champ import ArchCamera, ArchChamp, ArchScript, ArchStyle, Canvas, Scene

from . import physics as p
from .equations import visible
from .model import HOOK_DURATION, View, experiment_road, hook_state, lines, merge, part, tracks, vehicle
from .story import DOCK, RoadsterRenderer, model_state
from .timing import CHAPTERS, shot_at
from .v2_drawing import V2Painter


def opening_view():
    """Full C-road with physical depth, three-quarter orbit, and a moving car."""
    parts = vehicle() + experiment_road()
    radius = p.RADIUS + p.CG_HEIGHT
    angles = np.linspace(0, pi, 181)
    path = [(-23, 0), (0, 0)] + [(radius * sin(a), radius - radius * cos(a)) for a in angles[1:]] + [(-10, 2 * radius)]
    lower = (
        [(-23, -0.35), (0, -0.35)]
        + [((radius + 0.35) * sin(a), radius - (radius + 0.35) * cos(a)) for a in angles[1:]]
        + [(-10, 2 * radius + 0.35)]
    )
    sidewalls, underside = [], []
    for y in (-2.6, 2.6):
        points = [(x, y, z) for top, bottom in zip(path, lower) for x, z in (top, bottom)]
        faces = [[4, 2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2] for i in range(len(path) - 1)]
        sidewalls.append(pv.PolyData(points, np.asarray(faces).ravel()))
        underside.append(lines([(x, y, z) for x, z in lower]))
    parts += [
        part("stage_depth", merge(sidewalls), "#18335B"),
        part("stage_underlight", merge(underside), "#2868D6", "wireframe", 0.8, 2),
    ]
    ids = tuple(a.id for a in parts if not a.id.startswith("stage"))
    first = p.replay(hook_state(0)[2])
    parts = [replace(a, position=first.position, rotation=first.rotation) if a.id in ids else a for a in parts]
    script = ArchScript()
    samples = []
    for time in np.linspace(0, HOOK_DURATION, 97):
        state = p.replay(hook_state(float(time))[2])
        samples.append((float(time), state.position, state.rotation))
    tracks(script, ids, samples)
    camera = ArchCamera((-27, -55, 30), (-3, 0, 12.2), projection="perspective", view_angle=35, zoom=1.06)
    script.camera_to(
        ArchCamera((-3, -53, 24), (-3, 0, 12.2), projection="perspective", view_angle=35, zoom=1.06),
        at=0,
        duration=HOOK_DURATION,
        easing="smooth",
    )
    hidden = tuple(a.id for a in parts if a.style and a.style.opacity == 0)
    if hidden:
        script.hide(hidden, at=0, duration=0.000001)
    viewport = ArchChamp(
        parts,
        script,
        width=1600,
        height=900,
        position=(800, 450),
        camera=camera,
        units="m",
        style=ArchStyle(concept="solid"),
    )
    return View(viewport, Scene(Canvas(1600, 900, "#00000000")).add(viewport).wait(HOOK_DURATION), HOOK_DURATION)


class RoadsterV2Renderer(RoadsterRenderer):
    def view(self, mode):
        if mode == "hook-establish" and mode not in self.views:
            self.views[mode] = opening_view()
        return super().view(mode)

    def frame(self, node, time, size):
        self.source_time = time
        shot = shot_at(time)
        chapter = shot.chapter
        signature = (self.measuring, self.geometry, size, time)
        if signature == self.last_signature:
            return self.last_frame.copy()
        paint = V2Painter(size, self.math, self.math_cache, self.measuring, time)
        mode, age, origin = model_state(chapter, time)
        box = (0, 0, 1920, 1080)
        if time < HOOK_DURATION:
            mode, age, origin, box = self.opening(paint, time)
        elif chapter == 1 and time >= 35.88:
            self.questions(paint, time)
        elif chapter == 2 and time < 57:
            self.blueprint(paint, time)
        else:
            dock = p.smooth(p.progress(time, DOCK[chapter - 1] - 1.15, DOCK[chapter - 1]))
            full = np.array((0, 15, 1920, 1000))
            small = np.array((60, 40, 990, 710) if mode == "fans" else (-5, 25, 1130, 750))
            rect = tuple(full + (small - full) * dock)
            if chapter == 10 and time >= 733.6:
                rect = (80, 40, 1760, 980)
            view, box = self.arch(paint, mode, age, rect)
            self.overlays(paint, chapter, time, mode, age, origin, view, box)
            if dock > 0.05:
                # Sequential entrance: physical object, relationship, equation.
                layer = paint.layer()
                self.science(layer, chapter, time, age)
                enter = p.smooth(p.progress(time - shot.start, 0.05, 0.75))
                paint.composite(layer, dock * enter, (28 * (1 - enter), 0))
                self.equations(paint, chapter, time)
            if chapter == 1 and time >= 23.56:
                expression = (
                    r"F_s=\Delta p\,A"
                    if time < 29.96
                    else r"\boldsymbol{\tau}=\mathbf{r}\times\mathbf{F}"
                    if time < 32.74
                    else r"T_z>mg"
                )
                paint.formula(expression)
            if chapter == 10 and time >= 703.24:
                self.limitations(paint, time)
        self.last_layout = paint.boxes
        self.last_state = {
            "version": "v2",
            "chapter": chapter,
            "shot": shot.id,
            "mode": mode,
            "age": age,
            "origin": np.asarray(origin).tolist(),
            "time": time,
            "primary_box": box,
        }
        result = paint.finish()
        self.last_signature, self.last_frame = signature, result.copy()
        return result

    def opening(self, paint, time):
        mode, local, clock = hook_state(time)
        state = p.replay(clock)
        origin = np.asarray(state.position)
        view, box = self.arch(paint, mode, local, (40, 25, 1840, 1030))
        # Twin luminous tire wakes are attached to the moving chassis.
        for side in (-0.8, 0.8):
            trail = []
            for q in np.linspace(max(1.1, clock - 0.82), clock, 42):
                past = p.replay(float(q))
                point = np.asarray(past.position) + p.rotation_matrix(past.rotation) @ np.array((-0.9, side, -0.35))
                screen = self.project(view, box, local, point)
                if screen:
                    trail.append(screen)
            if len(trail) > 1:
                paint.line(trail, "red", 5.5, alpha=0.2)
                paint.line(trail[-22:], "red", 2.8, alpha=0.9)
                paint.line(trail[-6:], "white", 1.2, alpha=0.85)
        # Radius construction follows the car only while it is in the curved road.
        if 3 < clock < p.RELEASE_TIME:
            center = self.project(view, box, local, (0, 0, p.RADIUS + p.CG_HEIGHT))
            point = self.project(view, box, local, origin)
            if center and point:
                reveal = p.smooth(p.progress(clock, 3, 3.5))
                end = np.asarray(center) + (np.asarray(point) - center) * reveal
                paint.line([center, end], "blue", 1.5, alpha=0.55, dash=True)
                paint.circle(center, 4, "blue", 1, fill="white")
                label = np.asarray(center) + (np.asarray(point) - center) * 0.43 + (0, -24)
                paint.equation(r"R", tuple(label), size=42, width=100, color="cyan", alpha=reveal, anchor="mm")
        if state.phase == "FLIGHT" and state.roll_time < 1.6:
            rotation = p.rotation_matrix(state.rotation)
            for side in (-1, 1):
                point = origin + rotation @ np.array((0, side * 0.75, 0))
                direction = rotation @ np.array((0, 0, -side * (1 if state.roll_time < 0.8 else -1)))
                self.plume(paint, view, box, local, point, direction, time)
        return mode, local, origin, box

    @staticmethod
    def equations(paint, chapter, time):
        beats = visible(chapter, time)
        if not beats:
            return
        beat = beats[-1]
        elapsed = time - beat.time
        reveal = p.smooth(p.progress(elapsed, 0.08, 0.65))
        # Previous relation remains briefly as context, then makes room for the result.
        if len(beats) > 1 and elapsed < 2.8:
            alpha = 0.6 * (1 - p.smooth(p.progress(elapsed, 1.6, 2.8)))
            paint.equation(
                beats[-2].expression,
                (960, 811),
                size=38,
                width=1520,
                color="muted",
                alpha=alpha,
                anchor="mm",
                tag="previous-relation",
            )
        paint.formula(beat.expression, (960, 930 + 22 * (1 - reveal)), alpha=reveal, tag=f"cue-{beat.cue}")
        # A short paired rule gives the equation an optical base, without a footer.
        length = 140 * reveal
        paint.line([(960 - length, 1030), (954, 1030)], "red", 2, alpha=reveal)
        paint.line([(966, 1030), (960 + length, 1030)], "blue", 2, alpha=reveal)

    @staticmethod
    def fan(paint, center, radius=85, color="cyan"):
        paint.fan(center, radius)

    @staticmethod
    def jet(paint, center, color="orange", scale=1):
        x, y = center
        # Curved convergent/divergent nozzle, with streamlines through the throat.
        xs = np.linspace(-100, 85, 70)
        radii = 16 + 44 * ((xs + 20) / 105) ** 2
        radii = np.minimum(radii, 48)
        top = [(x + u * scale, y - r * scale) for u, r in zip(xs, radii)]
        bottom = [(x + u * scale, y + r * scale) for u, r in zip(xs, radii)]
        paint.polygon(top + bottom[::-1], "#07172B")
        paint.line(top, "blue", 3)
        paint.line(bottom, "blue", 3)
        for row in range(-2, 3):
            path = [(x + u * scale, y + row * r * 0.28 * scale) for u, r in zip(xs, radii)]
            path += [(x + (85 + q * 150) * scale, y + row * (13 + q * 24) * scale) for q in np.linspace(0, 1, 20)]
            paint.line(path, "red", 1.2, alpha=0.35)
            phase = (paint.time * 0.7 + row * 0.12) % 1
            index = int(phase * (len(path) - 1))
            paint.line(path[max(0, index - 5) : index + 1], "cyan", 2.5)
            paint.circle(path[index], 2.1 * scale, "white", fill="white")

    @staticmethod
    def pressure(paint, time):
        # Isometric transparent pressure chamber. Geometry communicates volume,
        # seal and extraction, while the only labels are the actual variables.
        a, b, c, d = (1140, 390), (1640, 390), (1780, 305), (1280, 305)
        down = np.array((0, 180))
        floor = [tuple(np.asarray(v) + down) for v in (a, b, c, d)]
        paint.polygon(floor, "#06152B")
        paint.polygon([a, b, floor[1], floor[0]], "#081D37")
        paint.polygon([b, c, floor[2], floor[1]], "#0A2643")
        paint.line([*floor, floor[0]], "blue", 2.5)
        for top, bottom in zip((a, b, c, d), floor):
            paint.line([top, bottom], "blue", 1.5, alpha=0.7)
        paint.line([a, b, c, d, a], "cyan", 3)
        for i in range(7):
            x = 1210 + i * 72
            q = (time * 0.8 - i * 0.13) % 1
            paint.arrow((x, 195 + q * 30), (x, 255 + q * 30), "red", width=2.4)
        for i in range(20):
            q = (time * 0.31 + i / 20) % 1
            x = 1180 + 450 * q
            y = 537 - 28 * sin(q * pi) - (i % 3) * 13
            paint.circle((x, y), 2.2, "cyan", fill="cyan")
        for x, y in ((1330, 355), (1555, 355)):
            # Squashed rotor blades lie in the roof plane of the chamber.
            paint.arc((x, y), 47, 0, 2 * pi, "blue", 2.2, squash=0.45)
            for i in range(6):
                angle = time * 4 + i * pi / 3
                paint.line([(x, y), (x + 40 * cos(angle), y + 18 * sin(angle))], "cyan", 3)
        paint.equation(r"p_a=101.3\,\mathrm{kPa}", (1450, 115), size=46, width=680, anchor="mm")
        paint.equation(
            r"p_u\simeq84.6\,\mathrm{kPa}" if time >= 215.48 else r"p_u<p_a",
            (1435, 457),
            size=46,
            width=560,
            color="cyan",
            anchor="mm",
        )
        if time >= 210.65:
            paint.line([(1170, 620), (1670, 620), (1790, 550)], "muted", 1.4)
            paint.equation(r"A=2\,\mathrm{m^2}", (1460, 685), size=48, width=600, anchor="mm")

    @staticmethod
    def control(paint, time):
        for i, symbol in enumerate((r"\mathbf{r}", r"\mathbf{v}", r"\mathbf{q}", r"\boldsymbol{\omega}")):
            x = 1180 + i * 190
            paint.equation(symbol, (x, 155), size=54, width=140, color="cyan" if i < 3 else "red", anchor="mm")
            paint.line([(x - 26, 204), (x + 26, 204)], "blue" if i < 3 else "red", 2)
        if time < 562.4:
            paint.equation(r"\mathbf{I}=", (1130, 418), size=48, width=125, color="cyan", anchor="mm")
            paint.matrix(
                ((r"800", r"I_{xy}", r"I_{xz}"), (r"I_{xy}", r"I_{yy}", r"I_{yz}"), (r"I_{xz}", r"I_{yz}", r"I_{zz}")),
                (1230, 280),
                cell=(177, 92),
                size=49,
            )
            paint.equation(r"[\mathrm{kg\,m^2}]", (1500, 607), size=32, width=300, color="muted", anchor="mm")
        else:
            # Each column is one nozzle wrench [d; r x d]. Signed blue/red
            # coefficients are fixed; the scan indicates column-wise allocation.
            locations = np.array(
                [
                    (1.5, -0.75, 0),
                    (1.5, 0.75, 0),
                    (-1.5, -0.75, 0),
                    (-1.5, 0.75, 0),
                    (1, -0.75, 0),
                    (1, 0.75, 0),
                    (-1, -0.75, 0),
                    (-1, 0.75, 0),
                    (0, -0.75, 0),
                    (0, 0.75, 0),
                ]
            )
            directions = np.array(
                [(0, 0, 1)] * 4 + [(0, 1, 0), (0, -1, 0), (0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0)]
            )
            allocation = np.vstack((directions.T, np.cross(locations, directions).T))
            paint.equation(r"\mathbf{B}\in\mathbb{R}^{6\times10}", (1450, 259), size=45, width=650, anchor="mm")
            column = int(time * 1.7) % 10
            for row in range(6):
                for col in range(10):
                    x, y = 1150 + col * 66, 335 + row * 45
                    value = allocation[row, col]
                    paint.polygon(
                        [(x, y), (x + 45, y), (x + 45, y + 26), (x, y + 26)],
                        "#163B67" if value > 0 else "#5B1628" if value < 0 else "#08101B",
                    )
                    if value:
                        paint.line([(x + 10, y + 13), (x + 35, y + 13)], "cyan" if value > 0 else "red", 2.4)
                        if value > 0:
                            paint.line([(x + 22, y + 6), (x + 22, y + 20)], "cyan", 2.4)
                    if col == column:
                        paint.line([(x, y + 29), (x + 45, y + 29)], "white", 1.3, alpha=0.6)
            for x, direction in ((1128, 1), (1800, -1)):
                paint.line([(x + 15 * direction, 326), (x, 326), (x, 605), (x + 15 * direction, 605)], "blue", 2.5)
        if time >= 547.88:
            symbols = (r"\hat{\mathbf{x}}", r"\mathbf{w}", r"\mathbf{u}", r"(\mathbf{F},\boldsymbol{\tau})")
            centers = (1170, 1360, 1550, 1770)
            for i, (x, symbol) in enumerate(zip(centers, symbols)):
                paint.equation(symbol, (x, 714), size=37, width=180, anchor="mm", color="red" if i == 2 else "white")
                paint.line([(x - 35, 758), (x + 35, 758)], "red" if i == 2 else "blue", 2.5)
                if i < 3:
                    x1, x2 = x + 65, centers[i + 1] - 65
                    paint.arrow((x1, 714), (x2, 714), "dim", width=2)
                    q = (time * 0.65 - i * 0.2) % 1
                    paint.circle((x1 + (x2 - x1) * q, 714), 3, "cyan", fill="white")

    def questions(self, paint, time):
        q = time - 35.88
        phase = min(2, int(q / 3.7))
        examples = (
            ("loop", 2.65 + 0.35 * sin(q * 0.6), r"F_s=\Delta p\,A"),
            ("roll", 0.8 + 0.72 * sin(q * 0.65), r"\tau=I\alpha"),
            ("landing", p.landing(0)["end"] * ((q * 0.12) % 1), r"T_z>mg"),
        )
        mode, age, formula = examples[phase]
        self.arch(paint, mode, age, (70, 15, 1780, 820))
        paint.formula(formula)

    def blueprint(self, paint, time):
        q = time - CHAPTERS[1][0]
        self.arch(paint, "side", 0.5, (30, 120, 1230, 690))
        for i, mode in enumerate(("top", "front")):
            self.arch(paint, mode, 0.5, (1260, 90 + i * 365, 600, 340))
        scan = 180 + (q * 0.27 % 1) * 640
        paint.line([(110, scan), (1160, scan)], "blue", 1.3, alpha=0.45)
        paint.line([(1200, 140), (1200, 750)], "dim", 1)
