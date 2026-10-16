# Phase 0 baseline reproduction

Run from the repository root at the revision pinned in the ADR. Use the existing
local environment; no sync/download/install is required. The `uv` cache override
is needed in this restricted workspace because its default cache is read-only.

```bash
UV_CACHE_DIR=/tmp/fc-premium-phase0-uv MPLCONFIGDIR=/tmp/fc-premium-phase0-mpl uv run --offline --no-sync pytest -q
UV_CACHE_DIR=/tmp/fc-premium-phase0-uv MPLCONFIGDIR=/tmp/fc-premium-phase0-mpl uv run --offline --no-sync pytest -q facelesschamp-kit/tests
UV_CACHE_DIR=/tmp/fc-premium-phase0-uv MPLCONFIGDIR=/tmp/fc-premium-phase0-mpl uv run --offline --no-sync pytest -q facelesschamp-agent/tests
UV_CACHE_DIR=/tmp/fc-premium-phase0-uv uv run --offline --no-sync ruff check src tests examples
UV_CACHE_DIR=/tmp/fc-premium-phase0-uv uv run --offline --no-sync ruff format --check src tests examples
```

Core: 1278 passed, 2 opt-in browser skips. Kit: 255 passed. Agent: 41 passed.
Lint passes. Formatting reports the four pre-existing files named in the ADR;
leave them unchanged during Phase 0. Run suites separately.

Copy the Python block below into `/tmp/fc-premium-phase0-audit.py`. It is an audit
driver preserved as documentation, not a library/test/example implementation.
It calls only existing APIs. Capture then benchmark after the test suites and
other render work finish; do not time benchmarks concurrently with tests.
`capture` overwrites these generated evidence files and its short preview.
`benchmark` uses five trials of twelve changing source times per worker; each
mode/resolution runs in a fresh process, followed by twenty-four cached holds.

```bash
MPLCONFIGDIR=/tmp/fc-premium-phase0-mpl .venv/bin/python /tmp/fc-premium-phase0-audit.py --stage capture
MPLCONFIGDIR=/tmp/fc-premium-phase0-mpl .venv/bin/python /tmp/fc-premium-phase0-audit.py --stage benchmark
ffprobe -v error -count_frames -show_entries stream=codec_name,width,height,r_frame_rate,nb_read_frames,pix_fmt -show_entries format=duration,size -of json output/premium_effects/phase0/baseline-spring.mp4
ffmpeg -v error -i output/premium_effects/phase0/baseline-spring.mp4 -f null -
ffmpeg -v error -ss 0.766666667 -i output/premium_effects/phase0/baseline-spring.mp4 -frames:v 1 -y output/premium_effects/phase0/decoded-023.png
```

The run produced six 960x540/AA1 PNGs and a labeled 3x2 contact sheet, 576
raw-hash comparisons at 480x270/AA1, a 2-second 960x540/30-FPS silent preview,
and a simple 4K/AA1 smoke PNG. Inspect the sheet, individual PNGs, decoded
frame and smoke frame. Preview/decode/inspection outcomes in `baseline.json`
were recorded after the actual run; the script intentionally does not assert
that a future human inspection has occurred.

Timing variation is expected on this AMD A6-9225 CPU. Cache bytes are explicitly
counted for decoded images, sprites and scene frames. RSS includes native Pillow
buffers; it is whole-process memory, not an incremental effect-memory claim.
`close()` reference release and RSS returning to the OS are separate questions.

