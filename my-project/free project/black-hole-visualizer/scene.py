"""Black hole visualizer: a 30-second Faceless Champ scene over a GPU geodesic tracer.

python scene.py --frame 3 9 17 23 28          # 720p stills
python scene.py --preview 8 14                # 720p MP4 excerpt
python scene.py --audit                       # design audit of the overlays
python scene.py                               # full 1080p render (2x2 supersampled)
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import physics
from engine import CameraRig, Shot, source

from faceless_champ import (
    Bloom,
    Callout,
    Circle,
    Dot,
    Draw,
    EffectStack,
    FadeIn,
    FadeOut,
    GlassCard,
    GradientStop,
    LinearGradient,
    Number,
    Polyline,
    Rectangle,
    Scene,
    Text,
    Theme,
    with_alpha,
)

ROOT = Path(__file__).resolve().parent
DURATION = 30.0
SIZE = (1920, 1080)
SHIFT_RIGHT = -0.40  # lens shift that parks the hole in the right half during the diagram beat

# Camera choreography, in units of M (horizon r = 2). Inclination 90° is edge-on.
RIG = CameraRig(
    [
        Shot(0.0, 78, 85, -40, fov=30),
        Shot(6.5, 40, 83, -8, fov=32),
        Shot(10.5, 36, 79, 10, fov=32, shift=SHIFT_RIGHT),
        Shot(14.0, 34, 76, 22, fov=32, shift=SHIFT_RIGHT),
        Shot(16.0, 31, 76, 28, fov=40),
        Shot(20.0, 29, 76, 30, fov=40),
        Shot(23.6, 38, 24, 90, fov=34),
        Shot(25.6, 30, 55, 130, fov=36),
        Shot(30.0, 15, 86, 175, fov=44),
    ]
)

theme = Theme.named("midnight")


# --------------------------------------------------------------------------- beats


def geodesic_diagram(scene: Scene, box, start: float):
    """2D equatorial slice: photon paths from physics.trace_planar_ray, to scale."""
    cx, cy = box.center
    half = 13.0  # half-width of the slice, in M
    scale = min(box.width, box.height) / (2 * half)

    def to_px(p):
        return (cx + p[0] * scale, cy - p[1] * scale)

    rings = [
        Circle(
            physics.R_ISCO * scale,
            position=(cx, cy),
            fill=None,
            stroke=theme.color("tertiary"),
            stroke_width=2,
            opacity=0.8,
        ),
        Circle(physics.R_PHOTON * scale, position=(cx, cy), fill=None, stroke=theme.color("secondary"), stroke_width=2),
        Circle(
            physics.RS * scale,
            position=(cx, cy),
            fill=theme.color("background"),
            stroke=theme.color("text"),
            stroke_width=2,
        ),
    ]
    rays = []
    for b in (-9.5, -7.0, -4.6, -2.2, 0.4, 2.6, 4.6, 5.21, 6.2, 8.2, 10.5):
        ray = physics.trace_planar_ray(b, start_x=-half, max_r=half * 1.45)
        pts = [p for p in ray.points if abs(p[0]) <= half and abs(p[1]) <= half]
        if len(pts) < 2:
            continue
        pts = pts[:: max(1, len(pts) // 260)] + [pts[-1]]
        color = theme.color("highlight") if ray.captured else theme.color("primary")
        rays.append(
            Polyline([to_px(p) for p in pts], stroke=color, stroke_width=3, line_cap="round", fill=None, opacity=0.9)
        )

    for i, ring in enumerate(rings):
        scene.play_at(start + 0.15 * i, Draw(ring), run_time=0.9, rate_func="emphasized")
    for i, ray in enumerate(rays):
        scene.play_at(start + 0.7 + 0.12 * i, Draw(ray), run_time=1.6, rate_func="decelerate")
    return rings + rays


def legend(column, top: float):
    items = []
    entries = (
        ("text", "Horizon · 1 rs"),
        ("secondary", "Photon sphere · 1.5 rs"),
        ("tertiary", "Last stable orbit · 3 rs"),
    )
    for i, (color, label) in enumerate(entries):
        y = top + i * 46
        x = column.left
        items.append(Dot((x + 8, y), radius=8, color=color))
        text = Text(label, role="label", color="text")
        items.append(text.move_to(x + 32 + text.bounds.width / 2, y))
    return items


def hud(scene: Scene, area, start: float, end: float):
    """Live readouts synced to the camera rig: distance and static-observer clock rate."""
    right = area.right - 8
    top = area.top + 24
    rows = []
    numbers = []

    def readouts(t):
        r = RIG.state(t).r
        return r / physics.RS, physics.clock_rate(r)

    fields = (("DISTANCE", ".1f", " rs"), ("CLOCK RATE", ".3f", "×"))
    for i, ((caption, fmt, suffix), v0) in enumerate(zip(fields, readouts(start + 0.5))):
        y = top + i * 124
        label = Text(caption, role="label", color="muted", tracking=0.14)
        label.move_to(right - label.bounds.width / 2, y)
        value = Number(v0, role="heading", format_spec=fmt, suffix=suffix, width=260, align="right")
        value.move_to(right - 130, y + 48)
        rows += [label, value]
        numbers.append(value)

    scene.reveal(*rows, at=start, stagger=0.08)
    step = 0.25
    t = start + 0.5
    while t + step <= end - 0.6:
        for value, target in zip(numbers, readouts(t + step)):
            scene.play_at(t, value.animate.value_to(target), run_time=step, rate_func="linear")
        t += step
    # Exit authored last: no animation may be added after a removal is scheduled.
    with scene.at(end - 0.6):
        scene.play(*(FadeOut(item) for item in rows), run_time=0.6, rate_func="accelerate")
        scene.remove(*rows)


def scrim(height=460):
    """Bottom gradient that keeps copy readable over the bright disk."""
    bg = theme.color("background")
    fill = LinearGradient((GradientStop(0, with_alpha(bg, 0)), GradientStop(1, with_alpha(bg, 0.82))), angle=90)
    return Rectangle(width=SIZE[0], height=height, position=(SIZE[0] / 2, SIZE[1] - height / 2), fill=fill, stroke=None)


def build():
    with theme.use():
        scene = Scene(theme.canvas(*SIZE))
        canvas = scene.canvas
        area = canvas.safe_area()

        # -- the simulation itself, with GPU bloom on the hot inner disk
        view = source(RIG, DURATION, size=SIZE, samples=SAMPLES).viewport(
            width=SIZE[0],
            height=SIZE[1],
            position=canvas.bounds.center,
            effects=EffectStack(bloom=Bloom(radius=18, threshold=0.62, intensity=0.42)),
        )
        scene.add(view)
        scene.play(FadeIn(view), run_time=1.6, rate_func="decelerate")

        # -- beat 1: title
        intro = area.inset(0, bottom=40).rows((3, 1))[1]
        title = Text("Where light bends back", role="display")
        title.move_to(intro.left + title.bounds.width / 2, intro.center[1])
        eyebrow = theme.text("SCHWARZSCHILD BLACK HOLE", role="label", tracking=0.18)
        eyebrow.move_to(intro.left + eyebrow.bounds.width / 2, title.bounds.top - 36)
        sub = Text("Every pixel is a photon traced through curved spacetime.", role="body", color="muted")
        sub.move_to(intro.left + sub.bounds.width / 2, title.bounds.bottom + 44)
        scene.reveal(scrim(), at=0.8, style="fade", until=6.6)
        scene.reveal(eyebrow, title, sub, at=1.0, stagger=0.14, until=6.4)

        # -- beat 2: geodesic diagram on a card (2D), hole parked right
        card_box = area.columns((5, 7), gap=48)[0].inset(0, y=10)
        card = GlassCard(card_box, opacity=0.8)
        inner = card_box.inset(48)
        heading = Text("How light falls in", role="heading")
        heading.move_to(inner.left + heading.bounds.width / 2, inner.top + heading.bounds.height / 2)
        diagram_box = inner.inset(0, top=heading.bounds.height + 24, bottom=230)
        scene.reveal(card, heading, at=7.0, stagger=0.1, until=14.6)
        diagram = geodesic_diagram(scene, diagram_box, start=7.5)
        keys = legend(inner, diagram_box.bottom + 40)
        note = Text("Aimed within 2.6 rs: captured.", role="caption", color="muted")
        note.move_to(inner.left + note.bounds.width / 2, inner.bottom - note.bounds.height / 2)
        scene.reveal(*keys, note, at=9.4, stagger=0.1, until=14.6)
        with scene.at(14.1):
            scene.play(*(FadeOut(item) for item in diagram), run_time=0.5)

        # -- beat 3: annotate the 3D image (camera holds azimuth 28-30° from 16 to 20 s)
        t_mid = 18.0
        cam_az = math.radians(RIG.values(t_mid)["az"])
        r_mark = 8.0
        approaching = RIG.project(
            (r_mark * math.cos(cam_az - math.pi / 2), r_mark * math.sin(cam_az - math.pi / 2), 0), t_mid, SIZE
        )
        receding = RIG.project(
            (r_mark * math.cos(cam_az + math.pi / 2), r_mark * math.sin(cam_az + math.pi / 2), 0), t_mid, SIZE
        )
        centre = RIG.project((0, 0, 0), t_mid, SIZE)
        edge = (RIG.shadow_edge(t_mid, SIZE) + 6) / math.sqrt(2)
        ring = (centre[0] - edge, centre[1] - edge)
        callouts = [
            Callout("Photon ring", ring, offset=(-130, -150)),
            Callout("Approaching · blueshifted", approaching, offset=(40, 260)),
            Callout("Receding · redshifted", receding, offset=(-40, 330)),
        ]
        scene.reveal(scrim(), at=15.9, style="fade", until=20.8)
        for i, c in enumerate(callouts):
            scene.reveal(c.dot, c.line, c.label, at=16.2 + 0.6 * i, stagger=0.12, until=20.6)

        # -- beat 4 + 5: polar view, then the dive; HUD runs throughout
        hud(scene, area, start=6.8, end=29.0)
        polar = Text("Seen from the pole", role="heading")
        polar.move_to(area.left + polar.bounds.width / 2, area.bottom - polar.bounds.height / 2)
        scene.reveal(scrim(), at=21.8, style="fade", until=29.6)
        scene.reveal(polar, at=22.0, until=25.2)

        closing = Text("Inside 1 rs, even light stays.", role="title")
        closing.move_to(area.left + closing.bounds.width / 2, area.bottom - closing.bounds.height / 2)
        scene.reveal(closing, at=26.2, until=29.4)

        fade = Rectangle(
            width=SIZE[0],
            height=SIZE[1],
            position=canvas.bounds.center,
            fill=theme.color("background"),
            stroke=None,
            opacity=0,
        )
        with scene.at(29.0):
            scene.play(fade.animate.opacity_to(1), run_time=1.0, rate_func="accelerate")
        scene.wait_until(DURATION)
    return scene


SAMPLES = 1


def main(argv=None):
    global SAMPLES
    from faceless_champ import ExportProgress, ExportSettings, create_renderer, design_audit, render, save_frame

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--frame", type=float, nargs="+", metavar="T")
    mode.add_argument("--preview", type=float, nargs=2, metavar=("START", "END"))
    mode.add_argument("--audit", action="store_true")
    parser.add_argument("--quality", choices=("720p", "1080p", "4k"))
    parser.add_argument("--samples", type=int, help="supersampling grid per axis (default 1 for checks, 2 for full)")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    checking = bool(args.frame or args.preview)
    short = {"720p": 720, "1080p": 1080, "4k": 2160}[args.quality or ("720p" if checking else "1080p")]
    size = (short * 16 // 9, short)
    SAMPLES = args.samples or (1 if checking else 2)
    scene = build()
    out = ROOT / "output"
    out.mkdir(exist_ok=True)

    if args.audit:
        report = design_audit(scene)
        for f in report.findings:
            print(f"[{f.severity}] t={f.time:.2f}s {f.message}")
        print("audit ok" if report.ok else "audit has findings")
        return
    if args.frame:
        with create_renderer("moderngl", antialias=1) as renderer:
            for t in args.frame:
                path = out / f"frame-{t:05.2f}.png"
                save_frame(scene, t, path, size=size, renderer=renderer, overwrite=True)
                print(path)
        return

    start, end = args.preview or (0.0, DURATION)
    path = args.output or out / ("preview.mp4" if args.preview else "black-hole-visualizer.mp4")
    settings = ExportSettings(
        width=size[0],
        height=size[1],
        fps=args.fps,
        backend="moderngl",
        antialias=1,
        crf=20 if args.preview else 14,
        preset="veryfast" if args.preview else "slow",
    )
    with ExportProgress() as progress:
        render(scene, path, settings=settings, start_time=start, end_time=end, overwrite=True, progress=progress)
    print(path)


if __name__ == "__main__":
    main()
