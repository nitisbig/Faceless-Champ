"""Fast editorial motion, authored on the unchanged source narration clock."""

from itertools import pairwise

from faceless_champ import (
    Animation,
    Arrow,
    Circle,
    Draw,
    FadeIn,
    FadeOut,
    Group,
    Line,
    Polyline,
    PopIn,
    ProgressBar,
    ProgressRing,
    Pulse,
    Rectangle,
    SlideIn,
    ease_out,
    linear,
)

from .design import CONFIG, INK, RUST, STONE, WHITE, artwork, icon, number, panel, pill, text


# These helpers compose public library animations; no frame renderer lives here.
def beat(b, source, label, *animations, duration=0.42, easing=None):
    """Record a meaningful visual action and schedule it on the source clock."""
    local = source - b.start_time
    if local < -1e-8 or local + duration > b.segment_duration + 1e-8:
        raise ValueError(f"Visual beat outside chapter: {label}")
    b.visual_beats.append({"source_time": round(source, 3), "duration": duration, "action": label})
    with b.at(max(0, local)):
        b.play(*animations, run_time=duration, rate_func=easing)


def show(b, source, label, *components, duration=0.38):
    beat(b, source, label, *(SlideIn(c, distance=24) for c in components), duration=duration)


def retire(b, source, *components):
    beat(b, source, "Reframe the evidence", *(FadeOut(c) for c in components), duration=0.22)
    with b.at(source - b.start_time + 0.22):
        b.remove(*components)


def path(points, *, color=RUST, width=6):
    return Polyline(points, stroke=color, stroke_width=width, fill=None, line_cap="round")


def arrow(a, z, *, color=RUST, width=4):
    return Arrow(a, z, stroke=color, stroke_width=width, tip_size=15)


def chrome(b, section, title, subtitle, *, source="", index=0):
    b.visual_beats = []
    b.add(
        text("NVDA", 147, 87, 32, weight=750),
        text(section, 565, 88, 24, weight=550, color=RUST),
        pill(f"0{index + 1} / 06", 910, 88, 155),
        Line(936, position=(540, 143), stroke="#E4E0D7", stroke_width=2),
        text(subtitle, 540, 345, 28, color="#746E63"),
        text(source, 540, 1467, 23, color="#746E63"),
    )
    show(b, b.start_time, "Chapter headline", text(title, 540, 246, 79, serif=True, weight=600))
    # The thin rail gives continuous orientation without distracting from the data.
    for i, label in enumerate(("QUESTION", "GROWTH", "PRICE", "RISKS", "TEST", "END")):
        x = 147 + 157 * i
        b.add(text(label, x, 1531, 18, color=RUST if i == index else "#888174", weight=650))
        rail = ProgressBar(
            width=125, height=5, color=RUST, track_color="#E6E2D8", progress=1 if i < index else 0, position=(x, 1561)
        )
        b.add(rail)
        if i == index:
            b.visual_progress = rail