```python
"""Read-only System 02 baseline; uses only existing public rendering APIs."""
from __future__ import annotations

import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import platform
import random
import resource
import statistics
import subprocess
import sys
from time import perf_counter

import PIL
from PIL import Image as PI, ImageDraw, ImageFilter
from faceless_champ import (
    BarChart, Bounds, Canvas, ChartStyle, Circle, ColorScheme, Group, Image,
    PillowRenderer, Rectangle, RectangleMask, Scene, ShadowStyle, Spring,
    Text, card_content_bounds, card_surface,
)
from faceless_champ.typography import load_font

ROOT = Path.cwd()
EVIDENCE = ROOT / "docs/decisions/premium-effects-baseline"
OUTPUT = ROOT / "output/premium_effects/phase0"
TIMES = (0, .1, .37, .77, 1, 2)


def scene_for(name):
    dark = name in {"shadow_dark", "spring_group", "masked_group"}
    bg, fg = ("#111827", "#ECF3FF") if dark else ("#E8E6E2", "#14202E")
    scene = Scene(Canvas(960, 540, bg))
    shadow = None if name == "solid_light" else ShadowStyle(
        color="#00000088" if dark else "#00000026")
    bounds = Bounds(180, 135, 780, 405) if shadow is None else Bounds(120, 75, 840, 465)
    card = card_surface(bounds, fill="#253852" if dark else "#FFFFFF", radius=36, shadow=shadow)
    label = Text(name.replace("_", " ").upper(), font_size=28, color=fg, position=(480, 270))
    if name == "spring_group":
        group = Group(card, label)
        scene.add(group)
        scene.play(group.animate.move_to(520, 258).rotate_to(8).scale_to(.9),
                   run_time=2, rate_func=Spring(100, 10, 1))
    elif name == "masked_group":
        accent = Circle(radius=80, fill="#58DFC180", stroke=None, position=(710, 270), z_index=1)
        group = Group(card, label, accent, mask=RectangleMask(630, 290),
                      scale_x=1.08, scale_y=.85, rotation=-9, opacity=.72)
        scene.add(group)
    elif name == "chart_card":
        inner = card_content_bounds(bounds, shadow=shadow, padding=30)
        style = ChartStyle(scheme=replace(ColorScheme.named("clean-flow"), surface="#00000000"),
                           grid=False, font_size=17)
        chart = BarChart(("CPU", "Reuse", "Seek"), {"Baseline": (4, 7, 6)},
                         width=inner.width, height=inner.height, position=inner.center, style=style)
        scene.add(card, chart)
    else:
        scene.add(card, label)
    scene.wait_until(2.25)
    return scene


def rss_kib():
    values = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines() if ":" in line)
    return int(values["VmRSS"].split()[0])


def cache_info(renderer):
    sizes = {}
    for name in ("_sprites", "_images", "_scene_frames", "_equations", "_caption_sprites", "_code_sprites"):
        sizes[name] = len(getattr(renderer, name))
    sizes["decoded_rgba_bytes"] = sum(f.width * f.height * 4 for frames, _ in renderer._images.values() for f in frames)
    sizes["sprite_rgba_bytes"] = sum(f.width * f.height * 4 for f in renderer._sprites.values())
    sizes["scene_frame_bytes"] = renderer._frame_cache_bytes
    return sizes


def capture():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    names = ("solid_light", "shadow_light", "shadow_dark", "spring_group", "masked_group", "chart_card")
    records = []
    sheet = PI.new("RGB", (1440, 604), "#D7DBE2")
    for i, name in enumerate(names):
        scene = scene_for(name)
        with PillowRenderer(1) as renderer:
            frame = renderer.frame(scene, .77, (960, 540))
            path = EVIDENCE / f"{i + 1:02d}-{name}.png"
            frame.save(path)
            thumb = frame.convert("RGB").resize((480, 270), PI.Resampling.LANCZOS)
            x, y = i % 3 * 480, i // 3 * 302
            sheet.paste(thumb, (x, y))
            ImageDraw.Draw(sheet).text((x + 12, y + 278), f"{i+1:02d}  {name}  /  t=0.77s  /  AA1",
                                       fill="#172333", font=load_font(None, 15))
            records.append({"name": name, "path": str(path.relative_to(ROOT)), "time": .77,
                            "rgba_sha256": sha256(frame.tobytes()).hexdigest(), "size": frame.size,
                            "surface_png_sha256": [sha256(e.component.source_bytes).hexdigest()
                                for e in scene.entries if isinstance(e.component, Image)]})
    sheet.save(EVIDENCE / "contact-sheet.png")
    # Cache modes, FPS workloads, and arbitrary source-time seek orders.
    comparisons = 0
    for name in names:
        scene = scene_for(name)
        for cache in (0, 64):
            with PillowRenderer(1, frame_cache_mb=cache) as renderer:
                expected = {t: sha256(renderer.frame(scene, t, (480, 270)).tobytes()).hexdigest() for t in TIMES}
                shuffled = list(TIMES)
                random.Random(20261016).shuffle(shuffled)
                for order in (TIMES, tuple(reversed(TIMES)), tuple(shuffled), TIMES * 2):
                    for t in order:
                        assert sha256(renderer.frame(scene, t, (480, 270)).tobytes()).hexdigest() == expected[t]
                        comparisons += 1
                for fps in (24, 30, 60):
                    for i in range(0, fps * 2, max(1, fps // 6)):
                        renderer.frame(scene, i / fps, (480, 270))
                    for t in TIMES:
                        assert sha256(renderer.frame(scene, t, (480, 270)).tobytes()).hexdigest() == expected[t]
                        comparisons += 1
                renderer.close()
                assert all(not getattr(renderer, key) for key in ("_images", "_sprites", "_scene_frames", "_fonts"))
    # Show that direct RGBA blur darkens color with decreasing coverage.
    patch = PI.new("RGBA", (80, 80))
    ImageDraw.Draw(patch).rectangle((25, 25, 55, 55), fill=(255, 0, 0, 255))
    blurred = patch.filter(ImageFilter.GaussianBlur(5))
    colored_probe = {str(x): blurred.getpixel((x, 40)) for x in (15, 20, 25, 30, 40)}
    assert 0 < colored_probe["20"][0] < 255 and colored_probe["20"][0] == colored_probe["20"][3]
    # Current member-opacity semantics: two half-opacity overlapping leaves give alpha 192.
    a = Rectangle(width=100, height=100, fill="red", stroke=None, position=(100, 80))
    b = Rectangle(width=100, height=100, fill="blue", stroke=None, position=(100, 80))
    overlap = Scene(Canvas(200, 160, "#00000000")).add(Group(a, b, opacity=.5, mask=RectangleMask(60, 60))).wait(1)
    with PillowRenderer(1) as renderer:
        overlap_pixel = renderer.frame(overlap, 0, (200, 160)).getpixel((100, 80))
    assert overlap_pixel[3] == 192
    # One high-resolution smoke frame, small native sprite/scene only, no masked 4K stress.
    with PillowRenderer(1) as renderer:
        start = perf_counter()
        smoke = renderer.frame(scene_for("shadow_light"), .77, (3840, 2160))
        smoke_ms = (perf_counter() - start) * 1000
        smoke.save(OUTPUT / "4k-shadow-smoke.png")
    source_files = subprocess.check_output(["git", "ls-files", "src", "tests", "examples", "pyproject.toml", "uv.lock"], text=True).splitlines()
    data = {
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
        "python": platform.python_version(), "pillow": PIL.__version__, "platform": platform.platform(),
        "cpu": next(line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name")),
        "frames": records, "deterministic_hash_comparisons": comparisons,
        "seek_validation": "480x270 AA1; caches 0/64 MiB; forward/reverse/shuffled/repeated and 24/30/60 FPS source sampling; no three-FPS encoded-video claim",
        "direct_rgba_blur_probe": colored_probe, "overlapping_group_opacity_pixel": overlap_pixel,
        "smoke_4k": {"path": str((OUTPUT / "4k-shadow-smoke.png").relative_to(ROOT)), "render_ms_including_scene_construction": smoke_ms, "size": smoke.size},
        "source_sha256": {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in source_files},
    }
    (EVIDENCE / "baseline.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({k:v for k,v in data.items() if k not in {"source_sha256", "frames"}}, indent=2), flush=True)
    video = scene_for("spring_group").render(OUTPUT / "baseline-spring.mp4", width=960, height=540,
        fps=30, antialias=1, preset="fast", crf=20, end_time=2, overwrite=True)
    print(f"Preview: {video}", flush=True)


def benchmark_scene(mode):
    scene = Scene(Canvas(960, 540, "#111827"))
    for i in range(6):
        x, y = 160 + i % 3 * 320, 155 + i // 3 * 240
        if mode == "plain_motion":
            face = Rectangle(width=210, height=120, corner_radius=18, fill="#253852", stroke=None, position=(x, y))
        else:
            face = card_surface(Bounds(x-140, y-95, x+140, y+95), radius=18, fill="#253852",
                                shadow=ShadowStyle(blur=6, offset=(0, 4)))
        label = Text(f"CARD {i+1}", position=(x, y), font_size=21, color="#ECF3FF")
        kwargs = {"mask": RectangleMask(270, 180), "scale_x": .95, "scale_y": .9} if mode == "masked_affine" else {}
        group = Group(face, label, **kwargs)
        with scene.at(0):
            scene.add(group)
            scene.play(group.animate.move_to(x+10, y-12), run_time=2, rate_func=Spring(100, 10, 1))
    scene.wait_until(2.25)
    return scene


def worker(mode, width, aa):
    size = (width, width * 9 // 16)
    start = perf_counter()
    scene = benchmark_scene(mode)
    build_ms = (perf_counter()-start)*1000
    r = PillowRenderer(aa)
    start = perf_counter()
    r.frame(scene, .1, size)
    cold_ms = (perf_counter()-start)*1000
    for t in (.2, .3, .4):
        r.frame(scene, t, size)
    trials = []
    for _ in range(5):
        start = perf_counter()
        for i in range(12):
            r.frame(scene, .05 + i / 7, size)
        trials.append((perf_counter()-start)*1000/12)
    r.frame(scene, 2, size)
    start = perf_counter()
    for _ in range(24):
        r.frame(scene, 2, size)
    hold_ms = (perf_counter()-start)*1000/24
    cache = cache_info(r)
    before = rss_kib()
    r.close()
    after = rss_kib()
    closed = cache_info(r)
    assert all(v == 0 for v in closed.values())
    print(json.dumps({"mode":mode, "size":size, "antialias":aa, "construction_ms":build_ms,
        "cold_frame_ms":cold_ms, "trials_ms_per_frame":trials, "median_ms_per_frame":statistics.median(trials),
        "hold_ms_per_frame":hold_ms, "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "rss_before_close_kib":before, "rss_after_close_kib":after,
        "cache_before_close":cache, "cache_after_close":closed}))


def benchmark():
    rows=[]
    for width in (960, 1920):
        for mode in ("plain_motion", "surface_motion", "masked_affine"):
            raw = subprocess.check_output([sys.executable, __file__, "--worker", mode, str(width), "1"], text=True)
            row = json.loads(raw)
            rows.append(row)
            print(json.dumps(row), flush=True)
    data = json.loads((EVIDENCE / "baseline.json").read_text())
    data["benchmarks"] = rows
    data["benchmark_method"] = "Separate fresh subprocess per mode/size; AA1; 3 warmup frames, 5 trials x 12 changing-time frames, 24 holds; render-only timings excluding FFmpeg; whole-process native-inclusive Linux RSS; run after tests finish. Static source caches are not all byte-bounded."
    (EVIDENCE / "baseline.json").write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("capture", "benchmark"))
    parser.add_argument("--worker", nargs=3)
    args=parser.parse_args()
    if args.worker:
        worker(args.worker[0], int(args.worker[1]), int(args.worker[2]))
    elif args.stage == "capture":
        capture()
    elif args.stage == "benchmark":
        benchmark()
```
