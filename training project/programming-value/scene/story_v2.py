"""Source-clock cinematic diagrams. The written outline precedes this module."""

from facelesschamp_kit import BlockBuild, Video

from faceless_champ import (
    Arrow,
    Circle,
    Draw,
    Equation,
    Gauge,
    Group,
    Number,
    Polyline,
    Pulse,
    Rectangle,
    Text,
    Typewriter,
    Write,
    fit_text,
)

from .design import CHAPTERS
from .design_v2 import *


def tagged(c, role="graphic", owner="", name=""):
    c.audit_role, c.audit_owner, c.audit_name = role, owner, name
    return c


def text(words, x, y, size=40, color=WHITE, owner="", mono=False):
    return tagged(
        Text(
            words,
            font=MONO if mono else FONT,
            font_size=size,
            font_weight=None if mono else 550,
            color=color,
            position=(x, y),
        ),
        "label",
        owner,
        words,
    )


class Art:
    """Fresh owned primitives with named animation handles and semantic audit tags."""

    def __init__(self):
        self.items, self.parts, self.focus, self.paths = [], {}, [], []

    def add(self, c, name=None):
        self.items.append(c)
        if name:
            self.parts[name] = c
        return c

    def label(self, words, x, y, **kw):
        name = kw.pop("name", None)
        return self.add(text(words, x, y, **kw), name)

    def path(self, points, color=LINE, width=4, name=None, arrow=False):
        c = (
            Arrow(points[0], points[-1], stroke=color, stroke_width=width, tip_size=16)
            if arrow
            else Polyline(points, stroke=color, stroke_width=width, fill=None, line_cap="round")
        )
        self.add(tagged(c, "connector"), name)
        if name:
            self.paths.append(name)
        return c

    def node(self, label, x, y, color=SYSTEM, w=220, h=132, name=None):
        owner = name or label
        back = tagged(
            Rectangle(
                width=w,
                height=h,
                corner_radius=20,
                fill="#080C12",
                stroke=LINE,
                stroke_width=1,
                position=(x + 12, y + 14),
            ),
            "depth",
            owner,
        )
        body = tagged(
            Rectangle(width=w, height=h, corner_radius=20, fill=SURFACE, stroke=color, stroke_width=2, position=(x, y)),
            "surface",
            owner,
        )
        mark = tagged(
            Circle(radius=9, fill=color, stroke=None, position=(x - w / 2 + 26, y - h / 2 + 26)), "graphic", owner
        )
        word = tagged(
            fit_text(
                label,
                Bounds(x - w / 2 + 20, y - 28, x + w / 2 - 20, y + 46),
                font=FONT,
                font_weight=550,
                font_size=40,
                min_font_size=32,
                color=WHITE,
            ),
            "label",
            owner,
            label,
        )
        group = Group(back, body, mark, word)
        self.add(group, owner)
        self.focus.append(owner)
        return group

    def orb(self, x, y, color, name, radius=60, label=None):
        children = [
            tagged(
                Circle(radius=radius + 14, fill=None, stroke=color, stroke_width=2, opacity=0.16, position=(x, y)),
                "halo",
                name,
            ),
            tagged(Circle(radius=radius, fill=SURFACE, stroke=color, stroke_width=3, position=(x, y)), "surface", name),
            tagged(
                Circle(radius=radius - 12, fill=None, stroke=color, stroke_width=1, opacity=0.4, position=(x, y)),
                "halo",
                name,
            ),
        ]
        if label:
            children.append(text(label, x, y, color=color, owner=name))
        group = self.add(Group(*children), name)
        self.focus.append(name)
        return group

    def token(self, x, y, color=HUMAN, name="token"):
        return self.add(
            Group(
                tagged(Circle(radius=20, fill=color, stroke=None, opacity=0.12, position=(x, y)), "halo", name),
                tagged(Circle(radius=10, fill=color, stroke=None, position=(x, y)), "token", name),
            ),
            name,
        )

    def expression(self, words, colors=None, y=842):
        # A conceptual expression, positioned inside the proof rather than a title.
        terms = []
        for i, word in enumerate(words):
            color = (colors or [WHITE] * len(words))[i]
            symbol = {"→": r"\rightarrow", "≠": r"\ne"}.get(word)
            c = (
                tagged(Equation(symbol, font_size=64, color=color, fontset="stix"), "label", "expression", word)
                if symbol
                else text(word, 0, 0, size=64, color=color, owner="expression")
            )
            terms.append(c)
            self.parts[f"term-{i}"] = c
        g = Group(*terms).arrange(gap=36).move_to(960, y)
        self.add(g, "expression")
        return g

    def finish(self):
        root = Group(*self.items)
        root.audit_focus, root.audit_paths = self.focus, self.paths
        return BlockBuild(root, self.parts)


