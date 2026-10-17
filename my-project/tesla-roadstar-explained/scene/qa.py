"""Source-clock, physical, layout and encoded-media evidence for this project."""

import hashlib
import html
import itertools
import json
import math
import subprocess
from dataclasses import asdict
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw

from . import ASSETS, END, FPS, OUTPUT, ROOT
from . import physics as p
from .drawing import Painter, font
from .equations import BEATS
from .timing import CHAPTERS, CONTEXT, SHOTS, TITLES, TRACK, transcript


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def source_integrity():
    names = ("audio.mp3", "cue-per-word.srt", "normal-subtitle.srt", "scene-plan.md")
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}
    path = ROOT / "source-fingerprints.json"
    if path.exists():
        if json.loads(path.read_text()) != hashes:
            raise ValueError("Supplied source files changed; inspect source-fingerprints.json")
    else:
        write_json(path, hashes)
    return hashes


def check_project(renderer, geometry=True):
    from .model import components, export_refined
    from .story import all_expressions, flow_view

    hashes = source_integrity()
    assert len(TRACK.cues) == 1975 and len(CONTEXT.cues) == 247
    assert len(SHOTS) == 40 and len(CHAPTERS) == 10
    assert abs(TRACK.duration - 738.12) < 1e-8
    assert SHOTS[0].start == 0 and SHOTS[-1].end == END
    assert all(a.end == b.start for a, b in itertools.pairwise(SHOTS))
    assert tuple(c.index for c in TRACK.cues) == tuple(range(1, 1976))
    assert sum(s.end_cue - s.cue + 1 for s in SHOTS) == 1975
    overlaps = [
        (a.index, b.index, round(a.end - b.start, 6)) for a, b in zip(TRACK.cues, TRACK.cues[1:]) if a.end > b.start
    ]
    assert overlaps == [
        (436, 437, 0.001),
        (670, 671, 0.001),
        (824, 825, 0.001),
        (1037, 1038, 0.001),
        (1240, 1241, 0.001),
    ]
    # Numerical invariants, including actual friction versus capacity.
    for a in np.linspace(0, np.pi, 1001):
        state = p.loop(a)
        net = (
            (state["normal"] - p.SUCTION) * state["inward"]
            + np.array((0, 0, -p.WEIGHT))
            + state["friction"] * state["tangent"]
        )
        np.testing.assert_allclose(net, p.MASS * state["centripetal"] * state["inward"], atol=1e-8)
        assert state["normal"] >= 0 and abs(state["friction"]) <= state["normal"]
    for t in np.linspace(0, p.landing(0)["end"], 1001):
        s = p.landing(t)
        assert s["height"] >= 0
        if not s["contact"]:
            assert abs(p.MASS * s["acceleration"] - (s["thrust"] - p.WEIGHT)) < 1e-8
    assert abs(p.roll(1.6)["theta"] - np.pi) < 1e-9 and p.roll(1.6)["omega"] == 0
    for t in np.linspace(p.RELEASE_TIME, p.REPLAY_TIME - 1e-6, 100):
        s = p.replay(t)
        assert s.normal == 0 and s.suction == 0
    for expression in all_expressions():
        Painter((960, 540), renderer.math, renderer.math_cache).equation(expression, (25, 25))
    flow_view()  # Enforce readable labels that actually fit their control nodes.
    meshes = {}
    if geometry:
        meshes = export_refined()
        c = components()
        assert all(c[name].is_manifold for name in ("body", "canopy", "chassis", "tanks", "tires", "skirts", "nozzles"))
        assert abs(c["tires"].bounds[4] + p.CG_HEIGHT) < 1e-6
        assert len(c["rotors"]) == 4
        for mode in (
            "hero",
            "assembly",
            "model",
            "fans",
            "slope",
            "wall",
            "loop",
            "replay",
            "roll",
            "tanks",
            "nozzle",
            "control",
            "landing",
            "hover",
        ):
            renderer.view(mode)
    assets = json.loads((ASSETS / "13_Generated/provenance.json").read_text())
    for asset in assets["assets"]:
        path = ASSETS / "13_Generated" / asset["filename"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == asset["sha256"]
    data = {
        "passed": True,
        "source_hashes": hashes,
        "word_cues": 1975,
        "context_cues": 247,
        "preserved_overlaps": overlaps,
        "shots": 40,
        "chapters": 10,
        "duration": END,
        "fps": FPS,
        "frame_count": round(END * FPS),
        "full_export_verified": False,
        "checkpoints": p.checkpoints(),
        "meshes": meshes,
        "generated_images": len(assets["assets"]),
        "equations_typeset": len(all_expressions()),
    }
    write_json(OUTPUT / "checks.json", data)
    write_json(
        ROOT / "cue-plan.json",
        {
            "chapters": [
                {"chapter": i + 1, "title": TITLES[i], "start": a, "end": b} for i, (a, b) in enumerate(CHAPTERS)
            ],
            "shots": [
                {
                    **asdict(s),
                    "id": s.id,
                    "narration": transcript(s),
                    "equation_cues": [b.cue for b in BEATS.get(s.chapter, ()) if s.cue <= b.cue <= s.end_cue],
                }
                for s in SHOTS
            ],
        },
    )
    return data


def layout_findings(boxes):
    result = []
    for box in boxes:
        x1, y1, x2, y2 = box["bounds"]
        if min(x1, y1) < -1 or x2 > 1921 or y2 > 1081:
            result.append({"code": "OUTSIDE_CANVAS", **box})
    for i, a in enumerate(boxes):
        for b in boxes[i + 1 :]:
            x1, y1, x2, y2 = a["bounds"]
            xx1, yy1, xx2, yy2 = b["bounds"]
            dx, dy = min(x2, xx2) - max(x1, xx1), min(y2, yy2) - max(y1, yy1)
            # Ignore an exact duplicate draw, not repeated labels at new positions.
            duplicate = a["tag"] == b["tag"] and a["bounds"] == b["bounds"]
            if dx > 3 and dy > 3 and not duplicate:
                result.append({"code": "TEXT_OVERLAP", "a": a, "b": b})
    return result


def audit_layout():
    from .story import RoadsterRenderer

    times = {float(t) for t in np.arange(0, END, 0.5)}
    events = [s.start for s in SHOTS] + [b.time for beats in BEATS.values() for b in beats]
    for t in events:
        times.update(max(0, min(END - 0.001, t + offset)) for offset in (-1 / 30, 0, 1 / 30, 0.6, 1.2))
    findings = []
    with RoadsterRenderer(geometry=False) as renderer:
        for count, t in enumerate(sorted(times), 1):
            renderer.layout_at(t)
            findings.extend(
                {"time": t, "shot": renderer.last_state["shot"], **x} for x in layout_findings(renderer.last_layout)
            )
            if count % 300 == 0:
                print(f"Layout audit: {count}/{len(times)} samples", flush=True)
    data = {
        "samples": len(times),
        "sample_stride_seconds": 0.5,
        "measurement_resolution": [3840, 2160],
        "findings": findings,
        "passed": not findings,
        "method": "Native 4K text/equation bounds and projected force labels; image layers reviewed separately",
    }
    write_json(OUTPUT / "layout-audit.json", data)
    return data


def storyboard(renderer, master):
    folder = OUTPUT / "storyboard"
    folder.mkdir(parents=True, exist_ok=True)
    frames = []
    findings = []
    for s in SHOTS:
        times = (s.start + min(3, (s.end - s.start) * 0.25), s.end - min(1.1, (s.end - s.start) * 0.15))
        for phase, t in zip(("established", "accumulated"), times):
            file = f"{s.id}-{phase}-{t:09.3f}.png"
            image = renderer.frame(master, t, (1280, 720))
            image.save(folder / file)
            issues = layout_findings(renderer.last_layout)
            findings.extend({"shot": s.id, "time": t, **x} for x in issues)
            frames.append(
                {
                    "shot": s.id,
                    "chapter": s.chapter,
                    "time": t,
                    "phase": phase,
                    "image": file,
                    "name": s.name,
                    "cue_start": s.cue,
                    "cue_end": s.end_cue,
                    "narration": transcript(s),
                }
            )
        print(f"Storyboard {s.id}: {s.start:.3f}–{s.end:.3f}", flush=True)
    write_json(folder / "frames.json", frames)
    write_json(folder / "layout-findings.json", findings)
    sheets = []
    for chapter in range(1, 11):
        entries = [f for f in frames if f["chapter"] == chapter]
        sheet = Image.new("RGB", (1600, 1040), "#05070B")
        draw = ImageDraw.Draw(sheet)
        for i, f in enumerate(entries):
            with Image.open(folder / f["image"]) as im:
                thumb = im.resize((780, 439), Image.Resampling.LANCZOS)
            x, y = 10 + (i % 2) * 800, 10 + (i // 2) * 260
            # Eight samples per chapter arranged as two columns / four rows.
            thumb = thumb.resize((430, 242), Image.Resampling.LANCZOS)
            sheet.paste(thumb, (x, y))
            draw.text((x + 440, y + 20), f"{f['shot']}\n{f['phase']}\n{f['time']:.3f} s", font=font(20), fill="white")
        path = folder / f"chapter-{chapter:02d}.jpg"
        sheet.save(path, quality=94)
        sheets.append(path)
    cards = []
    for f in frames:
        cards.append(f'''<article data-chapter="{f["chapter"]}"><a href="{f["image"]}"><img loading="lazy" src="{f["image"]}"></a>
        <h3>{f["shot"]} · {html.escape(f["name"])} · {f["time"]:.3f}s</h3><p>{f["phase"]} · cues {f["cue_start"]}–{f["cue_end"]}</p>
        <details><summary>Narration</summary>{html.escape(f["narration"])}</details></article>''')
    page = (
        """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Roadster engineering film · storyboard</title><style>body{background:#000;color:#f3faff;font:16px system-ui;margin:32px}
    h1{color:#57edff}main{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}img{width:100%}article{border-bottom:1px solid #214357;padding-bottom:24px}
    select,button{font:inherit;background:#081522;color:white;padding:10px;border:1px solid #57edff}p,details{color:#9cb6c9}h3{font-weight:500}
    @media(max-width:850px){main{grid-template-columns:1fr}}</style><h1>Roadster: mathematics behind the maneuver</h1>
    <p>40 shots · 80 source-clock frames · 4K/30 target · illustrative engineering reconstruction</p>
    <p>Full export intentionally unrendered. <a style="color:#57edff" href="../index.html">Narrated preview player</a> · <a style="color:#57edff" href="../verification.json">Verification evidence</a></p>
    <label>Chapter <select id="chapter"><option value="all">All</option>"""
        + "".join(f'<option value="{i}">{i:02d} · {TITLES[i - 1]}</option>' for i in range(1, 11))
        + """</select></label><hr><main>"""
        + "".join(cards)
        + """</main>
    <script>document.querySelector('#chapter').onchange=e=>document.querySelectorAll('article').forEach(a=>a.hidden=e.target.value!=='all'&&a.dataset.chapter!==e.target.value)</script></html>"""
    )
    (folder / "index.html").write_text(page)
    return {"frames": 80, "layout_findings": len(findings), "sheets": [str(x.relative_to(OUTPUT)) for x in sheets]}


def pcm(path, start=None, duration=None):
    command = ["ffmpeg", "-v", "error", "-i", str(path)]
    if start is not None:
        command += ["-ss", str(start)]
    if duration is not None:
        command += ["-t", str(duration)]
    result = subprocess.run(command + ["-f", "f32le", "-ac", "1", "-ar", "8000", "-"], capture_output=True, check=True)
    return np.frombuffer(result.stdout, dtype="<f4").astype(float)


@lru_cache(maxsize=1)
def reference_audio():
    return pcm(ROOT / "audio.mp3")


def alignment(path, start, duration):
    audio = pcm(path)
    reference = reference_audio()
    rate = 8000
    half = 640
    n = round(min(3, duration - 1) * rate)
    checks = []
    for offset in sorted({0.4, max(0.4, (duration - n / rate) / 2), max(0.4, duration - n / rate - 0.4)}):
        target_start = round(offset * rate)
        ref_start = round((start + offset) * rate) - half
        target = audio[target_start : target_start + n]
        ref = reference[ref_start : ref_start + n + 2 * half]
        if len(target) != n or len(ref) != n + 2 * half:
            raise ValueError("Incomplete reference window; audio alignment cannot be certified")
        target = target - target.mean()
        ref = ref - ref.mean()
        size = 1 << (len(ref) + n - 1).bit_length()
        convolution = np.fft.irfft(np.fft.rfft(ref, size) * np.fft.rfft(target[::-1], size), size)
        dots = convolution[n - 1 : len(ref)]
        sums = np.concatenate(([0], np.cumsum(ref * ref)))
        energies = sums[n:] - sums[:-n]
        correlations = dots / np.sqrt(np.maximum(energies * np.sum(target * target), 1e-20))
        peak = int(np.argmax(correlations))
        lag = (peak - half) / rate
        score = float(correlations[peak])
        checks.append(
            {"offset": offset, "lag_seconds": lag, "correlation": score, "passed": abs(lag) <= 0.001 and score > 0.98}
        )
    return {"passed": all(c["passed"] for c in checks), "windows": checks}


def verify_media():
    metadata = OUTPUT / "previews.json"
    previews = json.loads(metadata.read_text()) if metadata.exists() else []
    results = []
    folder = OUTPUT / "encoded-frames"
    folder.mkdir(parents=True, exist_ok=True)
    for item in previews:
        path = OUTPUT / item["file"]
        info = json.loads(
            subprocess.check_output(
                ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)]
            )
        )
        video = next(s for s in info["streams"] if s["codec_type"] == "video")
        audio = next(s for s in info["streams"] if s["codec_type"] == "audio")
        decoded = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"], capture_output=True, check=False
        )
        expected = math.ceil((item["end"] - item["start"]) * item["fps"] - 1e-9)
        media_ok = (
            decoded.returncode == 0
            and int(video["nb_frames"]) == expected
            and video["width"] == item["width"]
            and video["height"] == item["height"]
            and video["avg_frame_rate"] == f"{item['fps']}/1"
            and abs(float(audio["duration"]) - expected / item["fps"]) <= 0.05
        )
        sync = alignment(path, item["start"], expected / item["fps"])
        samples = []
        for k, at in enumerate(
            (min(1.0, float(video["duration"]) / 4), float(video["duration"]) / 2, float(video["duration"]) - 0.5)
        ):
            sample = folder / f"chapter-{item['chapter']:02d}-{k}.png"
            subprocess.run(
                ["ffmpeg", "-v", "error", "-y", "-i", str(path), "-ss", str(at), "-frames:v", "1", str(sample)],
                check=True,
            )
            samples.append(str(sample.relative_to(OUTPUT)))
        result = {
            **item,
            "complete_decode_passed": decoded.returncode == 0,
            "expected_frames": expected,
            "encoded_frames": int(video["nb_frames"]),
            "encoded_frame_rate": video["avg_frame_rate"],
            "audio_codec": audio["codec_name"],
            "audio_alignment": sync,
            "passed": media_ok and sync["passed"],
            "inspection_frames": samples,
        }
        results.append(result)
        print(f"Verified chapter {item['chapter']:02d}: decode={media_ok}, alignment={sync['passed']}", flush=True)
    data = {
        "full_export_verified": False,
        "preview_count": len(results),
        "previews_passed": {r["chapter"] for r in results} == set(range(1, 11)) and all(r["passed"] for r in results),
        "encoded_visual_inspection_passed": False,
        "previews": results,
    }
    write_json(OUTPUT / "verification.json", data)
    cards = []
    for item in results:
        chapter = item["chapter"]
        cards.append(
            f"<article><h2>{chapter:02d} / {html.escape(TITLES[chapter - 1])}</h2>"
            f'<video controls preload="none" poster="encoded-frames/chapter-{chapter:02d}-1.png" '
            f'src="{html.escape(item["file"])}"></video>'
            f"<p>Source clock {item['start']:.3f}–{item['end']:.3f} s · "
            f"{item['width']}×{item['height']} / {item['fps']} fps</p></article>"
        )
    (OUTPUT / "index.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Roadster / narrated engineering previews</title><style>"
        "body{background:#000;color:#eefaff;font:16px system-ui;margin:36px;max-width:1800px}"
        "h1,a{color:#57edff}h2{font-size:19px;font-weight:500}p{color:#96b1c4}"
        "main{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:32px}video{width:100%;background:#050c12}"
        "article{border-bottom:1px solid #214357;padding-bottom:14px}@media(max-width:850px){main{grid-template-columns:1fr}}"
        "</style><h1>Roadster / the mathematics behind the maneuver</h1>"
        "<p>Ten narrated excerpts from the 40-shot film. Full 4K export remains unrendered.</p>"
        '<p><a href="storyboard/index.html">80-frame storyboard</a> · <a href="verification.json">Media checks</a> · '
        '<a href="../README.md">Renderer and assumptions</a></p><main>' + "".join(cards) + "</main></html>"
    )
    return data