def opening(b, mode):
    chrome(
        b,
        "THE INVESTMENT QUESTION",
        "After the run.",
        "A strong business. A demanding price.",
        source="Illustrative price path · no historical prices",
        index=0,
    )
    graph = panel(540, 748, 936, 644)
    b.add(
        graph,
        text("MOMENTUM", 233, 476, 24, color=RUST, weight=650),
        pill("NEAR RECORD HIGHS", 739, 476, 335),
        text("PRICE", 171, 979, 21, color="#746E63"),
        text("TIME →", 889, 979, 21, color="#746E63"),
    )
    for y in (600, 710, 820, 930):
        b.add(Line(800, position=(550, y), stroke="#E3DFD4", stroke_width=1))
    points = [(155, 909), (249, 860), (342, 889), (450, 770), (555, 792), (664, 674), (770, 699), (916, 563)]
    curve = path(points, width=8)
    show(b, 0.55, "Chip artwork enters", artwork(1, 540, 1230, 936, 282, mode))
    beat(b, 1.36, "Price momentum draws", Draw(curve), duration=2.55, easing=linear)
    marker = Circle(radius=10, fill=RUST, stroke=WHITE, stroke_width=4, position=points[0])
    beat(b, 1.36, "Track the run", FadeIn(marker), duration=0.12)
    # Follow the same polyline while it draws, rather than an unrelated cursor.
    lengths = [0.0]
    for a, z in pairwise(points):
        lengths.append(lengths[-1] + ((z[0] - a[0]) ** 2 + (z[1] - a[1]) ** 2) ** 0.5)
    keys = tuple((length / lengths[-1], p) for length, p in zip(lengths, points))
    beat(
        b,
        1.36,
        "Follow the rising price",
        Animation(marker, {"position": points[-1]}, keyframes={"position": keys}),
        duration=2.55,
        easing=linear,
    )
    show(b, 2.16, "Record-high callout", text("The run", 262, 563, 56, serif=True))
    show(b, 3.93, "Company versus price", pill("BUSINESS ≠ STOCK", 540, 1035, 320, dark=True))
    beat(b, 4.35, "Emphasize the high", Pulse(marker, factor=1.65), duration=0.48)
    show(b, 4.88, "Turn momentum into a question", text("Still worth watching?", 540, 1407, 52, serif=True, color=RUST))
    ring = ProgressRing(width=56, height=56, stroke_width=3, color=RUST, track_color="#E6D4C8", position=points[-1])
    beat(b, 5.75, "Highlight the starting hurdle", FadeIn(ring), ring.animate.progress_to(1), duration=0.72)
    show(b, 6.60, "Next: inspect the engine", pill("START WITH GROWTH", 540, 404, 325))


