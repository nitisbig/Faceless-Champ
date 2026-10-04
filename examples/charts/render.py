"""Render a deterministic chart showcase: python examples/charts/render.py --preview."""

import argparse
import math
from pathlib import Path

from faceless_champ import (
    Axis,
    BarChart,
    Canvas,
    ChartReveal,
    ChartStyle,
    ColorScheme,
    Heatmap,
    Histogram,
    LineChart,
    NetworkGraph,
    PieChart,
    PillowRenderer,
    SankeyChart,
    ScatterPlot,
    Scene,
    Sequence,
    VectorField,
)


def showcase(theme="midnight"):
    style = ChartStyle(scheme=ColorScheme.named(theme), font_size=20, title_size=32)
    options = {"width": 1140, "height": 620, "position": (640, 360), "style": style}
    wave = [(i / 10, math.sin(i / 10)) for i in range(63)]
    samples = [math.sin(i * 1.7) + math.cos(i * 0.43) for i in range(160)]
    vectors = [(x, y, -y * 0.18, x * 0.18) for x in range(-2, 3) for y in range(-2, 3)]
    specs = [
        (
            BarChart(
                ["Q1", "Q2", "Q3", "Q4"],
                {"Revenue": [4, 6, 5, 8], "Costs": [-2, -3, -2, -4]},
                title="Economics / Quarterly cash flow",
                y_axis=Axis(limits=(-5, 10), unit="M"),
                **options,
            ),
            {"Revenue": [5, 7, 9, 8], "Costs": [-3, -2, -4, -3]},
        ),
        (
            LineChart(
                {"sin(x)": wave},
                title="Mathematics / Oscillation",
                x_axis=Axis(label="Time (s)"),
                y_axis=Axis(limits=(-1.2, 1.2), label="Amplitude"),
                **options,
            ),
            {"sin(x)": [(x, math.sin(x + 1)) for x, _ in wave]},
        ),
        (
            ScatterPlot(
                {"Observations": [(i, i * 0.6 + math.sin(i)) for i in range(15)]},
                title="Science / Measured response",
                x_axis=Axis(label="Input"),
                y_axis=Axis(limits=(-1, 11), label="Response"),
                **options,
            ),
            {"Observations": [(i, i * 0.65 + math.cos(i)) for i in range(15)]},
        ),
        (
            Histogram(
                samples,
                bins=[-2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2],
                title="Statistics / Sample distribution",
                y_axis=Axis(limits=(0, 45), label="Count"),
                **options,
            ),
            [v * 0.7 for v in samples],
        ),
        (
            Heatmap(
                [[1, 0.3, -0.2], [0.3, 1, 0.6], [-0.2, 0.6, 1]],
                row_labels=["Equity", "Bonds", "Gold"],
                column_labels=["Equity", "Bonds", "Gold"],
                color_limits=(-1, 1),
                title="Finance / Correlation matrix",
                **options,
            ),
            [[1, -0.1, 0.4], [-0.1, 1, 0.2], [0.4, 0.2, 1]],
        ),
        (
            NetworkGraph(
                ["A", "B", "C", "D", "E"],
                [("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("E", "A"), ("A", "C")],
                weights=[1, 2, 3, 2, 1, 2],
                directed=True,
                title="Networks / Directed interactions",
                **options,
            ),
            [3, 1, 2, 4, 2, 1],
        ),
        (
            VectorField(
                vectors,
                title="Physics / Rotational vector field",
                x_axis=Axis(limits=(-3, 3), label="x"),
                y_axis=Axis(limits=(-3, 3), label="y"),
                **options,
            ),
            [(x, y, dx * 1.7, dy * 1.7) for x, y, dx, dy in vectors],
        ),
        (
            SankeyChart(
                ["Income", "Spending", "Saving", "Needs", "Wants"],
                [
                    ("Income", "Spending", 70),
                    ("Income", "Saving", 30),
                    ("Spending", "Needs", 45),
                    ("Spending", "Wants", 25),
                ],
                title="Economics / Household allocation",
                **options,
            ),
            [60, 40, 40, 20],
        ),
        (
            PieChart(
                ["Equity", "Bonds", "Cash"], [55, 30, 15], hole=0.5, title="Finance / Portfolio allocation", **options
            ),
            [40, 40, 20],
        ),
    ]
    scenes = []
    for chart, target in specs:
        scene = Scene(Canvas(1280, 720, style.scheme.background))
        scene.play(ChartReveal(chart), run_time=1).wait(0.5)
        scene.play(chart.animate.data_to(target), run_time=1.5).wait(1)
        scenes.append(scene)
    return Sequence(*scenes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", choices=("midnight", "paper", "ocean"), default="midnight")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preview", action="store_true", help="Render 640x360 at 12 fps")
    mode.add_argument("--frame", type=float, help="Render one frame at this time in seconds")
    mode.add_argument(
        "--storyboard", action="store_true", help="Render reveal/mid-transition/final frames for each chart"
    )
    parser.add_argument("--output", type=Path, help="MP4, PNG, or storyboard directory")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    movie = showcase(args.theme)
    root = Path(__file__).resolve().parent / "output" / args.theme
    if args.frame is not None or args.storyboard:
        renderer = PillowRenderer()
        renderer.validate(movie)
        if args.frame is not None:
            if not 0 <= args.frame <= movie.duration:
                parser.error(f"--frame must be between 0 and {movie.duration}")
            jobs = [(args.output or root / "frame.png", args.frame)]
        else:
            directory = args.output or root / "frames"
            jobs = [
                (directory / f"{i + 1:02d}-{label}.png", i * 4 + time)
                for i in range(9)
                for label, time in (("reveal", 0.5), ("transition", 2.25), ("final", 3.5))
            ]
        for path, _ in jobs:
            if path.exists() and not args.overwrite:
                raise FileExistsError(f"{path} exists; pass --overwrite")
        for path, time in jobs:
            path.parent.mkdir(parents=True, exist_ok=True)
            renderer.frame(movie, time, (1280, 720)).save(path)
        print(f"Wrote {len(jobs)} frame(s)")
    else:
        output = args.output or root / "charts.mp4"
        movie.render(
            output,
            width=640 if args.preview else 1280,
            height=360 if args.preview else 720,
            fps=12 if args.preview else 24,
            preset="fast",
            overwrite=args.overwrite,
        )
        print(output)


if __name__ == "__main__":
    main()