def code_art():
    a = Art()
    for i, (x, color, label) in enumerate(((500, MUTED, "Manual"), (1420, AI, "AI"))):
        owner = f"console-{i}"
        a.add(
            tagged(
                Rectangle(
                    width=660,
                    height=360,
                    corner_radius=24,
                    fill=SURFACE,
                    stroke=color,
                    stroke_width=2,
                    position=(x, 480),
                ),
                "surface",
                owner,
            )
        )
        a.label(label, x, 254, color=color)
        a.path(((x - 280, 350), (x + 280, 350)), color=LINE, width=2)
        rows = ["def build(idea):", "    parts = connect(idea)", "    test(parts)", "    return system"]
        for j, row in enumerate(rows):
            c = text(row, x, 397 + j * 57, size=34, color=color if j in (0, 3) else WHITE, owner=owner, mono=True)
            a.add(c, f"code-{i}-{j}")
        a.add(
            tagged(Rectangle(width=12, height=32, fill=color, stroke=None, position=(x - 280, 640)), "token", owner),
            f"cursor-{i}",
        )
        a.focus.append(f"cursor-{i}")
    a.expression(["code", "≠", "purpose"], [AI, WHITE, HUMAN])
    return a.finish()


def flow_art(labels=("Request", "Data", "Sheet", "Invoice", "Follow-up"), feedback=False):
    a = Art()
    n = len(labels)
    xs = [260 + i * 1400 / (n - 1) for i in range(n)]
    for i in range(n - 1):
        a.path(((xs[i] + 118, 500), (xs[i + 1] - 122, 500)), color=SYSTEM, name=f"edge-{i}", arrow=True)
    for i, (x, label) in enumerate(zip(xs, labels)):
        a.node(label, x, 500, name=f"node-{i}", w=220)
        # Isometric inset document: separate graphic above each stage.
        a.add(
            tagged(
                Polyline(
                    ((x - 28, 324), (x + 28, 308), (x + 54, 325), (x - 2, 343), (x - 28, 324)),
                    stroke=SYSTEM,
                    stroke_width=2,
                    fill="#05241B",
                    closed=True,
                ),
                "graphic",
                f"node-{i}",
            )
        )
    a.path(((xs[0], 702), (xs[-1], 702)), color=LINE, width=2)
    a.token(xs[0], 702)
    if feedback:
        a.path(((xs[-1], 575), (xs[-1], 790), (xs[0], 790), (xs[0], 575)), color=HUMAN, name="feedback")
    a.expression(["parts", "→", "system"], [MUTED, WHITE, SYSTEM], y=902)
    return a.finish()


def scale_art():
    a = Art()
    for i, (x, label, color, prefix, value) in enumerate(
        ((420, "Data", SYSTEM, "×", 1), (960, "Users", AI, "", 10), (1500, "Cost", HUMAN, "$", 1))
    ):
        beginning = len(a.items)
        owner = f"metric-{i}"
        a.add(
            tagged(
                Rectangle(
                    width=440,
                    height=450,
                    corner_radius=24,
                    fill=SURFACE,
                    stroke=LINE,
                    stroke_width=2,
                    position=(x, 530),
                ),
                "surface",
                owner,
            )
        )
        a.label(label, x, 375, color=color, owner=owner)
        number = tagged(
            Number(
                value,
                prefix=prefix,
                font=FONT,
                font_weight=600,
                font_size=62,
                width=380,
                color=color,
                position=(x, 510),
            ),
            "label",
            owner,
            label,
        )
        a.add(number, f"value-{i}")
        a.focus.append(f"value-{i}")
        for j in range(12):
            a.add(
                tagged(
                    Rectangle(
                        width=20,
                        height=34 + (j % 4) * 18,
                        corner_radius=3,
                        fill=color,
                        stroke=None,
                        opacity=0.22,
                        position=(x - 165 + j * 30, 664),
                    ),
                    "graphic",
                    owner,
                ),
                f"bar-{i}-{j}",
            )
        members = a.items[beginning:]
        a.items[beginning:] = [Group(*members)]
        a.parts[f"metric-{i}"] = a.items[-1]
    a.label("Hypothetical scale", 960, 880, size=32, color=MUTED)
    return a.finish()


def questions_art():
    a = Art()
    labels = ("Audience", "Problem", "Data", "Mistakes", "Cost", "Growth", "Restraint")
    coords = ((360, 300), (760, 300), (1160, 300), (1560, 300), (460, 700), (960, 700), (1460, 700))
    for i, (label, (x, y)) in enumerate(zip(labels, coords)):
        dx, dy = x - 960, y - 500
        length = (dx * dx + dy * dy) ** 0.5
        ux, uy = dx / length, dy / length
        distance = min(143 / abs(ux) if ux else float("inf"), 68 / abs(uy) if uy else float("inf"))
        a.path(((960 + ux * 90, 500 + uy * 90), (x - ux * distance, y - uy * distance)), color=LINE, name=f"edge-{i}")
    a.orb(960, 500, AI, "model", radius=72, label="AI")
    for i, (label, (x, y)) in enumerate(zip(labels, coords)):
        a.node(label, x, y, HUMAN, w=270, h=120, name=f"node-{i}")
    a.expression(["questions", "→", "useful"], [HUMAN, WHITE, SYSTEM], y=910)
    return a.finish()