def growth(b, mode):
    r = CONFIG["revenue"]
    metrics = CONFIG["earnings"]
    chrome(
        b,
        "01 / THE GROWTH ENGINE",
        "Growth, in numbers.",
        "Reported revenue · USD billions",
        source="NVIDIA earnings · Q2 FY2027 · 26 Aug 2026",
        index=1,
    )
    hero = number(0, 540, 487, 108, prefix="$", suffix="B", width=650)
    quarter = text("Q2 FY27", 540, 582, 26, weight=650)
    show(b, 7.80, "Quarterly revenue counter", hero, quarter)
    chart_panel = panel(540, 904, 936, 548)
    b.add(chart_panel)
    grid = []
    for v in (0, 25, 50, 75, 100):
        y = 1090 - v * 3.7
        grid.extend(
            [Line(747, position=(589, y), stroke="#E0DACE", stroke_width=1), text(str(v), 149, y, 21, color="#746E63")]
        )
    labels = [text("Q2 FY26", 360, 1143, 28, weight=550), text("Q2 FY27", 762, 1143, 28, weight=550)]
    b.add(*grid, *labels)
    bars = [
        Rectangle(width=166, height=1, corner_radius=0, position=(x, 1090), fill=c, stroke=None)
        for x, c in ((360, STONE), (762, RUST))
    ]
    previous = number(0, 360, 843, 44, prefix="$", suffix="B", color=INK, width=245)
    current = number(0, 762, 658, 44, prefix="$", suffix="B", width=245)
    growth_card = Group(
        panel(310, 1310, 445, 183, dark=True), text("YEAR OVER YEAR", 310, 1263, 21, color="#DDD4C6", weight=600)
    )
    increase_card = Group(panel(777, 1310, 445, 183), text("ADDED REVENUE", 777, 1263, 21, color="#746E63", weight=600))
    yoy = number(0, 310, 1336, 65, prefix="+", suffix="%", decimals=0, color=WHITE, width=380)
    added = number(0, 777, 1336, 62, prefix="+$", suffix="B", width=395)
    scale = text("0–100B scale", 789, 620, 22, color="#746E63")
    show(b, 8.89, "Reveal revenue scale", scale)
    beat(
        b, 9.40, "Count the current quarter", hero.animate.value_to(r["billions_usd"][1]), duration=2.1, easing=ease_out
    )
    beat(
        b,
        10.25,
        "Build last year's revenue",
        FadeIn(previous),
        previous.animate.value_to(r["billions_usd"][0]),
        bars[0].animate.height_to(r["billions_usd"][0] * 3.7),
        bars[0].animate.move_to(360, 1090 - r["billions_usd"][0] * 3.7 / 2),
        duration=0.95,
    )
    same_quarter = text("SAME FISCAL QUARTER · ONE YEAR APART", 540, 1202, 21, color="#746E63", weight=550)
    show(b, 11.65, "The same quarter one year apart", same_quarter)
    beat(
        b,
        12.55,
        "Reveal this year's revenue",
        FadeIn(current),
        current.animate.value_to(r["billions_usd"][1]),
        bars[1].animate.height_to(r["billions_usd"][1] * 3.7),
        bars[1].animate.move_to(762, 1090 - r["billions_usd"][1] * 3.7 / 2),
        duration=1.0,
    )
    show(b, 13.70, "Growth metrics enter", growth_card, increase_card, yoy, added)
    beat(
        b,
        14.40,
        "Over double year-on-year",
        yoy.animate.value_to(r["yoy_percent"]),
        added.animate.value_to(metrics["added_revenue_billions"]),
        duration=0.85,
    )
    bracket = path([(464, 919), (527, 919), (527, 734), (661, 734)], color=INK, width=3)
    beat(b, 15.45, "Bridge the growth difference", Draw(bracket), duration=0.55)
    multiple = pill("2.06× LAST YEAR", 420, 665, 290, dark=True)
    show(b, 16.35, "Revenue growth multiple", multiple)
    beat(b, 17.25, "Focus the engine", Pulse(hero, factor=1.035), duration=0.45)
    # The infrastructure evidence replaces the complete graph region.
    retire(
        b,
        17.90,
        hero,
        quarter,
        chart_panel,
        *grid,
        *labels,
        *bars,
        previous,
        current,
        growth_card,
        increase_card,
        yoy,
        added,
        scale,
        same_quarter,
        bracket,
        multiple,
    )
    picture = artwork(2, 540, 651, 936, 448, mode)
    show(b, 18.15, "Enter the infrastructure buildout", picture)
    dc_card = Group(
        panel(540, 1012, 936, 228),
        icon("\ue1db", 180, 1009, 86),
        text("DATA CENTER", 470, 944, 24, weight=650),
        text("Q2 FY27 revenue", 464, 1075, 24, color="#746E63"),
        text("OF REVENUE", 847, 1110, 20, color="#746E63", weight=550),
    )
    dc = number(0, 472, 1011, 70, prefix="$", suffix="B", width=390)
    share = ProgressRing(
        width=133, height=133, color=RUST, track_color="#E4DDD0", stroke_width=11, position=(847, 1016)
    )
    share_label = number(0, 847, 1016, 31, suffix="%", width=128)
    show(b, 18.95, "The revenue engine", dc_card, dc, share, share_label)
    beat(
        b,
        19.75,
        "Data Center revenue and mix",
        dc.animate.value_to(metrics["data_center_billions"]),
        share.animate.progress_to(metrics["data_center_share_percent"] / 100),
        share_label.animate.value_to(metrics["data_center_share_percent"]),
        duration=0.8,
    )
    show(b, 20.75, "Data Center growth", pill("DATA CENTER +117% YoY", 540, 1169, 435))
    nodes = [
        Group(panel(x, 1322, 260, 140, accent=x == 847), icon(glyph, x, 1290, 44), text(label, x, 1358, 24, weight=600))
        for x, glyph, label in ((233, "\ue8b8", "AI DEMAND"), (540, "\ue1db", "BUILDOUT"), (847, "\ue322", "NVIDIA"))
    ]
    show(b, 21.42, "AI demand enters", nodes[0])
    beat(
        b,
        22.15,
        "Demand funds the buildout",
        Draw(arrow((368, 1322), (399, 1322))),
        SlideIn(nodes[1], distance=20),
        duration=0.42,
    )
    beat(
        b,
        22.90,
        "NVIDIA sits at the center",
        Draw(arrow((675, 1322), (706, 1322))),
        PopIn(nodes[2], from_scale=0.9, overshoot=1.025),
        duration=0.45,
    )
    beat(b, 23.65, "Revenue engine emphasis", Pulse(share, factor=1.04), duration=0.42)


