"""Audit preserved inputs, source-time motion, and an optional rendered MP4."""

import argparse
import hashlib
import json
import math
import subprocess
from array import array
from itertools import pairwise
from pathlib import Path

from main import PROJECT, stock_analysis_video, timeline
from scene.design import CONFIG

from faceless_champ import Circle, Polyline, Text


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def audio_alignment(media):
    def waveform(path):
        data = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "8000", "-f", "f32le", "-"],
            check=True,
            capture_output=True,
        ).stdout
        result = array("f")
        result.frombytes(data)
        return result

    source, rendered = waveform(PROJECT / "audio.mp3"), waveform(media)
    # Check beginning, middle and end independently to catch clock drift.
    checks = []
    for seconds in (2, 15, 30, 45, 58):
        indices = range(seconds * 8000, (seconds + 2) * 8000, 8)
        values = [source[i] for i in indices]
        norm = sum(x * x for x in values) ** 0.5

        def score(offset, indices=indices, values=values, norm=norm):
            target = [rendered[i + offset] for i in indices]
            return sum(x * y for x, y in zip(values, target)) / (norm * sum(y * y for y in target) ** 0.5)

        coarse = max(range(-1600, 1601, 20), key=score)
        best = max(range(coarse - 20, coarse + 21), key=score)
        correlation = score(best)
        if abs(best) > 32 or correlation < 0.97:
            raise ValueError(f"Narration alignment failed at {seconds}s: lag {best / 8000:g}s")
        checks.append(
            {"source_seconds": seconds, "offset_seconds": best / 8000, "waveform_correlation": round(correlation, 6)}
        )
    return checks


def graph_alignment(video):
    errors = []
    for index, width, radius, times in ((0, 8, 10, (1.75, 2.59, 3.90)), (4, 7, 8, (55.7, 56.5, 57.1))):
        scene = video.children[0].children[index]
        curve = next(
            e for e in scene.entries if isinstance(e.component, Polyline) and e.component.stroke_width == width
        )
        dot = next(e for e in scene.entries if isinstance(e.component, Circle) and e.component.width == radius * 2)
        shape = curve.component
        left, top = shape.position[0] - shape.width / 2, shape.position[1] - shape.height / 2
        points = [(left + x, top + y) for x, y in shape.points]
        distances = [math.dist(a, z) for a, z in pairwise(points)]
        for source_time in times:
            local = source_time - scene.start_time
            progress = curve.state_at(local)["draw"]
            remaining = ((points[-1][0] - points[0][0]) if shape.draw_by == "x" else sum(distances)) * progress
            expected = points[-1]
            for (a, z), length in zip(pairwise(points), distances):
                span = z[0] - a[0] if shape.draw_by == "x" else length
                if remaining <= span:
                    expected = tuple(x + (y - x) * remaining / span for x, y in zip(a, z))
                    break
                remaining -= span
            error = math.dist(expected, dot.state_at(local)["position"])
            if error > 0.01:
                raise ValueError(f"Graph marker detached at {source_time}s")
            errors.append(error)
    return {"sample_count": len(errors), "max_error_design_pixels": round(max(errors), 6)}