def human_art():
    a = Art()
    for i, (label, x, y) in enumerate(
        (("Needs", 410, 300), ("People", 1510, 300), ("Responsibility", 410, 700), ("Consequences", 1510, 700))
    ):
        a.path(
            ((x + (160 if x < 960 else -160), y), (760 if x < 960 else 1160, y), (800 if x < 960 else 1120, 500)),
            color=HUMAN,
            name=f"edge-{i}",
        )
        a.node(label, x, y, HUMAN, w=330, h=116, name=f"node-{i}")
    # Human silhouette inside an illuminated decision ring.
    a.orb(960, 500, HUMAN, "decision", radius=134)
    a.add(tagged(Circle(radius=28, fill=HUMAN, stroke=None, position=(960, 458)), "graphic", "decision"))
    a.add(
        tagged(
            Polyline(
                ((901, 559), (918, 516), (960, 497), (1002, 516), (1019, 559)),
                stroke=HUMAN,
                stroke_width=12,
                line_cap="round",
            ),
            "graphic",
            "decision",
        )
    )
    a.expression(["context", "→", "judgment"], [HUMAN, WHITE, HUMAN], y=910)
    return a.finish()


def complexity_art(resolved=False):
    a = Art()
    xs = [(-165, -115), (-40, -165), (115, -120), (180, 10), (100, 160), (-50, 150), (-170, 65), (0, 0)]
    for i in range(len(xs)):
        for j in range(i + 1, len(xs)):
            if (i + j) % 3 == 0:
                a.path(
                    ((460 + xs[i][0], 485 + xs[i][1]), (460 + xs[j][0], 485 + xs[j][1])),
                    color=LINE,
                    width=2,
                    name=f"tangle-{i}-{j}",
                )
    for i, (x, y) in enumerate(xs):
        a.orb(460 + x, 485 + y, ERROR, f"knot-{i}", radius=17)
    a.label("Complexity", 460, 748, color=ERROR)
    a.items = [Group(*a.items)]
    a.parts["tangle"] = a.items[0]
    a.path(((740, 500), (1110, 500)), color=HUMAN, width=5, name="bridge", arrow=True)
    assembly_start = len(a.items)
    for i, (x, y) in enumerate(((1290, 380), (1530, 380), (1290, 620), (1530, 620))):
        owner = f"module-{i}"
        # A clean isometric assembly replaces a pile of unrelated fragments.
        for depth in (32, 16, 0):
            a.add(
                tagged(
                    Polyline(
                        (
                            (x - 78, y - 38 + depth),
                            (x, y - 76 + depth),
                            (x + 78, y - 38 + depth),
                            (x + 78, y + 38 + depth),
                            (x, y + 76 + depth),
                            (x - 78, y + 38 + depth),
                        ),
                        closed=True,
                        fill=SURFACE,
                        stroke=SYSTEM if depth == 0 else LINE,
                        stroke_width=2,
                    ),
                    "graphic",
                    owner,
                )
            )
        a.add(tagged(Circle(radius=13, fill=SYSTEM, stroke=None, position=(x, y)), "graphic", owner), owner)
        a.focus.append(owner)
    a.path(((1290, 472), (1290, 530)), color=SYSTEM, name="join-0")
    a.path(((1530, 472), (1530, 530)), color=SYSTEM, name="join-1")
    a.path(((1372, 380), (1448, 380)), color=SYSTEM, name="join-2")
    a.path(((1372, 620), (1448, 620)), color=SYSTEM, name="join-3")
    a.label("Useful system", 1410, 808, color=SYSTEM)
    members = a.items[assembly_start:]
    a.items[assembly_start:] = [Group(*members)]
    a.parts["assembly"] = a.items[-1]
    a.expression(["understand", "→", "build"], [HUMAN, WHITE, SYSTEM], y=916)
    a.focus = [f"module-{i}" for i in range(4)]
    return a.finish()


def claims_art():
    a = Art()
    for i, (label, x) in enumerate((("Programming", 430), ("Developers", 960), ("Learning", 1490))):
        a.orb(x, 455, ERROR, f"claim-{i}", radius=90, label="?")
        a.label(label, x, 650, color=WHITE)
    a.expression(["code", "≠", "understanding"], [AI, WHITE, HUMAN])
    return a.finish()


def economics_art():
    a = Art()
    for i, (cx, label, color, up) in enumerate(
        ((510, "Production cost", AI, False), (1410, "Decision importance", HUMAN, True))
    ):
        a.path(((cx - 285, 310), (cx - 285, 702), (cx + 290, 702)), color=LINE, width=2)
        points = []
        for k in range(41):
            t = k / 40
            y = 640 - 260 * (1 - (1 - t) ** 2) if up else 380 + 260 * (1 - (1 - t) ** 2)
            points.append((cx - 245 + 490 * t, y))
        a.path(points, color=color, width=6, name=f"curve-{i}")
        a.label(label, cx, 238, color=color)
        a.token(*points[0], color=color, name=f"token-{i}")
        a.focus.append(f"token-{i}")
    a.label("Conceptual relationship", 960, 907, size=32, color=MUTED)
    return a.finish()