def expectations(b, mode):
    chrome(
        b,
        "02 / THE PRICE OF EXPECTATIONS",
        "The bar is high.",
        "The stock already assumes a strong future.",
        source="Illustrative hurdle · no valuation or forecast data",
        index=2,
    )
    premium = Group(
        panel(540, 497, 936, 190, dark=True),
        text("PREMIUM VALUATION", 540, 455, 24, color="#DDD4C6", weight=650),
        text("A lot is already priced in.", 540, 521, 47, serif=True, color=WHITE),
    )
    show(b, 24.75, "Valuation dashboard", premium)
    base = panel(540, 955, 936, 647)
    show(b, 25.50, "Expectation test viewport", base)
    show(b, 26.35, "Read the hurdle", text("FUTURE PERFORMANCE", 540, 675, 24, color="#746E63", weight=600))
    growth_node = Group(icon("\ue8e5", 270, 875, 74), text("GROWTH", 270, 977, 26, weight=600))
    price_node = Group(icon("\ueb70", 540, 875, 74), text("PRICE", 540, 977, 26, weight=600))
    hurdle_node = Group(icon("\ue8e8", 810, 875, 74), text("HURDLE", 810, 977, 26, weight=600))
    first_link, second_link = arrow((350, 875), (435, 875)), arrow((620, 875), (705, 875))
    show(b, 26.35, "Growth drives the price", growth_node)
    show(b, 27.15, "Premium price condition", pill("HIGH PRICE", 294, 1390, 280))
    beat(b, 27.15, "Growth feeds valuation", Draw(first_link), SlideIn(price_node, distance=18), duration=0.42)
    beat(b, 28.05, "Price implies a hurdle", Draw(arrow((449, 1390), (520, 1390))), duration=0.4)
    beat(b, 28.05, "The price sets the hurdle", Draw(second_link), SlideIn(hurdle_node, distance=18), duration=0.42)
    show(b, 28.71, "Premium valuation means a high bar", pill("HIGH EXPECTATIONS", 752, 1390, 380, dark=True))
    retire(b, 29.18, growth_node, price_node, hurdle_node, first_link, second_link)
    baseline = Line(750, position=(540, 1157), stroke=STONE, stroke_width=2)
    show(b, 29.60, "Performance baseline", baseline, text("Growth has to clear the hurdle", 540, 1296, 33, serif=True))
    hurdle = Line(750, position=(540, 893), stroke=RUST, stroke_width=4)
    beat(b, 30.77, "Draw the expectation hurdle", Draw(hurdle), duration=0.48)
    show(b, 31.55, "Mark what is priced in", pill("PRICED-IN EXPECTATIONS", 377, 840, 405))
    ordinary = Rectangle(width=154, height=1, position=(330, 1157), fill=STONE, stroke=None)
    exceptional = Rectangle(width=154, height=1, position=(751, 1157), fill=RUST, stroke=None)
    show(
        b,
        32.45,
        "Separate the two performance outcomes",
        text("GOOD", 330, 1200, 23, weight=650),
        text("EXCEPTIONAL", 751, 1200, 23, color=RUST, weight=650),
    )
    beat(
        b,
        33.35,
        "Ordinary growth builds",
        ordinary.animate.height_to(168),
        ordinary.animate.move_to(330, 1073),
        duration=0.65,
    )
    show(b, 34.83, "Good growth still below the bar", text("Below the bar", 330, 974, 30, color="#746E63"))
    beat(
        b,
        35.45,
        "Exceptional growth starts",
        exceptional.animate.height_to(180),
        exceptional.animate.move_to(751, 1067),
        duration=0.55,
    )
    beat(
        b,
        36.28,
        "Exceptional growth clears the hurdle",
        exceptional.animate.height_to(407),
        exceptional.animate.move_to(751, 953.5),
        duration=0.6,
    )
    check = icon("\ue5ca", 751, 723, 46)
    show(b, 37.10, "Clearing the bar is the test", check)
    show(b, 37.82, "Continuation matters", text("And keep doing it.", 540, 1336, 30, color=RUST, weight=550))


