"""Fresh core components for the approved tutorial design; callers own timing."""

import math

from faceless_champ import CLEAN_FLOW_FONT, Canvas, Circle, Group, Polyline, Rectangle, Spring

from facelesschamp_kit.coding import CodingChamp
from facelesschamp_kit.desktop import File, Folder, MacOSPreset, OSClip, OSScript, VirtualFileSystem
from facelesschamp_kit.diagrams import FlowChamp, FlowEdge, FlowGraph, FlowNode, FlowScript, FlowTheme

from .style import CodingTutorialStyle


def _rounded_outline(corners, radius=15):
    """Round a local, orthogonal silhouette using quadratic corner segments."""
    result = []
    for i, corner in enumerate(corners):
        previous, following = corners[i - 1], corners[(i + 1) % len(corners)]
        distances = (math.dist(corner, previous), math.dist(corner, following))
        inset = min(radius, *(distance / 2 for distance in distances))
        start = tuple(c + (p - c) * inset / distances[0] for c, p in zip(corner, previous))
        end = tuple(c + (p - c) * inset / distances[1] for c, p in zip(corner, following))
        for step in range(9):
            t = step / 8
            result.append(
                tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * c + t**2 * b for a, c, b in zip(start, corner, end))
            )
    return tuple(result)


class CodingTutorialTemplate:
    """Build editable visuals without lesson content, narration, execution or a scene clock."""

    def __init__(self, style=None):
        self.style = style if style is not None else CodingTutorialStyle.load()
        if not isinstance(self.style, CodingTutorialStyle):
            raise TypeError("style must be CodingTutorialStyle")
        self.workspace = self.style.workspace()
        self.window_spring = Spring(self.style.spring_stiffness, self.style.window_damping, 1)
        self.icon_spring = Spring(self.style.spring_stiffness, self.style.icon_damping, 1)

    def canvas(self):
        return Canvas(1920, 1080, self.style.background)

    def group(self, *components, bounds):
        """Fit the whole reference canvas into kit bounds, retaining child coordinates.

        Create this wrapper before scene ownership; animate its children using
        the ordinary 1920x1080 workspace coordinates. No stretching is applied.
        """
        viewport = Rectangle(
            width=1920, height=1080, position=(960, 540), fill=None, stroke=None, stroke_width=0, opacity=0
        )
        root = Group(viewport, *components)
        reference = root.bounds
        root.scale = min(bounds.width / reference.width, bounds.height / reference.height)
        root.position = bounds.center
        return root

    def finder(self, filename, source="", *, folder="Code"):
        return OSClip(
            VirtualFileSystem(Folder("root", folder, (File("source", filename, source),))),
            OSScript().select("source", at=1.10, duration=0.7, cursor=False),
            mode="finder",
            width=1280,
            height=800,
            cursor=False,
            preset=MacOSPreset(
                wallpaper=self.style.background, accent=self.style.accent, font=str(CLEAN_FLOW_FONT), font_size=28
            ),
            position=(1240, 560),
            scale=0.77,
            opacity=0,
        )

    def editor(self, source, *, filename="main.py", language="python"):
        box, unit, design = self.workspace.code_bounds, self.workspace.unit, self.workspace
        code = CodingChamp(
            source,
            language=language,
            theme=design.theme,
            chrome=False,
            font_size=design.code_size * unit,
            padding=8 * unit,
            width=box.width,
            height=box.height,
            position=(box.left, box.top),
            anchor="top_left",
            reveal=0,
        )
        caret = Rectangle(
            width=3,
            height=46 * unit,
            fill=self.style.accent,
            stroke=None,
            position=(box.left + code.code_x, box.top + code.code_y + 4),
            anchor="top_left",
        )
        window = design.window(design.editor_full, filename, children=(code, caret))
        window.position, window.scale, window.opacity = (960, 562), 0.96, 0
        return window, code, caret

    def terminal(self, text, *, title="Terminal"):
        design, unit = self.workspace, self.workspace.unit
        box = design.terminal_bounds
        code = CodingChamp(
            text,
            language="text",
            theme=design.theme,
            chrome=False,
            line_numbers=False,
            font_size=design.terminal_size * unit,
            padding=0,
            width=box.width - 48 * unit,
            height=100 * unit,
            position=(box.left + 24 * unit, box.top + 112 * unit),
            anchor="top_left",
            reveal=0,
        )
        window = design.window(box, title, children=(code,))
        window.position, window.scale, window.opacity = (box.center[0], box.center[1] + 20), 0.96, 0
        return window, code

    def flow(self, script=None):
        graph = FlowGraph(
            (
                FlowNode("source", symbol="junction", position=(380, 40), size=(12, 12)),
                FlowNode("result", symbol="junction", position=(1340, 40), size=(12, 12)),
            ),
            (FlowEdge("execution", "source", "result", route="straight"),),
            layout="manual",
        )
        script = (
            script
            if script is not None
            else (
                FlowScript()
                .reveal(("source", "result", "execution"), at=0, duration=0.30)
                .signal("execution", at=0.32, duration=1.47, marker="capsule", color=self.style.accent)
            )
        )
        return FlowChamp(
            graph,
            script,
            width=1728,
            height=80,
            position=(960, 934),
            opacity=0,
            theme=FlowTheme(
                background="#00000000",
                surface=self.style.accent,
                foreground=self.style.accent,
                accent=self.style.accent,
                stroke=self.style.connector,
                stroke_width=2,
            ),
        )

    def emblem(self):
        # Two interlocking silhouettes, authored as vectors rather than text glyphs.
        upper = (
            (-8, -142),
            (-100, -142),
            (-100, -52),
            (-20, -52),
            (-20, -30),
            (-152, -30),
            (-152, 84),
            (-108, 84),
            (-108, 10),
            (16, 10),
            (40, -14),
            (40, -142),
        )
        blue = _rounded_outline(upper)
        yellow = tuple((-x, -y) for x, y in blue)
        return Group(
            Polyline(blue, closed=True, fill=self.style.python_blue, stroke=self.style.background, stroke_width=10),
            Polyline(yellow, closed=True, fill=self.style.python_yellow, stroke=self.style.background, stroke_width=10),
            Circle(7, fill="white", stroke=None, position=(-70, -108)),
            Circle(7, fill="white", stroke=None, position=(70, 108)),
            position=(370, 568),
            scale=0.90,
            opacity=0,
        )
