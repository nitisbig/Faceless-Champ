"""Illustrative user growth; all visual and animation behavior comes from the library."""

import json
from pathlib import Path

from faceless_champ import Animation, Canvas, FadeIn, Image, Line, Number, Polyline, Scene, Text, linear

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[1]
TERRA, GRAY, PALE = "#C15F3C", "#B1ADA1", "#F4F3EE"
FONT = ROOT / "assets/fonts/DMSans[opsz,wght].ttf"
FONT = FONT if FONT.exists() else None


def label(value, x, y, size=24, color=GRAY, **kwargs):
    return Text(value, position=(x, y), font=FONT, font_size=size, color=color, **kwargs)


def ai_company_video():
    data = json.loads((PROJECT / "data/growth.json").read_text())
    scene = Scene(Canvas(1920, 1080, "#FFFFFF"))
    title = label("AI, finding its audience.", 100, 68, 66, TERRA, anchor="top_left")
    subtitle = label("Five imagined growth stories · time from each beginning", 103, 158, 26, anchor="top_left")
    with scene.at(0):
        scene.play(FadeIn(title), FadeIn(subtitle), run_time=1)
        scene.add(label("ILLUSTRATIVE DATA · NOT REPORTED USER COUNTS", 960, 1020, 22, TERRA))
    x0, x1, top, row_height = 425, 1575, 320, 127
    start, travel = 3.0, 23.0
    # Shared relative timeline; origins and all values are fictional, not historical claims.
    cursor = Line(length=660, stroke=PALE, stroke_width=3, rotation=90, position=(x0, 580), z_index=-1)
    elapsed = Number(
        0,
        format_spec=".1f",
        suffix=" years",
        font=FONT,
        font_size=44,
        color=TERRA,
        position=(1670, 141),
        width=300,
        align="right",
    )
    with scene.at(1):
        scene.play(FadeIn(cursor), FadeIn(elapsed), run_time=0.7)
    with scene.at(start):
        scene.play(cursor.animate.move_to(x1, 580), elapsed.animate.value_to(3), run_time=travel, rate_func=linear)
    for year in range(4):
        x = x0 + (x1 - x0) * year / 3
        with scene.at(0.6):
            scene.add(label(str(year), x, 940, 25))
    with scene.at(0.6):
        scene.add(label("YEARS FROM BEGINNING", 1000, 980, 18))
        scene.add(label("USERS / MILLIONS", 1750, 235, 19, TERRA))
    for i, company in enumerate(data["companies"]):
        base = top + i * row_height
        logo = Image.from_source(
            PROJECT / "logo" / company["logo"], width=52, height=52, trim=True, tint=TERRA, position=(128, base - 20)
        )
        name = label(company["name"], 181, base - 37, 29, TERRA, anchor="top_left")
        baseline = Line(length=x1 - x0, stroke=PALE, stroke_width=2, position=((x0 + x1) / 2, base))
        with scene.at(0.6 + i * 0.18):
            scene.play(FadeIn(logo), FadeIn(name), FadeIn(baseline), run_time=0.7)
        values = company["users_millions"]
        points = [(x0 + j / (len(values) - 1) * (x1 - x0), base - v / 100 * 90) for j, v in enumerate(values)]
        # Many short linear samples of a smoothstep curve keep paths and logos synchronized.
        dense = []
        for j in range(len(points) - 1):
            for k in range(20):
                u = k / 20
                eased = u * u * (3 - 2 * u)
                dense.append(
                    (
                        points[j][0] + (points[j + 1][0] - points[j][0]) * u,
                        points[j][1] + (points[j + 1][1] - points[j][1]) * eased,
                        values[j] + (values[j + 1] - values[j]) * eased,
                    )
                )
        dense.append((*points[-1], values[-1]))
        marker = Image.from_source(
            PROJECT / "logo" / company["logo"],
            width=32,
            height=32,
            trim=True,
            tint=TERRA,
            position=points[0],
            z_index=2,
        )
        count = Number(
            0,
            format_spec=".1f",
            suffix="M",
            font=FONT,
            font_size=40,
            color=TERRA,
            width=210,
            align="right",
            position=(1750, base - 27),
        )
        with scene.at(2):
            scene.play(FadeIn(marker), FadeIn(count), run_time=0.6)
        curve = Polyline([point[:2] for point in dense], stroke=TERRA, stroke_width=3, line_cap="round", draw_by="x")
        positions = tuple((j / (len(dense) - 1), point[:2]) for j, point in enumerate(dense))
        counts = tuple((j / (len(dense) - 1), point[2]) for j, point in enumerate(dense))
        with scene.at(start):
            scene.play(
                Animation(curve, {"draw": 1.0}, {"draw": 0.0}),
                Animation(marker, {"position": points[-1]}, keyframes={"position": positions}),
                Animation(count, {"value": values[-1]}, keyframes={"value": counts}),
                run_time=travel,
                rate_func=linear,
            )
    scene.wait_until(30)
    return scene


def timeline(video):
    return {
        "duration": video.duration,
        "background": "#FFFFFF",
        "chapters": [{"start": 0, "end": 30, "title": "An illustrative audience"}],
        "storyboard_times": [1.5, 4, 9, 15, 22, 29],
        "data": "data/growth.json",
        "metric": "Illustrative users in millions",
        "note": "All values and relative origins are fictional, not reported company history.",
    }