def risks(b, mode):
    chrome(
        b,
        "03 / PRESSURES ON THE THESIS",
        "Three points of friction.",
        "How each risk reaches the growth story.",
        source="Potential mechanisms · no estimated impact percentages",
        index=3,
    )
    # Each row explains a mechanism; decorative severity scores are avoided.
    for y, digit, title, detail, glyph in (
        (582, "01", "Custom AI chips", "Compete for the same spending", "\ue322"),
        (913, "02", "Power constraints", "Can slow new deployments", "\uea0b"),
        (1244, "03", "Higher interest rates", "Pressure premium valuations", "\ueb58"),
    ):
        show(
            b,
            b.start_time + (int(digit) - 1) * 0.24,
            f"Risk {digit} surface",
            panel(540, y, 936, 294),
            text(digit, 130, y - 99, 22, color=RUST, weight=650),
        )
        b.add(text(title, 568, y - 104, 42, serif=True), text(detail, 559, y - 55, 25, color="#746E63"))
    chip = Group(icon("\ue322", 215, 611, 76), text("BUDGET", 215, 683, 21, weight=600))
    show(b, 38.92, "Custom-chip competition", chip)
    beat(
        b,
        39.55,
        "Budget splits across suppliers",
        Draw(path([(277, 611), (407, 611), (447, 582), (578, 582)], width=3)),
        Draw(path([(407, 611), (447, 653), (578, 653)], color=STONE, width=3)),
        SlideIn(pill("NVIDIA", 771, 582, 280, dark=True), distance=16),
        duration=0.44,
    )
    show(b, 40.25, "Alternative silicon competes", pill("CUSTOM SILICON", 771, 653, 280))
    power = icon("\uea0b", 216, 969, 73)
    show(b, 40.83, "Power bottleneck enters", power)
    blocks = [
        Rectangle(
            width=45, height=56, corner_radius=8, position=(x, 969), fill=RUST if i < 2 else "#D7D1C5", stroke=None
        )
        for i, x in enumerate((400, 468, 536, 604))
    ]
    beat(
        b, 41.50, "Deployment pipeline fills", *(PopIn(c, from_scale=0.7, overshoot=1.03) for c in blocks), duration=0.5
    )
    stop = Line(112, rotation=90, position=(679, 969), stroke=RUST, stroke_width=5)
    beat(
        b,
        42.25,
        "Limited power blocks the pipeline",
        Draw(arrow((261, 969), (350, 969))),
        Draw(stop),
        SlideIn(pill("DELAY", 831, 969, 210), distance=18),
        duration=0.45,
    )
    beat(
        b,
        43.00,
        "Capacity remains constrained",
        blocks[2].animate.fill_to("#B1ADA1"),
        blocks[3].animate.fill_to("#B1ADA1"),
        duration=0.5,
    )
    show(b, 44.00, "Rates pressure enters", icon("\ueb58", 215, 1300, 73))
    beat(
        b,
        44.65,
        "Higher rates arrow",
        Draw(arrow((359, 1342), (444, 1259))),
        SlideIn(text("RATES ↑", 509, 1359, 23, weight=650), distance=15),
        duration=0.42,
    )
    beat(
        b,
        45.35,
        "Valuation pressure arrow",
        Draw(arrow((659, 1259), (804, 1335), color=INK)),
        SlideIn(text("VALUATION ↓", 794, 1359, 23, weight=650), distance=15),
        duration=0.45,
    )
    show(b, 46.10, "Three mechanisms, one thesis", pill("WATCH ALL THREE", 540, 408, 335, dark=True))
    beat(b, 46.70, "Carry the risks into the verdict", Pulse(stop, factor=1.08), duration=0.38)