def app(a, x, y, name, color=AI):
    a.add(
        tagged(
            Rectangle(
                width=530, height=350, corner_radius=24, fill=SURFACE, stroke=color, stroke_width=2, position=(x, y)
            ),
            "surface",
            name,
        )
    )
    a.path(((x - 230, y - 110), (x + 230, y - 110)), color=LINE, width=2)
    for k in range(3):
        a.add(tagged(Circle(radius=5, fill=color, stroke=None, position=(x - 225 + k * 22, y - 140)), "graphic", name))
    for k, height in enumerate((55, 98, 143)):
        a.add(
            tagged(
                Rectangle(
                    width=54,
                    height=height,
                    corner_radius=5,
                    fill=color,
                    stroke=None,
                    opacity=0.7,
                    position=(x - 158 + k * 84, y + 67 - height / 2),
                ),
                "graphic",
                name,
            ),
            f"{name}-bar-{k}",
        )
    a.add(
        tagged(
            Rectangle(width=146, height=36, corner_radius=8, fill=color, stroke=None, position=(x + 125, y - 46)),
            "graphic",
            name,
        )
    )
    for k in range(3):
        a.path(((x + 54, y + 15 + k * 32), (x + 198, y + 15 + k * 32)), color=LINE, width=4)
    a.focus.append(f"{name}-bar-2")


def apps_art(wrong=False):
    a = Art()
    app(a, 480, 445, "app-left", AI)
    app(a, 1440, 445, "app-right", SYSTEM)
    a.label("Works", 480, 214, color=AI)
    a.label("Useful", 1440, 214, color=SYSTEM)
    for x, color, name, hit in ((480, ERROR, "need-left", False), (1440, SYSTEM, "need-right", True)):
        a.path(((x, 627), (x, 708)), color=color, name=f"edge-{name}", arrow=True)
        a.orb(x, 776, color, name, radius=54, label="✓" if hit else "×")
        a.label("Real need", x + 166, 776, size=32, color=MUTED)
    a.expression(["works", "≠", "useful"], [AI, WHITE, SYSTEM], y=917)
    return a.finish()


def network_art(labels=("Input", "Output", "Data", "Feedback", "Constraint", "Design"), center="System", color=SYSTEM):
    a = Art()
    # Routes end at node boundaries; no connector passes through labels.
    coords = [(420, 275), (960, 245), (1500, 275), (420, 720), (960, 750), (1500, 720)]
    for i, (x, y) in enumerate(coords[: len(labels)]):
        sx, sy = 960, 500
        dx, dy = x - sx, y - sy
        length = (dx * dx + dy * dy) ** 0.5
        a.path(
            ((sx + dx / length * 112, sy + dy / length * 112), (x - dx / length * 145, y - dy / length * 90)),
            color=LINE,
            name=f"edge-{i}",
        )
    a.orb(960, 500, color, "core", radius=100, label=center)
    for i, (label, (x, y)) in enumerate(zip(labels, coords)):
        a.node(label, x, y, color, w=280, h=112, name=f"node-{i}")
    a.expression(["structure", "→", "possibility"], [color, WHITE, HUMAN], y=925)
    return a.finish()


def machine_art():
    a = Art()
    # Layered code apparatus: input, functions and storage become software.
    a.orb(275, 500, AI, "input", radius=65, label="in")
    for i, (x, label) in enumerate(((630, "Loops"), (1030, "Functions"), (1430, "Data"))):
        a.node(label, x, 460, AI, w=260, h=148, name=f"node-{i}")
        a.path(((x - 88, 575), (x - 88, 656), (x + 88, 656), (x + 88, 575)), color=AI, name=f"loop-{i}")
        a.label(("repeat()", "transform()", "store()")[i], x, 741, size=34, color=AI, mono=True)
    for i, (left, right) in enumerate(((345, 490), (770, 890), (1170, 1290), (1570, 1660))):
        a.path(((left, 460), (right, 460)), color=AI, name=f"edge-{i}", arrow=True)
    a.orb(1730, 460, SYSTEM, "output", radius=55, label="✓")
    a.expression(["instructions", "→", "software"], [AI, WHITE, SYSTEM], y=925)
    return a.finish()


def compression_art():
    a = Art()
    for i, (label, y) in enumerate((("Docs", 300), ("Debug", 500), ("Boilerplate", 700))):
        a.node(label, 390, y, AI, w=290, h=112, name=f"node-{i}")
        a.path(((548, y), (720, y), (830, 500)), color=AI, name=f"edge-{i}")
        a.token(625, y, AI, name=f"token-{i}")
    a.orb(960, 500, HUMAN, "prompt", radius=100, label="Prompt")
    a.path(((1077, 500), (1290, 500)), color=SYSTEM, name="out", arrow=True)
    a.node("System", 1470, 500, SYSTEM, w=320, h=200, name="system")
    a.expression(["mechanics", "→", "intent"], [AI, WHITE, HUMAN], y=922)
    return a.finish()


