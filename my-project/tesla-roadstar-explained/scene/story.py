"""Forty-shot deterministic film renderer using public core rendering interfaces.

The root is a normal Scene with one master audio clip. This renderer implements
the core Renderer protocol; ArchChamp owns 3D authoring, PillowRenderer owns all
VTK sessions, and the project composes scientific plots and typeset equations.
"""

from collections import OrderedDict
from math import cos, pi, sin

import numpy as np
from PIL import Image

from faceless_champ import (
    Canvas,
    FlowChamp,
    FlowEdge,
    FlowGraph,
    FlowNode,
    FlowScript,
    FlowTheme,
    PillowRenderer,
    Scene,
    Spring,
)

from . import DECODED_AUDIO_DURATION, END, FONT, ROOT
from . import physics as p
from .drawing import C, Painter
from .equations import BEATS, visible
from .model import hook_state, make_view
from .timing import CHAPTERS, shot_at

DOCK = (35.88, 69.76, 108.28, 179.04, 275.82, 374.8, 431.88, 541.2, 589.12, 687)
SPRING = Spring(stiffness=180, damping=28, mass=1)


def build_master():
    return (
        Scene(Canvas(1920, 1080, "#000000"))
        .add_audio(ROOT / "audio.mp3", start=0, trim_end=DECODED_AUDIO_DURATION)
        .wait_until(END)
    )


def model_state(chapter, time):
    """One mapping from media time to the independent physical experiment clocks."""
    if chapter == 1:
        if time < 6.76:
            return "hero", 12 * p.progress(time, 0, 6.76), np.zeros(3)
        if time < 23.56:
            if time < 15.68:
                q = p.RELEASE_TIME * p.progress(time, 6.76, 15.68)
            else:
                q = p.RELEASE_TIME + p.FLIGHT_TIME * p.progress(time, 15.68, 23.56)
            return "replay", q, np.asarray(p.replay(q).position)
        if time < 29.96:
            return "loop", pi, np.asarray(p.loop(pi)["position"])
        if time < 32.74:
            q = 1.6 * p.progress(time, 29.96, 32.74)
            return "roll", q, np.zeros(3)
        if time < 35.88:
            q = p.landing(0)["end"] * p.progress(time, 32.74, 35.88)
            return "landing", q, np.array((4.6, 0, p.landing(q)["height"]))
        return "model", 3, np.zeros(3)
    if chapter == 2:
        if time < 69.76:
            return "assembly", 12 * p.progress(time, 57, 69.76), np.zeros(3)
        return "model", 3, np.zeros(3)
    if chapter == 3:
        if time < 146.16:
            a = 30 if time < 139.74 else 30 + 15 * p.progress(time, 139.74, 146.16)
        else:
            a = 45 + 45 * p.progress(time, 146.16, 158.5)
        return "slope", a, np.zeros(3)
    if chapter == 4:
        if time < 228.72:
            return "fans", 12 * p.progress(time, 170.76, 228.72), np.zeros(3)
        q = 12 * p.progress(time, 228.72, 268.88)
        return "wall", q, np.array((0, 0, 3 * p.progress(q, 3, 12)))
    if chapter == 5:
        a = 2 + (pi - 2) * p.progress(time, 285.52, 301.16) if 285.52 <= time < 301.16 else pi
        return "loop", a, np.asarray(p.loop(a)["position"])
    if chapter == 6:
        if time < 362.74:
            q = p.RELEASE_TIME + min(p.FLIGHT_TIME, 1.1 * p.progress(time, 353.4, 362.74))
            return "replay", q, np.asarray(p.replay(q).position)
        if time < 374.8:
            return "tanks", 5 * p.progress(time, 362.74, 374.8), np.zeros(3)
        return "nozzle", 4, np.zeros(3)
    if chapter == 7:
        if time < 457.92:
            q = 0
        elif time < 469.24:
            q = 1.6 * p.progress(time, 457.92, 469.24)
        elif time < 509.92:
            q = 0
        else:
            q = 1.6 * p.progress(time, 509.92, 517.68)
        return "roll", q, np.zeros(3)
    if chapter == 8:
        return "control", 2 * p.progress(time, 574.2, 580), np.zeros(3)
    if chapter == 9:
        end = p.landing(0)["end"]
        if time < 605.84:
            q = p.landing(0, assisted=False)["end"] * p.progress(time, 583.02, 602.91)
        elif time < 629.88:
            q = 0.6 * p.progress(time, 605.84, 625.28) + 0.4 * p.progress(time, 628.14, 629.88)
            return "hover", q, np.array((0, 0, p.hover_demo(q)["height"]))
        elif time < 642.07:
            q = p.landing(0)["switch"] * p.progress(time, 632.64, 642.07)
        elif time < 658.76:
            q = p.landing(0)["switch"]
        else:
            q = p.landing(0)["switch"] + (end - p.landing(0)["switch"]) * p.progress(time, 658.76, 665.26)
        return "landing", q, np.array((4.6, 0, p.landing(q)["height"]))
    if time < 703.24:
        q = p.REPLAY_TIME * p.progress(time, 677.92, 703.24)
        return "replay", q, np.asarray(p.replay(q).position)
    return "hero", 12 * p.progress(time, 703.24, 738.12), np.zeros(3)


