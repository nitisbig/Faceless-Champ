"""Cue-synchronized scene compositions, using only the main public library."""

from faceless_champ import (
    Arrow,
    Axis,
    BarChart,
    ChartStyle,
    Circle,
    Draw,
    FadeIn,
    FadeOut,
    Group,
    Line,
    Polyline,
    Rectangle,
    SlideIn,
    linear,
)

from .design import CONFIG, RUST, SANS, SCHEME, STONE, artwork, icon, panel, text


def opening(b, mode):
    b.add(text("NVDA / THE QUESTION", 540, 116, 27, color=RUST, weight=600))
    b.play(FadeIn(text("After the run,\nwhat comes next?", 540, 277, 88, serif=True)), run_time=0.4)
    b.add(artwork(1, 540, 1080, 880, 280, mode))
    b.add(text("Conceptual price path · no market data", 540, 855, 25))
    path = Polyline(
        [(150, 760), (265, 733), (385, 760), (485, 652), (610, 690), (720, 565), (820, 580), (930, 478)],
        stroke=RUST,
        stroke_width=6,
        fill=None,
        draw_by="x",
        line_cap="round",
    )
    with b.at_cue(6):
        b.play(Draw(path), run_time=1.45, rate_func=linear)
    with b.at_cue(8):
        b.play(
            FadeIn(text("Near record highs", 690, 431, 36)),
            FadeIn(Circle(radius=9, fill=RUST, stroke=None, position=(930, 478))),
            run_time=0.3,
        )
    with b.at_cue(16):
        b.play(SlideIn(text("Still worth watching?", 540, 1320, 64, serif=True, color=RUST), distance=20), run_time=0.4)
    b.add(text("Growth versus expectations", 540, 1500, 28))


def growth(b, mode):
    b.add(text("01 / THE GROWTH CASE", 540, 116, 27, color=RUST, weight=600))
    b.play(FadeIn(text("The engine\nis growth.", 540, 277, 96, serif=True)), run_time=0.35)
    chart = BarChart(
        CONFIG["revenue"]["categories"],
        {"Revenue": [CONFIG["revenue"]["billions_usd"][0], 0]},
        width=850,
        height=530,
        position=(540, 820),
        y_axis=Axis(limits=(0, 110), ticks=(0, 50, 100), unit="B"),
        style=ChartStyle(scheme=SCHEME, colors=(RUST,), font=SANS, font_size=32, legend=False),
    )
    source = text("NVIDIA earnings · fiscal Q2 FY2027\n26 Aug 2026 · revenue in USD billions", 540, 1160, 25)
    graph = Group(panel(540, 840, 920, 660), chart)
    values = CONFIG["revenue"]["billions_usd"]
    revenue = text(f"${values[1]:.1f}B", 540, 440, 104, serif=True, color=RUST)
    comparison = text(f"+{CONFIG['revenue']['yoy_percent']}% year over year", 540, 1290, 44, color=RUST)
    with b.at_cue(25):
        b.play(FadeIn(graph), FadeIn(source), run_time=0.4)
    with b.at_cue(36):
        b.play(chart.animate.data_to({"Revenue": values}), FadeIn(revenue), run_time=0.6)
    with b.at_cue(39):
        b.play(SlideIn(comparison, distance=16), run_time=0.35)
    with b.at_cue(48):
        b.play(FadeOut(graph), FadeOut(source), FadeOut(revenue), FadeOut(comparison), run_time=0.25)
        b.remove(graph, source, revenue, comparison)
        b.play(
            FadeIn(artwork(2, 540, 688, 920, 530, mode)),
            FadeIn(text("AI infrastructure", 540, 1040, 62, serif=True)),
            run_time=0.35,
        )
    with b.at_cue(55):
        b.play(
            Draw(Arrow((540, 1100), (540, 1220), stroke=RUST, stroke_width=4)),
            FadeIn(
                Group(
                    panel(540, 1340, 660, 150, accent=True),
                    icon("\ue322", 300, 1340, 78),
                    text("NVIDIA", 575, 1340, 60, serif=True),
                )
            ),
            run_time=0.4,
        )
    with b.at_cue(61):
        b.play(FadeIn(text("At the center of the buildout", 540, 1510, 30)), run_time=0.35)