def duplicate_art():
    a = Art()
    for row, y in enumerate((380, 660)):
        for i, (x, label) in enumerate(((420, "Enter"), (960, "Copy" if row == 0 else "Enter"), (1500, "Deliver"))):
            a.node(label, x, y, ERROR if i == 1 else SYSTEM, w=260, h=112, name=f"node-{row}-{i}")
            if i < 2:
                a.path(
                    ((x + 145, y), (x + 390, y)), color=ERROR if i == 0 else LINE, name=f"edge-{row}-{i}", arrow=True
                )
        a.token(620, y, ERROR, name=f"token-{row}")
    a.path(((960, 449), (960, 589)), color=ERROR, name="duplicate", width=3)
    a.label("Same data", 1190, 520, color=ERROR)
    a.expression(["repeat", "→", "redesign"], [ERROR, WHITE, HUMAN], y=925)
    return a.finish()


def resources_art():
    a = Art()
    for i, (x, label, color, p) in enumerate(
        ((430, "Time", AI, 0.8), (960, "Memory", SYSTEM, 0.45), (1490, "Resources", HUMAN, 0.65))
    ):
        a.add(
            tagged(
                Gauge(
                    width=310, height=240, progress=p, color=color, track_color=LINE, stroke_width=14, position=(x, 440)
                ),
                "graphic",
                f"gauge-{i}",
            ),
            f"gauge-{i}",
        )
        a.label(label, x, 620, color=color)
        a.focus.append(f"gauge-{i}")
        a.node(("Fast", "Lean", "Scalable")[i], x, 752, color, w=220, h=102, name=f"node-{i}")
    a.expression(["trade-offs", "→", "choice"], [MUTED, WHITE, HUMAN], y=920)
    return a.finish()


def process_art():
    a = Art()
    for i, (label, x) in enumerate((("Simplify", 350), ("Delegate", 760), ("Automate", 1170), ("Eliminate", 1580))):
        a.label(label, x, 290, color=HUMAN)
        for j in range(3):
            a.orb(x, 425 + j * 130, SYSTEM if i != 3 else ERROR, f"step-{i}-{j}", radius=32)
            if j < 2:
                a.path(((x, 473 + j * 130), (x, 505 + j * 130)), color=LINE, name=f"edge-{i}-{j}")
        if i == 1:
            a.path(((x + 55, 425), (x + 112, 425), (x + 112, 685), (x + 55, 685)), color=HUMAN, name="delegate")
        if i == 2:
            a.path(((x + 55, 425), (x + 112, 425), (x + 112, 685), (x + 55, 685)), color=AI, name="automate")
    a.expression(["less waste", "→", "more value"], [ERROR, WHITE, SYSTEM], y=925)
    return a.finish()


def two_users_art():
    a = Art()
    a.orb(960, 260, AI, "model", radius=85, label="AI")
    for i, x in enumerate((470, 1450)):
        a.path(((960, 360), (960, 395), (x, 395), (x, 454)), color=AI, name=f"edge-{i}")
        app(a, x, 645, f"app-{i}", AI if i == 0 else SYSTEM)
        a.label("Generate" if i == 0 else "Understand", x, 900, color=AI if i == 0 else HUMAN)
    return a.finish()


def professions_art():
    a = Art()
    a.orb(960, 525, AI, "core", radius=54, label="AI")
    for i, (x, y) in enumerate(((490, 350), (1430, 350), (490, 695), (1430, 695))):
        a.path(
            ((960 + (65 if x > 960 else -65), 525), (x, y + (120 if y < 525 else -120))), color=LINE, name=f"edge-{i}"
        )
    for i, (label, x, y) in enumerate(
        (("Researcher", 490, 350), ("Designer", 1430, 350), ("Creator", 490, 695), ("Entrepreneur", 1430, 695))
    ):
        beginning = len(a.items)
        color = (SYSTEM, AI, AI, HUMAN)[i]
        a.orb(x, y, color, f"icon-{i}", radius=100)
        if i == 0:
            a.path(
                (
                    (x - 25, y - 57),
                    (x - 25, y - 15),
                    (x - 62, y + 53),
                    (x + 62, y + 53),
                    (x + 25, y - 15),
                    (x + 25, y - 57),
                ),
                color=color,
                width=5,
                name="flask",
            )
            a.path(((x - 42, y + 22), (x + 42, y + 22)), color=color, width=4)
        elif i == 1:
            a.add(
                tagged(
                    Rectangle(width=108, height=90, fill=None, stroke=color, stroke_width=4, position=(x, y)),
                    "graphic",
                    f"icon-{i}",
                )
            )
            a.path(((x - 44, y + 29), (x - 8, y - 12), (x + 15, y + 7), (x + 47, y - 34)), color=color, width=4)
        elif i == 2:
            a.path(((x - 47, y - 50), (x + 49, y), (x - 47, y + 50), (x - 47, y - 50)), color=color, width=5)
        else:
            for j in range(3):
                a.add(
                    tagged(
                        Rectangle(
                            width=22,
                            height=35 + j * 25,
                            fill=color,
                            stroke=None,
                            position=(x - 40 + j * 40, y + 30 - (35 + j * 25) / 2),
                        ),
                        "graphic",
                        f"icon-{i}",
                    )
                )
        a.label(label, x + 240, y, size=40, color=color)
        members = a.items[beginning:]
        a.items[beginning:] = [Group(*members)]
        a.parts[f"profession-{i}"] = a.items[-1]
    return a.finish()