def flow_view():
    nodes = tuple(
        FlowNode(id, label, position=(150 + i * 300, 100), size=(270, 140))
        for i, (id, label) in enumerate(
            (
                ("estimate", "r, v, q, ω"),
                ("controller", "w"),
                ("allocator", "B u"),
                ("jets", "F, τ"),
            )
        )
    )
    edges = tuple(FlowEdge(f"link{i}", nodes[i].id, nodes[i + 1].id) for i in range(3))
    edges += (FlowEdge("feedback", "jets", "estimate", waypoints=((1050, 220), (150, 220))),)
    script = FlowScript().reveal(tuple(n.id for n in nodes), at=0, duration=1, stagger=0.5)
    script.reveal(tuple(e.id for e in edges), at=2.5, duration=1)
    for i in range(3):
        script.signal(f"link{i}", at=3.5 + i, duration=1, color=C["cyan"], marker="packet")
    view = FlowChamp(
        FlowGraph(nodes, edges, layout="manual"),
        script,
        width=1200,
        height=280,
        position=(600, 140),
        theme=FlowTheme(
            font=str(FONT),
            font_size=34,
            minimum_font_size=34,
            foreground=C["white"],
            surface="#071018",
            background="#00000000",
            accent=C["cyan"],
            stroke=C["blue"],
            node_stroke=C["cyan"],
            stroke_width=1.6,
        ),
    )
    return Scene(Canvas(1200, 280, "#00000000")).add(view).wait(7)