def audit(media=None):
    video = stock_analysis_video("required")
    plan = timeline(video)
    hashes = {
        name: hashlib.sha256((PROJECT / name).read_bytes()).hexdigest() for name in CONFIG["preserved_asset_sha256"]
    }
    if hashes != CONFIG["preserved_asset_sha256"]:
        raise ValueError("An original image, narration, or subtitle has changed")
    expected_starts = [0, 7.28, 24.43, 38.54, 47.28, 59.15]
    if any(abs(c["start"] - start) > 1e-6 for c, start in zip(plan["chapters"], expected_starts, strict=True)):
        raise ValueError("A source cue boundary changed")
    if abs(plan["duration"] - 62.088) > 1e-6 or plan["word_cues"] != 160:
        raise ValueError("Source duration or cue count changed")
    chapters = []
    for c in plan["chapters"]:
        intervals = sorted((b["source_time"], b["source_time"] + b["duration"]) for b in c["visual_beats"])
        latest = c["start"]
        gap = 0
        for start, end in intervals:
            if start < c["start"] - 1e-6 or end > c["end"] + 1e-6:
                raise ValueError(f"Visual beat outside {c['id']}")
            gap = max(gap, start - latest)
            latest = max(latest, end)
        gap = max(gap, c["end"] - latest)
        limit = 1.3 if c["id"] == "closing" else 1.0
        if gap > limit:
            raise ValueError(f"Static hold too long in {c['id']}: {gap:.3f}s")
        chapters.append(
            {
                "id": c["id"],
                "meaningful_beats": len(intervals),
                "max_hold_without_meaningful_animation_seconds": round(gap, 3),
            }
        )
    # Scene snapshots are inspectable; assert that the revenue evidence's lifetime
    # ends before the infrastructure image enters. This catches ghost-layer regressions.
    board = video.children[0].children[1]
    ghost_numbers = [
        e
        for e in board.entries
        if hasattr(e.component, "value")
        and e.start + board.start_time < 17.9
        and (e.end is None or e.end + board.start_time > 18.15)
    ]
    if ghost_numbers:
        raise ValueError("Revenue-stage numbers survived the infrastructure transition")
    for chapter in video.children[0].children:
        for entry in chapter.entries:
            if isinstance(entry.component, Text):
                box = entry.component.bounds
                if box.left < 48 or box.right > 1032 or box.top < 40 or box.bottom > 1580:
                    raise ValueError(f"Text outside safe margins: {entry.component.text}")
    report = {
        "status": "passed",
        "design_version": CONFIG["visual_design"]["version"],
        "source_duration_seconds": plan["duration"],
        "word_cues": plan["word_cues"],
        "preserved_inputs_sha256": hashes,
        "asset_preservation": "passed",
        "source_clock": "passed",
        "pacing_excludes_progress_rail": True,
        "chapters": chapters,
        "revenue_to_infrastructure_lifetimes": "passed",
        "graph_markers": graph_alignment(video),
        "text_safe_margins": "passed at initial design layout",
        "earnings_source": CONFIG["revenue"]["source"],
        "visual_inspection": {
            "storyboard": "output/redesign-storyboard/storyboard.png",
            "design_size_frames": [6.7, 17.4, 23.7, 28.9, 37.8, 46.8, 58.6],
        },
        "full_export": "not checked",
    }
    if media is not None:
        media = Path(media).resolve()
        info = json.loads(run("ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(media)))
        streams = info["streams"]
        visual = next(s for s in streams if s["codec_type"] == "video")
        sound = next(s for s in streams if s["codec_type"] == "audio")
        numerator, denominator = map(int, visual["r_frame_rate"].split("/"))
        fps = numerator / denominator
        if (visual["width"], visual["height"]) != (1080, 1620) or fps != 30:
            raise ValueError("Expected a design-resolution 30 fps export")
        frames = math.ceil(plan["duration"] * fps)
        if int(visual["nb_frames"]) != frames:
            raise ValueError("Missing or excess video frames")
        if abs(float(visual["duration"]) - frames / fps) > 1e-5:
            raise ValueError("Unexpected video duration")
        if abs(float(sound["duration"]) - plan["duration"]) > 1 / fps:
            raise ValueError("Audio duration differs from source narration")
        run("ffmpeg", "-v", "error", "-i", str(media), "-f", "null", "-")
        report["narration_alignment"] = audio_alignment(media)
        report["full_export"] = {
            "path": str(media),
            "width": visual["width"],
            "height": visual["height"],
            "fps": fps,
            "frames": frames,
            "video_codec": visual["codec_name"],
            "audio_codec": sound["codec_name"],
            "duration_seconds": float(info["format"]["duration"]),
            "full_video_and_audio_decode": "passed",
        }
        saved_plan = json.loads((PROJECT / "output/timeline.json").read_text())
        report["full_export_settings"] = saved_plan["last_export_settings"]
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--media", type=Path)
    args = parser.parse_args()
    result = audit(args.media)
    destination = PROJECT / "output/redesign-verification.json"
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
