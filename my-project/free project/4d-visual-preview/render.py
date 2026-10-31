"""45-second preview: 1D -> 4D fullscreen, then the tesseract shrinks between two math panels."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from dimension_source import AXIS_COLORS, PULSE, draw, theta_zw

from faceless_champ import (
    Animation,
    Arrow,
    Draw,
    Equation,
    ExportProgress,
    ExportSettings,
    FunctionSource,
    GlassCard,
    Group,
    Number,
    PathData,
    Scene,
    Text,
    Theme,
    VectorPath,
    Viewport,
    create_renderer,
    dot_grid,
    linear,
    render,
    rendering_identity,
    save_frame,
)

DURATION = 45.0
SHRINK = (15.0, 16.6)
TITLE_GREEN = "#7DDB8F"
theme = Theme.named("midnight")


def frames(scene, obj, prop, values, start, end, rate_func=linear):
    """Source-clock keyframes (same helper as skia-math), repeatable for out-of-order stills."""
    values = tuple(values)
    with scene.at(start):
        scene.play(
            Animation(
                obj,
                {prop: values[-1]},
                starts={prop: values[0]},
                keyframes={prop: tuple((i / (len(values) - 1), v) for i, v in enumerate(values))},
                rate_func=rate_func,
            ),
            run_time=end - start,
        )


def appear(scene, obj, start, end=None, fade=0.45):
    with scene.at(start):
        scene.add(obj)
    frames(scene, obj, "opacity", (0, 1), start, start + fade)
    if end is not None:
        frames(scene, obj, "opacity", (1, 0), end - fade, end)


def pulse(scene, obj, at, peak=1.35):
    frames(scene, obj, "scale", (1, peak, 1), at, at + 0.7, rate_func="smooth")


def math_text(expr, size, color, position, **kwargs):
    return Equation(expr, font_size=size, color=color, position=position, **kwargs)


def brackets(bounds, color, width=4, lip=18):
    left, right, top, bottom = bounds.left, bounds.right, bounds.top, bounds.bottom
    path = PathData(
        (
            ("M", left + lip, top),
            ("L", left, top),
            ("L", left, bottom),
            ("L", left + lip, bottom),
            ("M", right - lip, top),
            ("L", right, top),
            ("L", right, bottom),
            ("L", right - lip, bottom),
        )
    )
    return VectorPath(path, stroke=color, stroke_width=width, line_cap="round", fill=None)


def build_scene() -> Scene:
    with theme.use():
        scene = Scene(theme.canvas())
        canvas = scene.canvas
        text, muted = theme.color("text"), theme.color("muted")
        x_c, y_c, z_c, w_c = AXIS_COLORS
        scene.add(dot_grid(canvas.bounds, color=theme.color("grid"), spacing=36, radius=1.2))

        # ---- Centre visual: one procedural source for the whole 45 s -------------------------------
        source = FunctionSource(draw, size=(1920, 1080), duration=DURATION)
        view = Viewport(source, width=1920, height=1080, position=canvas.bounds.center)

        safe = canvas.safe_area()
        title_box, body = safe.rows((1, 8.2), gap=24)
        left_col, mid_col, right_col = body.columns((1, 1.45, 1), gap=36)
        card = GlassCard(mid_col, opacity=0.5)
        appear(scene, card, SHRINK[0] + 0.5, fade=0.8)
        with scene.at(0):
            scene.add(view)
        target_scale = mid_col.width / 880  # the figure spans ~800 px of the 1920-wide source
        target_y = mid_col.center[1] - 10
        frames(scene, view, "scale", (1, target_scale), *SHRINK, rate_func="emphasized")
        frames(scene, view, "position", (canvas.bounds.center, (mid_col.center[0], target_y)), *SHRINK, "emphasized")

        # ---- 0-15 s fullscreen stage labels ----------------------------------------------------------
        stage_y = canvas.bounds.bottom - 120
        stages = (
            ("1D", "a line", r"(x)", x_c, 0.3, 3.2),
            ("2D", "a square", r"(x,\ y)", y_c, 3.2, 6.2),
            ("3D", "a cube", r"(x,\ y,\ z)", z_c, 6.2, 9.4),
            ("4D", "a tesseract", r"(x,\ y,\ z,\ w)", w_c, 9.4, SHRINK[0] + 0.3),
        )
        for tag, name, coords, color, start, end in stages:
            badge = Text(tag, role="title", color=color, position=(canvas.bounds.center[0] - 300, stage_y))
            label = Text(name, role="heading", color=text, position=(canvas.bounds.center[0] - 60, stage_y))
            eq = math_text(coords, 54, muted, (canvas.bounds.center[0] + 270, stage_y), color_map={"w": w_c})
            appear(scene, Group(badge, label, eq), start, end)
        hint = Text(
            "Each slice is one moment in time",
            role="body",
            color=muted,
            position=(canvas.bounds.center[0], safe.top + 40),
        )
        appear(scene, hint, 12.2, SHRINK[0] + 0.2)

        # ---- Title -----------------------------------------------------------------------------------
        title = theme.fit("Understand 4th Dimension Visually", title_box, role="title", color=TITLE_GREEN)
        appear(scene, title, SHRINK[0] + 0.4, 39.2, fade=0.7)
        closing = theme.fit("Moving along w is moving through time", title_box, role="title", color=w_c)
        appear(scene, closing, 39.4, fade=0.7)

        # ---- Left panel: coordinates, then counting ----------------------------------------------------
        appear(scene, GlassCard(left_col, opacity=0.62), SHRINK[1] - 0.3, fade=0.7)
        inner = left_col.inset(40)
        head_l, vec_box, cap_l, table_box, formula_box = inner.rows((0.5, 2.6, 0.45, 2.6, 0.8), gap=10)
        appear(scene, Text("COORDINATES", role="label", color=muted, position=head_l.center), 17.0)
        vec = vec_box.fit(170, vec_box.height)
        entries = vec.inset(18).rows(4)
        appear(scene, brackets(vec, text), 17.1)
        for k, (sym, color, at) in enumerate(zip("xyzw", AXIS_COLORS, (17.4, 17.8, 18.2, 20.0))):
            item = math_text(sym, 58, color, entries[k].center)
            appear(scene, item, at, fade=0.35)
            if sym == "w":
                pulse(scene, item, at + 0.4, 1.6)
        appear(scene, Text("Four numbers, one point", role="label", color=text, position=cap_l.center), 20.6, PULSE[0])

        rows = table_box.rows(5, gap=4)
        cols = [r.columns((1, 1.4, 1.2)) for r in rows]
        for c, head in zip(cols[0], ("dim", "vertices", "edges")):
            appear(scene, Text(head, role="label", color=muted, position=c.center), PULSE[0])
        for n in range(1, 5):
            at = PULSE[0] + 2 * (n - 1) + 0.2
            color = AXIS_COLORS[n - 1]
            cells = (f"{n}D", str(2**n), str(n * 2 ** (n - 1)))
            row = [
                Text(v, role="heading", color=color if i == 0 else text, position=cols[n][i].center)
                for i, v in enumerate(cells)
            ]
            appear(scene, Group(*row), at, fade=0.35)
            pulse(scene, row[1], at + 0.2, 1.3)
        formula = math_text(r"V = 2^n \qquad E = n\,2^{\,n-1}", 46, TITLE_GREEN, formula_box.center)
        appear(scene, formula, PULSE[1] - 1.4)

        # ---- Right panel: a fourth axis, the rotation, the projection ----------------------------------
        appear(scene, GlassCard(right_col, opacity=0.62), SHRINK[1] - 0.3, fade=0.7)
        inner = right_col.inset(40)
        head_r, axes_box, cap_r, matrix_head, matrix_box, proj_box = inner.rows((0.5, 2.6, 0.45, 0.5, 2.4, 0.8), gap=10)
        appear(scene, Text("A FOURTH DIRECTION", role="label", color=muted, position=head_r.center), 17.0)
        reach = min((axes_box.height - 70) / 1.42, axes_box.width * 0.5)
        ox, oy = axes_box.left + axes_box.width * 0.36, axes_box.bottom - reach * 0.3
        axes = (
            (Arrow((ox, oy), (ox + reach, oy), stroke=x_c, stroke_width=5), "x", (ox + reach + 26, oy), 17.3),
            (Arrow((ox, oy), (ox, oy - reach), stroke=y_c, stroke_width=5), "y", (ox, oy - reach - 30), 17.7),
        )
        for arrow, sym, at_pos, at in axes:
            with scene.at(at):
                scene.add(arrow)
                scene.play(Draw(arrow), run_time=0.6, rate_func="emphasized")
            appear(scene, math_text(sym, 44, arrow.stroke, at_pos), at + 0.4)
        # z drawn oblique (toward the viewer, down-left), as on paper.
        z_end = (ox - reach * 0.42, oy + reach * 0.26)
        z_arrow = Arrow((ox, oy), z_end, stroke=z_c, stroke_width=5)
        with scene.at(18.1):
            scene.add(z_arrow)
            scene.play(Draw(z_arrow), run_time=0.6, rate_func="emphasized")
        appear(scene, math_text("z", 44, z_c, (z_end[0] - 24, z_end[1] + 4)), 18.5)
        # w floats off the axes like the sketch: a direction with no room left on paper.
        w_start = (ox + reach * 0.62, oy - reach * 0.55)
        w_end = (ox + reach * 1.02, oy - reach * 0.98)
        w_arrow = Arrow(w_start, w_end, stroke=w_c, stroke_width=6)
        with scene.at(20.4):
            scene.add(w_arrow)
            scene.play(Draw(w_arrow), run_time=0.7, rate_func="overshoot")
        w_label = math_text("w", 50, w_c, (w_end[0] + 26, w_end[1] + 10))
        appear(scene, w_label, 20.9)
        pulse(scene, w_label, 21.3, 1.5)
        appear(scene, Text("At 90° to x, y and z", role="label", color=text, position=cap_r.center), 21.4)

        # Rotation matrix in the z-w plane, with a live theta read-out driven by the same function.
        m_start = 32.0
        appear(scene, Text("ROTATE IN THE ZW-PLANE", role="label", color=muted, position=matrix_head.center), m_start)
        grid_box = matrix_box.fit(matrix_box.width * 0.86, matrix_box.height * 0.78, align="top")
        appear(scene, brackets(grid_box, text), m_start + 0.2)
        cells = [
            ("1", "0", "0", "0"),
            ("0", "1", "0", "0"),
            ("0", "0", r"\cos\theta", r"-\sin\theta"),
            ("0", "0", r"\sin\theta", r"\cos\theta"),
        ]
        grid_rows = grid_box.inset(12).rows(4)
        for r, row in enumerate(cells):
            for c, (cell, box) in enumerate(zip(row, grid_rows[r].columns((0.6, 0.6, 1.3, 1.3)))):
                live = r >= 2 and c >= 2
                item = math_text(cell, 34, w_c if live else muted, box.center)
                appear(scene, item, m_start + 0.3 + 0.05 * (r * 4 + c), fade=0.3)
        theta_y = grid_box.bottom + (matrix_box.bottom - grid_box.bottom) / 2 + 4
        appear(scene, math_text(r"\theta =", 40, text, (grid_box.center[0] - 60, theta_y)), m_start + 1.2)
        start_deg, end_deg = math.degrees(theta_zw(m_start + 1.2)), math.degrees(theta_zw(DURATION))
        readout = Number(
            start_deg,
            formatter=lambda v: f"{v % 360:.0f}°",
            role="heading",
            color=w_c,
            position=(grid_box.center[0] + 60, theta_y),
        )
        appear(scene, readout, m_start + 1.2)
        frames(scene, readout, "value", (start_deg, end_deg), m_start + 1.2, DURATION)

        proj = math_text(r"x^{\prime} = \frac{d}{d - w}\;x", 46, TITLE_GREEN, proj_box.center)
        appear(scene, proj, 39.6)
        pulse(scene, proj, 40.4, 1.2)

        scene.wait_until(DURATION)
        return scene


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--range", type=float, nargs=2, metavar=("START", "END"), help="Export a source-clock section")
    mode.add_argument("--frame", type=float, metavar="SECONDS")
    mode.add_argument("--preview", action="store_true", help="13-19 s around the shrink, original source time")
    parser.add_argument("--quality", choices=("720p", "1080p", "4k"), default="1080p")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.frame is not None and not 0 <= args.frame < DURATION:
        parser.error("frame time must be in [0, 45)")
    if args.range is not None and not 0 <= args.range[0] < args.range[1] <= DURATION:
        parser.error("range must satisfy 0 <= START < END <= 45")
    scene = build_scene()
    settings = ExportSettings(backend="skia", antialias=1, quality=args.quality, fps=args.fps)
    out = args.output or ROOT / "output" / (
        f"frame-{args.frame:g}.png" if args.frame is not None else "preview.mp4" if args.preview else "4d-preview.mp4"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    source_range = args.range or (
        [args.frame, args.frame] if args.frame is not None else [13, 19] if args.preview else [0, DURATION]
    )
    if args.frame is not None:
        with create_renderer("skia", antialias=1) as renderer:
            save_frame(
                scene,
                args.frame,
                out,
                size=settings.dimensions(scene.canvas),
                renderer=renderer,
                overwrite=args.overwrite,
            )
    else:
        with ExportProgress() as progress:
            render(
                scene,
                out,
                settings=settings,
                start_time=source_range[0],
                end_time=source_range[1],
                overwrite=args.overwrite,
                progress=progress,
            )
    out.with_suffix(".json").write_text(
        json.dumps(
            {"scene_duration": DURATION, "source_range": source_range, "rendering": rendering_identity("skia", scene)},
            indent=2,
        )
    )
    print(out)


if __name__ == "__main__":
    main()