def verdict(b, mode):
    chrome(
        b,
        "04 / BUSINESS QUALITY × EXPECTATIONS",
        "Great company. High bar.",
        "Two different questions for investors.",
        source="Illustrative growth comparison · not a forecast",
        index=4,
    )
    show(b, 47.62, "Retain the compute sculpture", artwork(3, 540, 528, 936, 222, mode))
    company = Group(
        panel(307, 794, 452, 235),
        icon("\ue5ca", 307, 724, 41),
        text("STRONG BUSINESS", 307, 780, 23, weight=650),
        text("$96.2B", 307, 848, 56, weight=650),
    )
    price = Group(
        panel(777, 794, 452, 235, dark=True),
        icon("\ue8e5", 777, 724, 41, color=WHITE),
        text("HIGH EXPECTATIONS", 777, 780, 23, color="#DDD4C6", weight=650),
        text("A high hurdle", 777, 849, 43, serif=True, color=WHITE),
    )
    show(b, 48.35, "Business quality first", company)
    beat(b, 49.04, "Emphasize the revenue engine", Pulse(company, factor=1.025), duration=0.5)
    show(b, 49.88, "Fundamental growth", pill("REVENUE +106% YoY", 307, 946, 405))
    show(b, 50.80, "The price has a separate test", price)
    show(b, 51.90, "Distinguish business from stock", pill("ALREADY PRICED IN", 777, 946, 405, dark=True))
    show(
        b,
        52.75,
        "A great business is only half the test",
        text("QUALITY ≠ EXPECTATION BEAT", 540, 1013, 24, color=RUST, weight=650),
    )
    graph = panel(540, 1210, 936, 312)
    show(b, 53.60, "Reveal the forward test", graph)
    hurdle = Line(754, position=(540, 1193), stroke=STONE, stroke_width=3)
    beat(
        b,
        54.32,
        "Expectations become the benchmark",
        Draw(hurdle),
        SlideIn(text("THE EXPECTATION BAR", 376, 1153, 23, weight=550), distance=15),
        duration=0.4,
    )
    points = [(163, 1310), (350, 1290), (520, 1250), (705, 1170), (913, 1109)]
    curve = path(points, width=7)
    # draw_by=x makes the exact crossing predictable on the source clock.
    curve.draw_by = "x"
    beat(b, 55.32, "Future growth approaches the hurdle", Draw(curve), duration=2.03, easing=linear)
    dot = Circle(radius=8, fill=RUST, stroke=WHITE, stroke_width=3, position=points[0])
    beat(b, 55.32, "Track future performance", FadeIn(dot), duration=0.1)
    # x-linear progress reaches the hurdle at 56.57, just before 'beating'.
    keys = tuple(((p[0] - 163) / 750, p) for p in points)
    beat(
        b,
        55.32,
        "Move along the growth path",
        Animation(dot, {"position": points[-1]}, keyframes={"position": keys}),
        duration=2.03,
        easing=linear,
    )
    show(b, 56.84, "Growth beats what is priced in", pill("BEAT THE BAR", 755, 1065, 275, dark=True))
    beat(b, 57.60, "Highlight exceptional performance", Pulse(dot, factor=1.7), duration=0.42)
    show(
        b,
        58.08,
        "Land the investment question",
        text("Can growth keep beating it?", 540, 1409, 46, serif=True, color=RUST),
    )


def closing(b, mode):
    chrome(
        b,
        "THE TAKEAWAY",
        "Watch growth. Watch the bar.",
        "Business performance × expectations",
        source="NVIDIA · earnings-based analysis",
        index=5,
    )
    b.add(panel(540, 885, 936, 840))
    show(
        b,
        59.35,
        "Close on the two watchpoints",
        icon("\ue8e5", 540, 610, 97),
        text("GROWTH", 540, 756, 65, weight=650),
        text("EXPECTATIONS", 540, 866, 55, weight=650, color=RUST),
    )
    with b.at_cue(157):
        show(b, b.start_time + b.time, "Analysis label", pill("ANALYSIS", 540, 1025, 270, dark=True))
    with b.at_cue(159):
        show(b, b.start_time + b.time, "Narrated closing disclaimer", text("Not financial advice", 540, 1180, 37))


AUTHORS = [opening, growth, expectations, risks, verdict, closing]