def choose_art():
    a = Art()
    for i, (x, label, color) in enumerate(((480, "Solve", AI), (1440, "Choose", HUMAN))):
        a.orb(x, 500, color, f"target-{i}", radius=155)
        for radius in (100, 48):
            a.add(
                tagged(
                    Circle(radius=radius, fill=None, stroke=color, stroke_width=3, position=(x, 500)),
                    "graphic",
                    f"target-{i}",
                )
            )
        a.token(x, 500, color, name=f"token-{i}")
        a.label(label, x, 255, color=color)
        a.label("Specified problem" if i == 0 else "Worthwhile problem", x, 754, color=MUTED)
    a.expression(["solve", "≠", "choose"], [AI, WHITE, HUMAN], y=924)
    return a.finish()


def goal_art():
    a = Art()
    a.orb(360, 500, HUMAN, "human", radius=86, label="Why?")
    a.orb(960, 500, AI, "model", radius=100, label="AI")
    a.node("Useful", 1540, 500, SYSTEM, w=300, h=200, name="outcome")
    a.path(((466, 500), (842, 500)), color=HUMAN, width=5, name="intent", arrow=True)
    a.path(((1078, 500), (1373, 500)), color=AI, width=5, name="code", arrow=True)
    a.path(((360, 795), (1540, 795)), color=LINE, width=2)
    a.token(500, 795, HUMAN)
    a.label("Goal", 360, 720, color=HUMAN)
    a.label("Code", 960, 720, color=AI)
    a.label("Outcome", 1540, 720, color=SYSTEM)
    a.expression(["intention", "→", "system"], [HUMAN, WHITE, SYSTEM], y=916)
    return a.finish()


INTRO = [
    (0, 3, "code"),
    (3, 6, "flow"),
    (6, 9, "scale"),
    (9, 12, "questions"),
    (12, 15, "human"),
    (15, 18, "complexity"),
    (18, 21, "claims"),
    (21, 24.4, "apps"),
]
FACTORIES = {
    "code": code_art,
    "flow": flow_art,
    "scale": scale_art,
    "questions": questions_art,
    "human": human_art,
    "complexity": complexity_art,
    "claims": claims_art,
    "economics": economics_art,
    "apps": apps_art,
    "network": network_art,
    "machine": machine_art,
    "compression": compression_art,
    "duplicate": duplicate_art,
    "resources": resources_art,
    "process": process_art,
    "two_users": two_users_art,
    "professions": professions_art,
    "choose": choose_art,
    "goal": goal_art,
}
FACTORIES["closing"] = complexity_art