class RoadsterRenderer:
    def __init__(self, geometry=True):
        self.core = PillowRenderer(1, arch_session_limit=3, frame_cache_mb=24)
        self.math = PillowRenderer(1, frame_cache_mb=8)
        self.views = OrderedDict()
        self.math_cache = {}
        self.last_layout = []
        self.last_state = {}
        self.flow = None
        self.geometry = geometry
        self.measuring = False
        self.blueprints = {}
        self.fan_frames = OrderedDict()
        self.last_signature = None
        self.last_frame = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.core.close()
        self.math.close()
        self.views.clear()
        self.math_cache.clear()
        self.fan_frames.clear()
        self.last_frame = None

    def validate(self, node):
        if not isinstance(node, Scene) or abs(node.duration - END) > 1e-7:
            raise ValueError("Use build_master(); export ranges retain the master source clock")

    def view(self, mode):
        if mode not in self.views:
            self.views[mode] = make_view(mode)
            if len(self.views) > 8:
                self.views.popitem(last=False)
        self.views.move_to_end(mode)
        return self.views[mode]

    def arch(self, paint, mode, age, rect, alpha=1):
        # This camera drift continues even while a narrated physical state is held.
        x, y, w, h = rect
        t = getattr(self, "source_time", 0)
        zoom = 1 if mode == "hook-establish" else 1.025 + 0.018 * sin(t * 0.47)
        rect = (
            x - w * (zoom - 1) / 2 + (0 if mode == "hook-establish" else 8 * sin(t * 0.63)),
            y - h * (zoom - 1) / 2 + (0 if mode == "hook-establish" else 6 * cos(t * 0.51)),
            w * zoom,
            h * zoom,
        )
        v = self.view(mode)
        age = p.clamp(age, 0, v.duration)
        # Keep a stable viewport size during camera drift. HD/4K render at native
        # composition resolution; low review mode uses a smaller 3D viewport.
        native = (1920 if rect[2] > 1200 else 1080) if paint.scale >= 1 else (1280 if rect[2] > 1200 else 896)
        if mode == "hook-establish":
            native = 1920
        width = round(native * paint.scale)
        height = round(width * 9 / 16)
        if not self.geometry or alpha < 1e-6:
            ratio = min(rect[2] / 1600, rect[3] / 900)
            w, h = 1600 * ratio, 900 * ratio
            return v, (rect[0] + (rect[2] - w) / 2, rect[1] + (rect[3] - h) / 2, w, h)
        elif mode == "fans" and age >= 2:
            phase = ((age - 2) % 0.5) * 48
            first = int(phase)
            frames = []
            for index in (first, (first + 1) % 24):
                key = (width, index)
                if key not in self.fan_frames:
                    self.fan_frames[key] = self.core.frame(v.scene, 2 + index / 48, (width, height))
                    while len(self.fan_frames) > 24:
                        self.fan_frames.popitem(last=False)
                self.fan_frames.move_to_end(key)
                frames.append(self.fan_frames[key])
            image = Image.blend(frames[0], frames[1], phase - first)
        else:
            image = self.core.frame(v.scene, age, (width, height))
        box = paint.paste(image, rect, alpha, glow=True)
        return v, box

    @staticmethod
    def project(v, box, age, point):
        result = v.component.project_at(age, [tuple(point)])[0]
        if result is None:
            return None
        x, y, w, h = box
        return (x + result[0] / v.component.width * w, y + result[1] / v.component.height * h)

    def force(self, paint, v, box, age, origin, vector, color, label, scale=0.00009, offset=(12, -15), dash=False):
        if np.linalg.norm(vector) < 1e-6:
            return
        a = self.project(v, box, age, origin)
        b = self.project(v, box, age, np.asarray(origin) + np.asarray(vector) * scale)
        if a and b and np.linalg.norm(np.asarray(b) - a) >= 16:
            paint.arrow(a, b, color, width=3.5, dash=dash)
            if label:
                symbols = {
                    "mg sin θ": r"mg\sin\theta",
                    "friction": r"f",
                    "required grip": r"f",
                    "suction": r"F_s",
                    "reaction thrust": r"F",
                    "braking": r"T_z",
                }
                paint.equation(
                    symbols.get(label, label),
                    (b[0] + offset[0], b[1] + offset[1]),
                    size=31,
                    width=185,
                    color=color,
                    tag=f"force-{label}",
                )

    def frame(self, node, time, size):
        shot = shot_at(time)
        chapter = shot.chapter
        self.source_time = time
        # Time is always part of the signature: a held force state still has live
        # camera motion, flowing particles, a graph trace and a breathing glow.
        signature = (self.measuring, self.geometry, size, time)
        if signature == self.last_signature:
            return self.last_frame.copy()
        paint = Painter(size, self.math, self.math_cache, measure_only=self.measuring, time=time)
        mode, age, origin = model_state(chapter, time)
        box = (0, 0, 1920, 1080)
        if time < 6.76:
            mode, age, origin, box = self.opening(paint, time)
        elif chapter == 1 and time >= 35.88:
            self.questions(paint, time)
        elif chapter == 2 and time < 57:
            self.blueprint(paint, time)
        else:
            dock = SPRING(p.progress(time, DOCK[chapter - 1] - 1.2, DOCK[chapter - 1]))
            full = np.array((20, 80, 1880, 910))
            small = np.array((20, 70, 1060, 730))
            rect = tuple(full + (small - full) * dock)
            if chapter == 10 and time >= 733.6:
                rect = (120, 90, 1680, 880)
            v, box = self.arch(paint, mode, age, rect)
            self.overlays(paint, chapter, time, mode, age, origin, v, box)
            if dock > 0.1:
                self.science(paint, chapter, time, age)
                self.equations(paint, chapter, time)
            if chapter == 1 and time >= 23.56:
                expression = (
                    r"F_s=\Delta p\,A"
                    if time < 29.96
                    else r"\boldsymbol{\tau}=\mathbf{r}\times\mathbf{F}"
                    if time < 32.74
                    else r"T_z>mg"
                )
                paint.equation(expression, (110, 900), size=78, width=1600, color="cyan")
            if chapter == 10 and time >= 703.24:
                self.limitations(paint, time)
        # Brief chapter dissolves replace the old title and footer furniture.
        if chapter > 1:
            fade = p.smooth(p.progress(time, CHAPTERS[chapter - 1][0], CHAPTERS[chapter - 1][0] + 0.25))
        else:
            fade = 1
        self.last_layout = paint.boxes
        self.last_state = {
            "chapter": chapter,
            "shot": shot.id,
            "mode": mode,
            "age": age,
            "origin": np.asarray(origin).tolist(),
            "time": time,
            "primary_box": box,
        }
        result = paint.finish()
        if fade < 1 and not self.measuring:
            result = Image.blend(Image.new("RGB", size), result, fade)
        self.last_signature, self.last_frame = signature, result.copy()
        return result

    def layout_at(self, time, size=(3840, 2160)):
        """Measure actual output-size glyphs without rasterizing geometry."""
        geometry, measuring = self.geometry, self.measuring
        self.geometry, self.measuring = False, True
        try:
            self.frame(None, time, size)
            return self.last_layout
        finally:
            self.geometry, self.measuring = geometry, measuring

    def opening(self, paint, time):
        """One continuous wide demonstration, with the entire C-road in view."""
        mode, local, clock = hook_state(time)
        state = p.replay(clock)
        origin = np.asarray(state.position)
        view, box = self.arch(paint, mode, local, (75, 50, 1770, 980))
        # A short red wake makes direction readable while the blue road outline
        # supplies the spatial reference. No title, inset or cropped close-up.
        path = []
        for q in np.linspace(max(1.1, clock - 0.7), clock, 28):
            past = p.replay(float(q))
            point = np.asarray(past.position) + p.rotation_matrix(past.rotation) @ np.array((0, -0.95, -0.28))
            projected = self.project(view, box, local, point)
            if projected:
                path.append(projected)
        paint.line(path, "red", 3.8, alpha=0.85)
        # The pulse follows the road centerline rather than drifting in screen space.
        for i in range(6):
            angle = (time * 0.42 + i * pi / 6) % pi
            radius = p.RADIUS + p.CG_HEIGHT
            point = self.project(view, box, local, (radius * sin(angle), 0, radius - radius * cos(angle)))
            if point:
                paint.circle(point, 2.5, "red", fill="white")
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
        # A centered equation stage uses one stable reading axis across chapters.
        paint.line([(140, 884), (1780, 884)], "dim", 1, alpha=0.65)
        paint.line([(140, 884), (235, 884)], "red", 2.2)
        paint.line([(1685, 884), (1780, 884)], "blue", 2.2)
        if len(beats) > 1:
            previous = beats[-2]
            paint.equation(
                previous.expression,
                (960, 812),
                size=44,
                width=1620,
                color="muted",
                tag=f"cue-{previous.cue}",
                anchor="mt",
            )
        beat = beats[-1]
        reveal = p.smooth(p.progress(time, beat.time, beat.time + 0.45))
        paint.equation(
            beat.expression,
            (960, 925 + 10 * (1 - reveal) + 1.5 * sin(time * 1.7)),
            size=86,
            width=1650,
            color=beat.color,
            alpha=reveal,
            tag=f"cue-{beat.cue}",
            anchor="mt",
        )

    def overlays(self, paint, chapter, time, mode, age, origin, v, box):
        com = self.project(v, box, age, origin)
        if com and chapter in (2, 3, 4, 5, 7, 8, 9):
            paint.circle(com, 5.5, "white", 2, fill="cyan")
            paint.arc(com, 12 + 2 * sin(time * 3), time, time + 4.8, "cyan", 1.2, alpha=0.7)
        if chapter == 2 and time >= 77.36:
            self.force(paint, v, box, age, origin, (0, 0, -p.WEIGHT), "amber", "W", scale=0.00009)
            if time >= 86.5:
                self.force(paint, v, box, age, origin, (0, 0, p.WEIGHT), "blue", "N", scale=0.00009, offset=(12, -25))
        elif chapter == 3:
            angle = age * pi / 180
            state = p.incline(angle)
            normal, tangent = np.array((-sin(angle), 0, cos(angle))), np.array((cos(angle), 0, sin(angle)))
            self.force(paint, v, box, age, origin, (0, 0, -p.WEIGHT), "amber", "mg", scale=0.00015, offset=(-70, 15))
            if time >= 108.28:
                self.force(paint, v, box, age, origin, normal * state["normal"], "blue", "N", scale=0.00015)
                self.force(
                    paint,
                    v,
                    box,
                    age,
                    origin,
                    -tangent * state["downhill"],
                    "amber",
                    r"mg\sin\theta",
                    scale=0.00015,
                    offset=(-160, -24),
                    dash=True,
                )
            if time >= 121.64:
                self.force(paint, v, box, age, origin, tangent * state["friction"], "green", "f", scale=0.00015)
            paint.equation(rf"\theta={age:.0f}^\circ", (80, 710), size=42, width=380, color="white")
        elif chapter == 4 and time >= 228.72:
            for vector, color, label, scale, offset in (
                ((0, 0, -p.WEIGHT), "amber", "mg", 0.00013, (-80, 8)),
                ((-p.SUCTION, 0, 0), "blue", "N", 0.00008, (-35, -35)),
                ((p.SUCTION, 0, 0), "purple", "F_s", 0.00008, (15, -30)),
                ((0, 0, p.WEIGHT), "green", "f", 0.00013, (15, -30)),
            ):
                self.force(paint, v, box, age, origin, vector, color, label, scale=scale, offset=offset)
        elif chapter == 5:
            state = p.loop(age, speed=0 if time < 285.52 else 12)
            self.force(paint, v, box, age, origin, (0, 0, -p.WEIGHT), "amber", "mg", scale=0.0001, offset=(-85, 5))
            self.force(paint, v, box, age, origin, -state["inward"] * p.SUCTION, "purple", "F_s", scale=0.00008)
            self.force(
                paint,
                v,
                box,
                age,
                origin,
                state["inward"] * state["normal"],
                "blue",
                "N",
                scale=0.00008,
                offset=(18, 15),
            )
            if 285.52 <= time < 301.16:
                self.force(paint, v, box, age, origin, state["tangent"] * 1.7, "white", "v", scale=1, offset=(-30, -36))
        elif chapter == 6 and mode == "nozzle":
            self.plume(paint, v, box, age, (1.6, 0, 0), (1, 0, 0), time)
            self.force(paint, v, box, age, (0, 0, 0), (-22000, 0, 0), "orange", "F", scale=0.0001, offset=(-30, 20))
        elif chapter == 7:
            rotation = p.rotation_matrix((p.roll(age)["theta"] * 180 / pi, -180, 0))
            if time < 437.88:
                point = origin if time < 431.88 else origin + rotation @ np.array((0, 0.75, 0))
                self.force(paint, v, box, age, point, rotation @ np.array((0, 0, 8500)), "orange", "F", scale=0.00015)
            else:
                for side in (-1, 1):
                    point = origin + rotation @ np.array((0, side * 0.75, 0))
                    force = rotation @ np.array((0, 0, -side * p.roll(age)["force"] * (1 if age < 0.8 else -1)))
                    if time >= 491.44:
                        self.force(
                            paint,
                            v,
                            box,
                            age,
                            point,
                            force,
                            "orange",
                            "F",
                            scale=0.0004,
                            offset=(15, -18) if side > 0 else (-40, 10),
                        )
            if time >= 444.16:
                paint.equation(rf"t={age:.2f}\,\mathrm{{s}}", (80, 710), size=42, width=380)
        elif chapter == 8 and com:
            rotation = p.rotation_matrix((12 * (1 - p.roll(age, duration=2)["theta"] / pi), 0, 0))
            for axis, label, color in (
                ([1.8, 0, 0], "x", "cyan"),
                ([0, 1.8, 0], "y", "purple"),
                ([0, 0, 1.8], "z", "amber"),
            ):
                self.force(paint, v, box, age, origin, rotation @ axis, color, label, scale=1)
        elif chapter == 9:
            if mode == "hover":
                state = p.hover_demo(age)
                position = np.array((0, 0, state["height"]))
                self.force(
                    paint, v, box, age, position, (0, 0, -p.WEIGHT), "amber", "mg", scale=0.0002, offset=(-60, 5)
                )
                self.force(paint, v, box, age, position, (0, 0, state["thrust"]), "orange", "T_z", scale=0.0002)
                self.force(
                    paint,
                    v,
                    box,
                    age,
                    position,
                    (0, 0, state["velocity"]),
                    "cyan",
                    "v",
                    scale=0.25,
                    offset=(25, 5),
                    dash=True,
                )
            else:
                for x, assisted, color in ((-4.6, False, "amber"), (4.6, True, "cyan")):
                    state = p.landing(age, assisted=assisted)
                    position = np.array((x, 0, state["height"]))
                    self.force(paint, v, box, age, position, (0, 0, -p.WEIGHT), "amber", "", scale=0.00013)
                    if assisted and state["thrust"]:
                        self.force(
                            paint, v, box, age, position, (0, 0, state["thrust"]), "orange", "T_z", scale=0.00013
                        )
        elif mode == "replay":
            state = p.replay(age)
            rotation = p.rotation_matrix(state.rotation)
            if state.phase in {"FLIGHT", "BRAKING"}:
                for x in (-1.15, 1.15):
                    if state.thrust:
                        self.plume(
                            paint,
                            v,
                            box,
                            age,
                            np.asarray(origin) + rotation @ np.array((x, -0.65, -0.3)),
                            (0, 0, -1),
                            time,
                        )
            if chapter == 10:
                self.force(
                    paint, v, box, age, origin, (0, 0, -p.WEIGHT), "amber", "mg", scale=0.00023, offset=(-60, 15)
                )
                if state.thrust:
                    self.force(paint, v, box, age, origin, (0, 0, state.thrust), "orange", "T_z", scale=0.00013)

    @staticmethod
    def fan(paint, center, radius=85, color="cyan"):
        x, y = center
        paint.arc(center, radius, 0, 2 * pi, color, 2)
        paint.arc(center, radius + 13, paint.time * 1.4, paint.time * 1.4 + 3.7, color, 2, alpha=0.5)
        paint.circle(center, radius * 0.15, "white", fill=color)
        for i in range(7):
            a = paint.time * 4.5 + i * 2 * pi / 7
            paint.line(
                [
                    (x + radius * 0.22 * cos(a), y + radius * 0.22 * sin(a)),
                    (x + radius * 0.8 * cos(a + 0.28), y + radius * 0.8 * sin(a + 0.28)),
                ],
                color,
                10,
            )

    @staticmethod
    def jet(paint, center, color="orange", scale=1):
        x, y = center
        paint.line(
            [(x - 80 * scale, y - 34 * scale), (x - 15 * scale, y - 34 * scale), (x + 35 * scale, y - 58 * scale)],
            color,
            3,
        )
        paint.line(
            [(x - 80 * scale, y + 34 * scale), (x - 15 * scale, y + 34 * scale), (x + 35 * scale, y + 58 * scale)],
            color,
            3,
        )
        for i in range(16):
            q = (paint.time * 0.85 + i / 16) % 1
            paint.circle(
                (x + (40 + 150 * q) * scale, y + sin(i * 2.5) * 25 * q * scale),
                (1.5 + q * 2) * scale,
                "cyan",
                fill="white",
            )

    def science(self, paint, chapter, time, age):
        graph = (1090, 160, 750, 475)
        if chapter == 2:
            if time < 69.76:
                self.fan(paint, (1280, 310), 90, "purple")
                self.jet(paint, (1600, 540))
                paint.equation(r"F_s=\Delta p\,A", (1130, 435), size=44, width=640, color="purple")
                paint.equation(r"F=\dot m v_e", (1430, 675), size=44, width=420, color="orange")
            else:
                paint.equation(r"m=1700\,\mathrm{kg}", (1150, 205), size=62, width=650)
                for i in range(17):
                    x, y = 1170 + (i % 6) * 91, 360 + (i // 6) * 70
                    paint.line(
                        [(x, y), (x + 60, y), (x + 60, y + 42), (x, y + 42), (x, y)],
                        "cyan",
                        2,
                        alpha=0.4 + 0.4 * (0.5 + 0.5 * sin(time * 2 - i)),
                    )
                paint.arrow((1435, 585), (1435, 680), "amber", width=4)
                paint.equation(r"g=9.81\,\mathrm{m\,s^{-2}}", (1160, 710), size=43, width=670, color="amber")
        elif chapter == 3:
            angles = np.linspace(0, 90, 181)
            paint.graph(
                graph,
                [
                    (r"\sin\theta", angles, np.sin(np.radians(angles)), "amber"),
                    (r"\mu\cos\theta", angles, np.cos(np.radians(angles)), "green"),
                ],
                (0, 90),
                (0, 1.2),
                r"\theta\,(^{\circ})",
                r"F/(mg)",
                cursor=age,
                shade=(0, 45),
                ticks=3,
            )
            if time >= 139.74:
                paint.equation(r"\theta_{\max}=45^\circ", (1210, 710), size=53, width=610, color="green")
        elif chapter == 4:
            if time < 228.72:
                self.pressure(paint, time)
            else:
                for y, symbol, value, color in ((290, r"\mu N", 33.354, "green"), (505, r"mg", 16.677, "amber")):
                    paint.equation(symbol, (1130, y - 58), size=50, width=650, color=color)
                    end = 1130 + value / 33.354 * 650
                    paint.line([(1130, y + 12), (end, y + 12)], color, 13)
                    marker = (time * 0.43) % 1
                    paint.circle((1130 + (end - 1130) * marker, y + 12), 5, "white", fill="white")
                    paint.equation(rf"{value:.1f}\,\mathrm{{kN}}", (1130, y + 48), size=45, width=650, color=color)
        elif chapter == 5:
            velocities = np.linspace(0, 18, 121)
            ns = (p.SUCTION + p.MASS * velocities**2 / p.RADIUS + p.WEIGHT * cos(age)) / 1000
            paint.graph(
                graph,
                [(r"N(v)", velocities, ns, "blue")],
                (0, 18),
                (0, 75),
                r"v\;(\mathrm{m/s})",
                r"N\;(\mathrm{kN})",
                cursor=0 if time < 285.52 else 12,
                ticks=3,
                legend=False,
            )
            paint.equation(r"R=12\,\mathrm{m}", (1160, 705), size=45, width=310)
            if time >= 323.13:
                paint.equation(r"v=12\,\mathrm{m/s}", (1515, 705), size=45, width=330)
        elif chapter == 6:
            if time < 404.56:
                self.jet(paint, (1390, 345), scale=1.4)
                paint.arrow((1360, 510), (1760, 510), "cyan", width=4)
                paint.equation(r"\Delta\mathbf{p}_{g}", (1570, 545), size=49, width=230, color="cyan")
                paint.arrow((1410, 660), (1125, 660), "orange", width=4)
                paint.equation(r"-\Delta\mathbf{p}_{g}", (1130, 698), size=49, width=350, color="orange")
            else:
                ts = np.linspace(0, 7.5, 121)
                paint.graph(
                    graph,
                    [(r"m_g", ts, 250 - 20000 / 600 * ts, "purple")],
                    (0, 7.5),
                    (0, 250),
                    r"t\;(\mathrm{s})",
                    r"m_g\;(\mathrm{kg})",
                    cursor=7.5 * p.progress(time, 404.56, 416.9),
                    ticks=5,
                    legend=False,
                )
        elif chapter == 7:
            if time < 444.16:
                center = (1440, 410)
                paint.circle(center, 13, "white", fill="cyan")
                paint.arc(center, 155, time, time + 5.3, "purple", 4, squash=0.75)
                paint.arrow((1440, 410), (1690, 410), "cyan", width=4)
                paint.arrow((1440, 295), (1440, 175), "orange", width=4)
                paint.line([(1440, 410), (1440, 295)], "white", 2, dash=True)
                paint.equation(r"\mathbf{r}", (1470, 330), size=48, width=250)
                paint.equation(r"\mathbf{F}", (1470, 160), size=48, width=250, color="orange")
                paint.equation(r"\mathbf{r}\times\mathbf{F}", (1210, 650), size=65, width=620, color="purple")
            else:
                ts = np.linspace(0, 1.6, 161)
                states = [p.roll(t) for t in ts]
                for y, key, ylim, symbol, color in (
                    (120, "theta", (0, 180), r"\theta\;(^{\circ})", "purple"),
                    (335, "omega", (0, 4), r"\omega\;(\mathrm{rad/s})", "cyan"),
                    (550, "alpha", (-5.5, 5.5), r"\alpha\;(\mathrm{rad/s^2})", "orange"),
                ):
                    values = np.array([s[key] for s in states])
                    if key == "theta":
                        values = np.degrees(values)
                    paint.graph(
                        (1090, y, 750, 188),
                        [(key, ts, values, color)],
                        (0, 1.6),
                        ylim,
                        r"t\;(\mathrm{s})" if key == "alpha" else "",
                        symbol,
                        cursor=age,
                        ticks=2,
                        legend=False,
                    )
        elif chapter == 8:
            self.control(paint, time)
        elif chapter == 9:
            if 605.84 <= time < 629.88:
                ts = np.linspace(0, 1, 101)
                paint.graph(
                    (1090, 190, 750, 400),
                    [(r"v_z", ts, [p.hover_demo(t)["velocity"] for t in ts], "cyan")],
                    (0, 1),
                    (-15, -9),
                    r"t\;(\mathrm{s})",
                    r"v_z\;(\mathrm{m/s})",
                    cursor=age,
                    ticks=3,
                    legend=False,
                )
                paint.equation(r"T_z=mg\;\Rightarrow\;a_z=0", (1120, 700), size=50, width=720, color="orange")
            else:
                ts = np.linspace(0, p.landing(0)["end"], 161)
                rows = (
                    (155, "height", (0, 20), r"h\;(\mathrm{m})"),
                    (430, "velocity", (-21, 1), r"v_z\;(\mathrm{m/s})"),
                )
                if time >= 629.88:
                    rows = (
                        (110, "height", (0, 20), r"h\;(\mathrm{m})"),
                        (330, "velocity", (-21, 1), r"v_z\;(\mathrm{m/s})"),
                        (550, "thrust", (0, 40), r"T_z\;(\mathrm{kN})"),
                    )
                for y, key, ylim, label in rows:
                    series = [
                        (
                            r"T_z=0" if not assisted else r"T_z=2mg",
                            ts,
                            [p.landing(t, assisted=assisted)[key] / (1000 if key == "thrust" else 1) for t in ts],
                            color,
                        )
                        for assisted, color in ((False, "amber"), (True, "cyan"))
                    ]
                    paint.graph(
                        (1090, y, 750, 195 if len(rows) == 3 else 245),
                        series,
                        (0, p.landing(0)["end"]),
                        ylim,
                        r"t\;(\mathrm{s})" if key == rows[-1][1] else "",
                        label,
                        cursor=age,
                        ticks=2,
                        legend=False,
                    )
        elif chapter == 10 and time < 703.24:
            for index, color in enumerate(("purple", "green", "blue", "orange")):
                x, y = 1245 + index % 2 * 370, 285 + index // 2 * 340
                if index == 0:
                    self.fan(paint, (x, y), 72, color)
                elif index == 1:
                    paint.arrow((x - 75, y), (x + 75, y), color, width=4)
                    paint.arc((x, y), 80, time, time + 4.6, color, 2)
                elif index == 2:
                    paint.arc((x, y), 85, -pi / 2, pi / 2, color, 3)
                    a = time * 1.6
                    paint.circle((x + 85 * cos(a), y + 85 * sin(a)), 6, color, fill="white")
                else:
                    self.jet(paint, (x - 20, y), color, 0.7)
                expression = (r"\Delta p\,A", r"\mu N", r"v^2/R", r"\int F\,dt")[index]
                paint.equation(expression, (x - 100, y + 115), size=47, width=320, color=color)

    @staticmethod
    def pressure(paint, time):
        # Flowing particles carry the explanation instead of prose labels.
        x0, x1 = 1130, 1790
        paint.line([(x0 - 25, 315), (x0 + 45, 280), (x1 - 45, 280), (x1 + 25, 315)], "cyan", 4)
        paint.line([(x0 - 25, 580), (x1 + 25, 580)], "muted", 3)
        for i in range(20):
            y = 365 + i * 10
            paint.line([(x0, y), (x1, y)], "blue", 8, alpha=0.08 + i / 100)
        for i in range(8):
            x = x0 + 40 + i * 82
            pulse = 8 * sin(time * 3 - i * 0.4)
            paint.arrow((x, 194 + pulse), (x, 255 + pulse), "purple", width=2.5)
        for i in range(30):
            q = (time * 0.35 + i / 30) % 1
            paint.circle((x0 + q * (x1 - x0), 548 - 22 * sin(q * pi) + 6 * sin(i)), 2.5, "cyan", fill="cyan")
        paint.equation(r"p_a=101.3\,\mathrm{kPa}", (1180, 105), size=43, width=650)
        paint.equation(
            r"p_u\simeq84.6\,\mathrm{kPa}" if time >= 215.48 else r"p_u<p_a",
            (1200, 425),
            size=51,
            width=640,
            color="cyan",
        )
        if time >= 210.65:
            paint.equation(r"A=2\,\mathrm{m^2}", (1280, 680), size=52, width=520, color="purple")

    @staticmethod
    def control(paint, time):
        for i, (symbol, color) in enumerate(
            (
                (r"\mathbf{r}", "cyan"),
                (r"\mathbf{v}", "blue"),
                (r"\mathbf{q}", "purple"),
                (r"\boldsymbol{\omega}", "orange"),
            )
        ):
            paint.equation(symbol, (1130 + i * 175, 130), size=62, width=150, color=color)
        if time < 562.4:
            paint.equation(r"\mathbf{I}=", (1145, 422), size=53, width=120, color="purple", anchor="mm")
            paint.matrix(
                ((r"800", r"I_{xy}", r"I_{xz}"), (r"I_{xy}", r"I_{yy}", r"I_{yz}"), (r"I_{xz}", r"I_{yz}", r"I_{zz}")),
                (1240, 300),
                cell=(177, 88),
                size=48,
                color="purple",
            )
            paint.equation(r"[\mathrm{kg\,m^2}]", (1480, 610), size=36, width=350, color="muted")
        else:
            paint.equation(r"\mathbf{B}\in\mathbb{R}^{6\times10}", (1210, 255), size=53, width=600, color="cyan")
            for row in range(6):
                for col in range(10):
                    x, y = 1140 + col * 66, 360 + row * 44
                    alpha = 0.2 + 0.7 * (0.5 + 0.5 * sin(time * 3 - row * 0.55 - col * 0.7))
                    paint.line([(x, y), (x + 36, y)], "cyan" if row < 3 else "purple", 15, alpha=alpha)
            for x, direction in ((1115, 1), (1790, -1)):
                paint.line([(x + 12 * direction, 335), (x, 335), (x, 607), (x + 12 * direction, 607)], "white", 2)
        if time >= 547.88:
            centers = (1150, 1360, 1570, 1780)
            symbols = (r"\hat{\mathbf{x}}", r"\mathbf{w}", r"\mathbf{u}", r"\mathbf{F}")
            for i, (x, symbol) in enumerate(zip(centers, symbols)):
                paint.circle((x, 720), 39, ("cyan", "purple", "orange", "cyan")[i], 2)
                paint.equation(symbol, (x - 19, 704), size=35, width=75)
                if i < 3:
                    paint.arrow((x + 46, 720), (centers[i + 1] - 46, 720), "dim", width=2)
                    q = (time * 0.7 - i * 0.23) % 1
                    paint.circle((x + 46 + q * 118, 720), 4, "cyan", fill="white")

    def questions(self, paint, time):
        # Each compact experiment keeps moving while the narrator unifies them.
        q = time - 35.88
        examples = (
            ("loop", 2.65 + 0.35 * sin(q * 0.6), r"F_s=\Delta p A", "purple"),
            ("roll", 0.8 + 0.72 * sin(q * 0.65), r"\tau=I\alpha", "orange"),
            ("landing", p.landing(0)["end"] * ((q * 0.12) % 1), r"T_z>mg", "cyan"),
        )
        for i, (mode, age, expression, color) in enumerate(examples):
            x = 20 + i * 630
            self.arch(paint, mode, age, (x, 130 + 12 * sin(q * 0.7 + i), 620, 640))
            paint.equation(expression, (x + 65, 835), size=56, width=520, color=color)

    def blueprint(self, paint, time):
        q = time - CHAPTERS[1][0]
        for i, mode in enumerate(("side", "top", "front")):
            age = 0.5 + 0.4 * sin(q)
            self.arch(paint, mode, age, (35 + i * 630, 215 + 28 * sin(q * 0.9 + i), 590, 570))
        # A moving scan links the three orthogonal projections without captions.
        scan = 180 + (q * 0.35 % 1) * 690
        paint.line([(100, scan), (1820, scan)], "cyan", 1, alpha=0.3)

    def plume(self, paint, v, box, age, origin, direction, time):
        origin, direction = np.asarray(origin), np.asarray(direction)
        for i in range(16):
            q = (time * 1.8 + i / 16) % 1
            point = self.project(v, box, age, origin + direction * (0.15 + q * 2.5))
            if point:
                paint.circle(point, 1 + 3 * q, "cyan", 1, fill="white")

    def limitations(self, paint, time):
        if time >= 726.24:
            if time < 733.6:
                for i, (color, expression) in enumerate(
                    (("purple", r"\Delta p A"), ("cyan", r"\dot m v_e"), ("orange", r"\mathbf{B}\mathbf{u}"))
                ):
                    x, y = 1450, 260 + i * 205
                    paint.arc((x - 210, y + 20), 32, time, time + 4.8, color, 3)
                    paint.equation(expression, (x - 130, y - 10), size=67, width=520, color=color)
            return
        self.jet(paint, (1370, 235), "purple", 0.8)
        paint.equation(r"J=\int F\,dt<\infty", (1110, 330), size=49, width=720, color="purple")
        self.fan(paint, (1230, 550), 62, "blue")
        paint.equation(r"F_s=\Delta p A", (1360, 530), size=50, width=470, color="blue")
        center = (1240, 735)
        for radius in (21, 44, 67):
            paint.arc(center, radius, -time, -time + 5.6, "orange", 1.8)
        paint.circle((center[0] + 25 * sin(time * 2), center[1] + 12 * cos(time * 2.3)), 5, "cyan", fill="white")
        paint.equation(r"\mathbf{q}\to\mathbf{q}_{*}", (1370, 705), size=57, width=450, color="orange")


def all_expressions():
    return sorted({b.expression for beats in BEATS.values() for b in beats})