def expectations(b, mode):
    b.add(text("02 / THE VALUATION TEST", 540, 116, 27, color=RUST, weight=600))
    b.play(FadeIn(text("The bar\nis already high.", 540, 277, 96, serif=True)), run_time=0.35)
    b.add(text("Conceptual hurdle · not a forecast", 540, 1510, 26))
    with b.at_cue(77):
        b.play(
            FadeIn(Group(panel(540, 495, 870, 145), text("Premium valuation", 540, 495, 54, serif=True))), run_time=0.4
        )
    hurdle = Line(790, stroke=RUST, stroke_width=5, position=(540, 790))
    with b.at_cue(80):
        b.play(
            Draw(hurdle),
            FadeIn(text("EXPECTATIONS", 340, 733, 34, color=RUST, weight=600)),
            FadeIn(text("A high price assumes a strong future", 540, 1280, 36)),
            run_time=0.4,
        )
    ordinary = Rectangle(width=170, height=190, fill=STONE, stroke=None, position=(355, 1035))
    with b.at_cue(89):
        b.play(SlideIn(ordinary, direction="up", distance=25), FadeIn(text("Growth", 355, 1170, 36)), run_time=0.35)
    exceptional = Rectangle(width=170, height=490, fill=RUST, stroke=None, position=(725, 885))
    with b.at_cue(92):
        b.play(
            SlideIn(exceptional, direction="up", distance=25),
            FadeIn(text("Exceptional\ngrowth", 725, 1195, 36)),
            run_time=0.5,
        )
    with b.at_cue(95):
        b.play(FadeIn(text("Must continue.", 540, 1380, 62, serif=True, color=RUST)), run_time=0.3)


def risks(b, mode):
    b.add(text("03 / WHAT CAN GET IN THE WAY", 540, 116, 27, color=RUST, weight=600))
    b.play(FadeIn(text("Three pressures.\nOne growth story.", 540, 277, 86, serif=True)), run_time=0.35)
    for cue, y, glyph, title, detail in (
        (96, 620, "\ue322", "Custom AI chips", "Competition for spending"),
        (103, 920, "\uea0b", "Power constraints", "Slower deployments"),
        (111, 1220, "\ueb58", "Higher rates", "Pressure on valuations"),
    ):
        row = Group(
            panel(540, y, 910, 232),
            icon(glyph, 205, y - 30, 94),
            text(title, 585, y - 35, 53, serif=True),
            text(detail, 570, y + 52, 32),
            Arrow((300, y + 50), (345, y + 50), stroke=RUST, stroke_width=3, tip_size=12),
        )
        with b.at_cue(cue):
            b.play(SlideIn(row, direction="right", distance=22), run_time=0.45)
    b.add(text("Potential headwinds · no impact estimates", 540, 1510, 26))


def verdict(b, mode):
    b.add(text("04 / THE QUESTION THAT MATTERS", 540, 116, 27, color=RUST, weight=600))
    b.play(FadeIn(text("Great company.\nHigh expectations.", 540, 277, 85, serif=True)), run_time=0.35)
    b.add(artwork(3, 540, 535, 890, 210, mode))
    with b.at_cue(126):
        b.play(
            FadeIn(Group(panel(315, 780, 410, 175), text("Strong\nbusiness", 315, 780, 49, serif=True))), run_time=0.35
        )
    with b.at_cue(134):
        b.play(
            FadeIn(Group(panel(765, 780, 410, 175, accent=True), text("High\nexpectations", 765, 780, 49, serif=True))),
            run_time=0.35,
        )
    b.add(text("Conceptual comparison · not a forecast", 540, 1510, 25))
    expectation = Line(810, stroke=STONE, stroke_width=4, position=(540, 1100))
    with b.at_cue(136):
        b.play(Draw(expectation), FadeIn(text("Expected growth", 330, 1055, 30)), run_time=0.35)
    future = Polyline(
        [(155, 1300), (340, 1260), (520, 1200), (700, 1090), (925, 973)],
        stroke=RUST,
        stroke_width=6,
        fill=None,
        draw_by="x",
        line_cap="round",
    )
    with b.at_cue(147):
        # Reaches the expectation hurdle during cue 151, 'beating'.
        b.play(Draw(future), run_time=1.55, rate_func=linear)
    with b.at_cue(151):
        b.play(FadeIn(text("Can growth beat the bar?", 540, 1410, 58, serif=True, color=RUST)), run_time=0.35)


def closing(b, mode):
    b.add(text("NVDA / THE TAKEAWAY", 540, 116, 27, color=RUST, weight=600))
    b.play(FadeIn(text("Watch the growth.\nWatch the bar.", 540, 660, 99, serif=True)), run_time=0.35)
    with b.at_cue(157):
        b.play(FadeIn(text("Analysis", 540, 1030, 49, serif=True, color=RUST)), run_time=0.3)
    with b.at_cue(159):
        b.play(FadeIn(text("Not financial advice", 540, 1130, 36)), run_time=0.35)
    b.add(text("NVIDIA · growth versus expectations", 540, 1510, 27))


AUTHORS = [opening, growth, expectations, risks, verdict, closing]