# (first source cue, following cue, diagram, optional parameters, delayed reveals)
# Every interval is from outline-v2.md, not estimated from word counts.
SHOTS = {
    "code-value": [
        (68, 106, "two_users", {}, ()),
        (106, 173, "machine", {}, ((117, "input"), (131, "node-0"), (135, "node-1"), (141, "node-2"), (147, "output"))),
        (173, 210, "compression", {}, ((177, "node-0"), (191, "node-1"), (193, "node-2"), (201, "prompt"))),
        (210, 232, "economics", {}, ()),
        (232, 258, "apps", {}, ()),
        (
            258,
            300,
            "network",
            {"labels": ("Problem", "Connect", "Failure", "Design"), "center": "Think", "color": HUMAN},
            ((262, "node-0"), (267, "node-1"), (273, "node-2"), (280, "node-3")),
        ),
        (300, 306, "goal", {}, ()),
    ],
    "systems": [
        (
            306,
            339,
            "network",
            {"labels": ("Input", "Output", "Dependency", "Feedback", "Constraint", "Structure")},
            (),
        ),
        (339, 380, "flow", {}, ((345, "node-0"), (349, "node-1"), (351, "node-2"), (353, "node-3"), (356, "node-4"))),
        (380, 410, "flow", {}, ()),
        (410, 440, "duplicate", {}, ()),
        (440, 477, "flow", {"labels": ("Enter once", "Transform", "Deliver"), "feedback": True}, ()),
    ],
    "optimization": [
        (477, 506, "flow", {"labels": ("Input", "Correct", "Scale?")}, ()),
        (506, 539, "scale", {}, ((506, "metric-0"), (518, "metric-1"), (526, "metric-2"))),
        (539, 558, "resources", {}, ()),
        (558, 591, "network", {"labels": ("Work", "Repeat", "Patterns", "Decisions"), "center": "Process"}, ()),
        (591, 620, "process", {}, ()),
    ],
    "better-questions": [
        (620, 664, "two_users", {}, ()),
        (
            664,
            718,
            "questions",
            {},
            (
                (674, "node-0"),
                (680, "node-1"),
                (685, "node-2"),
                (691, "node-3"),
                (699, "node-4"),
                (703, "node-5"),
                (709, "node-6"),
            ),
        ),
        (718, 771, "flow", {"labels": ("Ask", "Compare", "Evaluate")}, ()),
        (
            771,
            814,
            "network",
            {"labels": ("Production", "Thinking", "Reliable", "Secure", "Complex"), "center": "Skill", "color": AI},
            ((780, "node-0"), (790, "node-1"), (809, "node-2"), (810, "node-3"), (812, "node-4")),
        ),
        (
            814,
            870,
            "professions",
            {},
            ((828, "profession-0"), (836, "profession-1"), (847, "profession-2"), (857, "profession-3")),
        ),
        (870, 903, "flow", {"labels": ("Idea", "Prototype", "System")}, ()),
    ],
    "human-judgment": [
        (903, 924, "goal", {}, ()),
        (
            924,
            969,
            "network",
            {
                "labels": ("Generate", "Analyze", "Architecture", "Patterns", "Create", "Improve"),
                "center": "AI",
                "color": AI,
            },
            ((926, "node-0"), (928, "node-1"), (931, "node-2"), (933, "node-3"), (937, "node-4"), (965, "node-5")),
        ),
        (969, 987, "choose", {}, ()),
        (987, 1042, "human", {}, ((1003, "node-0"), (1010, "node-1"), (1015, "node-2"), (1027, "node-3"))),
        (1042, 1077, "apps", {}, ()),
        (1077, 1102, "goal", {}, ()),
    ],
    "useful-systems": [
        (1102, 1160, "economics", {}, ()),
        (1160, 1198, "two_users", {}, ()),
        (1198, 1247, "complexity", {}, ()),
        (
            1247,
            1293,
            "network",
            {"labels": ("Systems", "Patterns", "Design", "Optimize"), "center": "Think", "color": HUMAN},
            ((1276, "node-0"), (1281, "node-1"), (1286, "node-2"), (1291, "node-3")),
        ),
        (1293, 1329, "goal", {}, ()),
        (1329, None, "closing", {}, ()),
    ],
}


