"""Three canvases, ten staggered panels, two crossfades, exactly one minute."""

from faceless_champ import Canvas, Circle, ColorScheme, FadeIn, Grid, Layer, Line, Rectangle, Scene, Sequence, SlideIn

from .equations import EQUATIONS
from .panels import EquationPanel
from .style import DEFAULT_SCHEME, SFX, TRANSPARENT, text

CROSSFADE = 0.6
PADDING = (214, 70, 90, 70)
GAP = 22
CHAPTERS = (
    {
        "title": "Foundations",
        "subtitle": "Distance, roots, steepness, and growth.",
        "duration": 24.6,
        "indices": (0, 1, 2, 3),
        "starts": (0.85, 6.45, 12.05, 17.65),
    },
    {
        "title": "Change & chance",
        "subtitle": "Rates, accumulation, motion, and evidence.",
        "duration": 24.6,
        "indices": (4, 5, 6, 7),
        "starts": (0.6, 6.2, 11.8, 17.4),
    },
    {
        "title": "Patterns",
        "subtitle": "Variation and frequencies: two ways to understand the world.",
        "duration": 12.0,
        "indices": (8, 9),
        "starts": (0.6, 5.8),
    },
)


class ChapterBackdrop(Scene):
    def __init__(self, chapter, index, *, sound=True, scheme=DEFAULT_SCHEME):
        super().__init__(Canvas(1920, 1080, scheme.background))
        self.chapter, self.index, self.sound = chapter, index, sound
        self.scheme = scheme

    def construct(self):
        chapter, index = self.chapter, self.index
        scheme = self.scheme
        specs = [EQUATIONS[i] for i in chapter["indices"]]
        # A restrained dotted field gives the canvas texture without a bitmap.
        for x in range(70, 1900, 48):
            for y in (22, 198, 1005):
                self.add(Circle(0.8, fill=scheme.grid, stroke=None, position=(x, y)))
        self.add(text("MATH / A PRACTICAL TOOLKIT", (74, 34), size=16, color=scheme.muted, anchor="top_left"))
        title = text("10 most useful equations", (70, 64), size=66, anchor="top_left", scheme=scheme, font_weight=600)
        subtitle = text(chapter["subtitle"], (75, 151), size=24, color=scheme.muted, body=True, anchor="top_left")
        with self.at(0.04):
            self.play(SlideIn(title, distance=20), run_time=0.55)
        with self.at(0.20):
            self.play(FadeIn(subtitle), run_time=0.5)
        self.add(text(f"0{index + 1}", (1708, 105), size=112, color=scheme.border))
        self.add(text(chapter["title"].upper(), (1708, 169), size=17, color=specs[0].accent(scheme)))
        self.add(Line(1780, stroke=scheme.border, stroke_width=1, position=(960, 193)))
        tall, height = index == 2, 776 if index == 2 else 377
        # These empty plates remain visible before a delayed Grid child appears.
        for slot, spec in enumerate(specs):
            x, y = 70 + (slot % 2) * 901, 214 + (slot // 2) * 399
            self.add(
                Rectangle(
                    width=869,
                    height=height - 10,
                    corner_radius=20,
                    stroke=scheme.grid,
                    stroke_width=1.5,
                    position=(x + 439.5, y + height / 2),
                )
            )
            self.add(text(f"{spec.number:02d}", (x + 40, y + 34), size=25, color=scheme.axis, anchor="top_left"))
        self.add(
            text(
                f"{specs[0].number:02d}—{specs[-1].number:02d} / 10",
                (75, 1031),
                size=21,
                color=scheme.muted,
                anchor="top_left",
            )
        )
        self.add(text("USEFUL IDEAS. BEAUTIFUL CONNECTIONS.", (960, 1040), size=17, color=scheme.muted))
        self.add(text("2 × 1" if tall else "2 × 2", (1804, 1040), size=19, color=scheme.muted))
        for slot, (spec, start) in enumerate(zip(specs, chapter["starts"])):
            with self.at(start):
                marker = Circle(3, fill=spec.accent(scheme), stroke=None, position=(1510 + slot * 24, 1040))
                self.play(FadeIn(marker), run_time=0.2)
        if self.sound and index:
            self.add_audio(SFX / "transition.wav", start=0.08, volume=0.8)
        self.wait_until(chapter["duration"])


def equation_video(*, sound=True, scheme=DEFAULT_SCHEME):
    scheme = ColorScheme.named(scheme) if isinstance(scheme, str) else scheme
    if not isinstance(scheme, ColorScheme):
        raise TypeError("scheme must be a ColorScheme or preset name")
    pages = []
    for index, chapter in enumerate(CHAPTERS):
        panels = [EquationPanel(EQUATIONS[i], tall=index == 2, sound=sound, scheme=scheme) for i in chapter["indices"]]
        grid = Grid(
            *panels,
            rows=1 if index == 2 else 2,
            columns=2,
            gap=GAP,
            padding=PADDING,
            start_times=chapter["starts"],
            canvas=Canvas(1920, 1080, TRANSPARENT),
        )
        pages.append(
            Layer(
                ChapterBackdrop(chapter, index, sound=sound, scheme=scheme),
                grid,
                canvas=Canvas(1920, 1080, scheme.background),
            )
        )
    video = Sequence(*pages, crossfade=CROSSFADE)
    video.color_scheme = scheme
    return video


def timeline(video):
    scheme = video.color_scheme
    chapters, equations = [], []
    for start, chapter in zip(video.starts, CHAPTERS):
        chapters.append(
            {
                "title": chapter["title"],
                "start": start,
                "end": start + chapter["duration"],
                "layout": "2 columns × 1 row" if len(chapter["indices"]) == 2 else "2 columns × 2 rows",
            }
        )
        for offset, index in zip(chapter["starts"], chapter["indices"]):
            spec = EQUATIONS[index]
            equations.append(
                {
                    "number": spec.number,
                    "title": spec.title,
                    "start": round(start + offset, 3),
                    "preview": round(start + offset + 4.5, 3),
                    "expression": spec.expression,
                    "color": spec.accent(scheme),
                    "symbol_colors": spec.color_map(scheme),
                }
            )
    return {
        "duration": video.duration,
        "crossfade": CROSSFADE,
        "color_scheme": scheme.name,
        "background": scheme.background,
        "foreground": scheme.text,
        "chapters": chapters,
        "equations": equations,
    }