def place(segment, start, end, kind, events, factory=None, reveals=(), voice=None, cue_range=None):
    """Absolute source windows; no accumulated waits or rebased narration."""
    local = start - segment.start
    life = end - start
    build = (factory or FACTORIES[kind])()
    reveal_times = {name: voice.track.cue(cue).start for cue, name in reveals}
    for name in reveal_times:
        build.children[name].opacity = 0
    for name, component in build.children.items():
        if name.startswith("term-"):
            component.opacity = 0
    h = segment.add_core(
        lambda ctx, box: build, at=local, duration=life, bounds=SAFE, enter="fade", enter_duration=min(0.35, life / 4)
    )
    focus = build.root.audit_focus

    def members(component):
        yield component
        if isinstance(component, Group):
            for child in component.children:
                yield from members(child)

    visible_after = {
        name: max([start] + [t for parent, t in reveal_times.items() if child in set(members(build.children[parent]))])
        for name, child in build.children.items()
    }
    event_times = [start]
    for name, component in build.children.items():
        if name.startswith("term-"):
            t = local + 0.15 + int(name.split("-")[1]) * 0.12
            segment.play(h[name], lambda c: c.animate.opacity_to(1), at=t, duration=0.3)
            if isinstance(component, Equation):
                segment.play(h[name], Write, at=t, duration=0.3)
    for name, t in reveal_times.items():
        segment.play(h[name], lambda c: c.animate.opacity_to(1), at=t - segment.start, duration=min(0.45, end - t))
        event_times.append(t)
    # Gentle push-in for graphics, leaving labels at their carefully measured positions.
    if kind in ("complexity", "closing", "choose", "human"):
        for name in ("decision", "target-0", "target-1", "module-0", "module-1", "module-2", "module-3"):
            if name in build.children:
                segment.play(h[name], lambda c: c.animate.scale_to(1.025), at=local + 0.05, duration=0.35)
    for j, t in enumerate([start + 0.6 + k * 2.6 for k in range(int(max(0, life - 0.8) / 2.6) + 1)]):
        if t + 0.6 >= end:
            continue
        available = [name for name in focus if visible_after[name] <= t]
        if not available:
            available = [
                name
                for name in build.children
                if visible_after[name] <= t and name not in build.root.audit_paths and name != "expression"
            ]
        if not available:
            available = ["expression"]
        name = available[j % len(available)]
        segment.play(h[name], lambda c: Pulse(c, factor=1.035), at=t - segment.start, duration=0.55)
        event_times.append(t)
    for j, name in enumerate(build.root.audit_paths):
        at = local + 0.12 + j * 0.08
        if at + 0.55 <= local + life:
            segment.play(h[name], Draw, at=at, duration=0.55)
    if kind == "code":
        for i in range(2):
            for j in range(4):
                segment.play(
                    h[f"code-{i}-{j}"], Typewriter, at=local + 0.2, duration=min(life - 0.4, 1.9 if i == 0 else 0.7)
                )
    if kind == "flow":
        # Token motion is divided into readable arrivals at each stage.
        stops = len(build.root.audit_focus)
        travel = max(0.4, (life - 0.9) / max(1, stops - 1))
        for i in range(1, stops):
            t = local + 0.6 + (i - 1) * travel
            segment.play(
                h["token"],
                lambda c, x=260 + i * 1400 / (stops - 1): c.animate.move_to(x, 702),
                at=t,
                duration=min(travel * 0.8, local + life - t - 0.05),
            )
    if kind == "scale":
        for i, (value, cue) in enumerate(((1000, 516), (10000000, 524), (1000, 537))):
            change = voice.track.cue(cue).start - segment.start if cue_range else local + 0.35
            segment.play(
                h[f"value-{i}"],
                lambda c, v=value: c.animate.value_to(v),
                at=change,
                duration=min(0.65, local + life - change - 0.05),
            )
            event_times.append(change + segment.start)
            for j in range(12):
                segment.play(
                    h[f"bar-{i}-{j}"],
                    lambda c: c.animate.opacity_to(0.85),
                    at=change,
                    duration=min(0.65, local + life - change - 0.05),
                )
    if kind == "economics":
        for i in range(2):
            for k in range(1, 9):
                t = k / 8
                cx = (510, 1410)[i]
                y = 640 - 260 * (1 - (1 - t) ** 2) if i else 380 + 260 * (1 - (1 - t) ** 2)
                at = local + 0.6 + (k - 1) * (life - 0.9) / 8
                segment.play(
                    h[f"token-{i}"],
                    lambda c, x=cx - 245 + 490 * t, y=y: c.animate.move_to(x, y),
                    at=at,
                    duration=(life - 0.9) / 8 * 0.88,
                )
    if kind == "resources":
        for i, target in enumerate((0.48, 0.75, 0.35)):
            segment.play(
                h[f"gauge-{i}"],
                lambda c, p=target: c.animate.progress_to(p),
                at=local + 0.6,
                duration=min(1.2, life - 0.9),
            )
    if kind == "process":
        for i, cue in enumerate((599, 600, 601, 603)):
            at = voice.track.cue(cue).start - segment.start if voice else local + 0.5
            if i in (0, 3):
                for j in (1,) if i == 0 else (0, 1, 2):
                    segment.play(h[f"step-{i}-{j}"], lambda c: c.animate.opacity_to(0.08), at=at, duration=0.65)
            elif i == 1:
                segment.play(h["step-1-1"], lambda c: c.animate.move_to(872, 555), at=at, duration=0.65)
            else:
                segment.play(h["step-2-1"], lambda c: c.animate.scale_to(1.3), at=at, duration=0.65)
            event_times.append(at + segment.start)
    if kind == "goal":
        segment.play(h["token"], lambda c: c.animate.move_to(1300, 795), at=local + 0.6, duration=max(0.4, life - 0.9))
    if kind in ("complexity", "closing"):
        # Tangle contracts while the stable modular system grows clearer.
        for i in range(8):
            segment.play(
                h[f"knot-{i}"], lambda c: c.animate.scale_to(0.55), at=local + 0.5, duration=min(1.1, life - 0.8)
            )
    if kind == "closing":
        at = voice.track.cue(1344).start - segment.start
        segment.play(h["tangle"], lambda c: c.animate.opacity_to(0), at=at, duration=0.7)
        segment.play(h["bridge"], lambda c: c.animate.opacity_to(0), at=at, duration=0.7)
        shift = voice.track.cue(1349).start - segment.start
        part = build.children["assembly"]
        _x, y = part.position
        segment.play(h["assembly"], lambda c, y=y: c.animate.move_to(960, y), at=shift, duration=1.15)
        event_times.extend([at + segment.start, shift + segment.start])
    events.append(
        {
            "kind": kind,
            "start": start,
            "end": end,
            "cues": cue_range,
            "attention": sorted(set(event_times)),
            "reveals": reveal_times,
        }
    )


def build(ctx, image_mode="auto"):
    video = Video(ctx)
    voice = video.narration(
        audio="audio.mp3",
        subtitles="cue-per-word.srt",
        markers={name: first for name, first, _ in CHAPTERS},
        captions=False,
        overlap_tolerance=0.001,
    )
    events = []
    for name, first, following in CHAPTERS:
        start = 0 if first == 1 else voice.track.cue(first).start
        end = voice.track.cue(following).start if following else voice.duration
        segment = video.segment(name, start=start, duration=end - start)
        if first == 1:
            for left, right, kind in INTRO:
                place(segment, left, right, kind, events)
        for cue, following_cue, kind, params, reveals in SHOTS[name]:
            left = voice.track.cue(cue).start
            right = voice.track.cue(following_cue).start if following_cue else voice.duration
            place(
                segment,
                left,
                right,
                kind,
                events,
                factory=lambda k=kind, p=params: FACTORIES[k](**p),
                reveals=reveals,
                voice=voice,
                cue_range=[cue, following_cue],
            )
    video.visual_events = events
    return video
