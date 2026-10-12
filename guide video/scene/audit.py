"""Whole-guide structural and sampled geometry checks, without a full export."""

import itertools
import math

from faceless_champ import Captions, CodeEditor

from .design import SAFE
from .playground import ExamplePlayback, replay
from .spec import DURATION, PROJECT, digest, track


def check(video, report):
    cues = track()
    assert len(cues.cues) == 819
    assert math.isclose(cues.duration, 286.08)
    overlaps = [(a.index, b.index) for a, b in zip(cues.cues, cues.cues[1:]) if a.end > b.start]
    assert overlaps == [(12, 13), (309, 310), (359, 360), (452, 453), (721, 722)]
    assert math.isclose(video.duration, DURATION)
    assert len(video.audio) == 1 and video.audio[0].start == 0
    assert video.audio[0].path == PROJECT / ".fc-kit/narration.wav"
    assert not any(isinstance(e.component, Captions) for e in video.entries)
    chapters = report["chapters"]
    assert chapters[0]["start"] == 0 and chapters[-1]["end"] == DURATION
    assert all(math.isclose(a["end"], b["start"]) for a, b in itertools.pairwise(chapters))
    for event in report["events"]:
        assert event["start"] < event["end"] <= DURATION
        if event["cue"] is not None:
            assert math.isclose(event["start"], cues.cue(event["cue"]).start)
    originals = {id(entry): component for component, entry in video._objects.items()}
    samples = {0, DURATION - 1e-6}
    bounds_checked = 0
    static_bounds = {}
    geometry = {"position", "scale", "scale_x", "scale_y", "rotation", "width", "height", "stroke_width"}

    def measured(entry, t):
        def moving(e):
            return any(m.property in geometry for m in e.tracks) or any(moving(c) for c in e.children)

        if moving(entry):
            return video.bounds_at(originals[id(entry)], t)
        if id(entry) not in static_bounds:
            static_bounds[id(entry)] = video.bounds_at(originals[id(entry)], entry.start)
        return static_bounds[id(entry)]

    for entry in video.entries:
        end = entry.end if entry.end is not None else video.duration
        assert 0 <= entry.start < end <= video.duration + 1e-8
        times = {entry.start, min(end - 1e-6, (entry.start + end) / 2), end - 1e-6}
        for motion in entry.tracks:
            assert motion.start >= entry.start - 1e-8
            assert motion.start + motion.duration <= end + 1e-8
            times.update(
                (
                    motion.start,
                    motion.start + motion.duration / 4,
                    motion.start + motion.duration / 2,
                    motion.start + motion.duration * 0.75,
                    min(end - 1e-6, motion.start + motion.duration),
                )
            )
        if entry.parent is None:
            for t in times:
                b = measured(entry, t)
                assert b.left >= SAFE.left - 1 and b.right <= SAFE.right + 1, (entry.component, t, b)
                assert b.top >= SAFE.top - 1 and b.bottom <= SAFE.bottom + 1, (entry.component, t, b)
                bounds_checked += 1
        samples.update(times)
        if isinstance(entry.component, CodeEditor):
            for c in entry.component.timeline.script.checkpoints:
                state = entry.component.timeline.state_at(c.edit_end)
                assert state["source"] == c.files[c.active_file]
    # Detect collisions between unrelated content roots; enclosure is intentional.
    # Text/Circle content inside the prepared output is inspected separately.
    warnings = []
    roots = [e for e in video.entries if e.parent is None]
    for t in sorted(samples):
        visible = [e for e in roots if e.start <= t < (e.end or DURATION) and e.state_at(t)["opacity"] > 0.15]
        evaluated = {id(e): measured(e, t) for e in visible}
        for a, b in itertools.combinations(visible, 2):
            x, y = evaluated[id(a)], evaluated[id(b)]
            # The origin and coordinate axes intentionally touch the output border.
            if 114.62 <= t < 133.36 and (
                isinstance(a.component, ExamplePlayback)
                or isinstance(b.component, ExamplePlayback)
                or type(a.component).__name__ == "Rectangle"
                and x.width > 1400
                or type(b.component).__name__ == "Rectangle"
                and y.width > 1400
            ):
                continue
            if (
                x.left <= y.left + 2
                and x.right >= y.right - 2
                and x.top <= y.top + 2
                and x.bottom >= y.bottom - 2
                or y.left <= x.left + 2
                and y.right >= x.right - 2
                and y.top <= x.top + 2
                and y.bottom >= x.bottom - 2
            ):
                continue
            if 114.62 <= t < 133.36 and {type(a.component).__name__, type(b.component).__name__} <= {"Circle", "Arrow"}:
                continue  # Coordinate arrows meet at the marked origin.
            width = min(x.right, y.right) - max(x.left, y.left)
            height = min(x.bottom, y.bottom) - max(x.top, y.top)
            if width > 8 and height > 8:
                warnings.append(
                    {
                        "time": round(t, 3),
                        "a": type(a.component).__name__,
                        "b": type(b.component).__name__,
                        "a_text": getattr(a.component, "text", None),
                        "b_text": getattr(b.component, "text", None),
                    }
                )
    if warnings:
        unique = {(w["a"], w["b"], w["a_text"], w["b_text"]): w for w in warnings}
        raise AssertionError(list(unique.values()))
    # Prepared output contains actual tracks from the executed example, including both fades.
    playback = next(e.component for e in video.entries if isinstance(e.component, ExamplePlayback))
    original = playback.prepared.results[-1]["values"]["scene"]
    example = replay(original)
    assert math.isclose(example.duration, 5.8)
    assert len(example.entries) == 2
    text, dot = example.entries
    assert text.component.text == "Hello, Faceless Champ"
    assert dot.component.width == 120
    assert dot.state_at(0)["position"] == (400, 700)
    assert dot.state_at(4)["position"] == (1520, 700)
    assert text.state_at(5.3)["opacity"] == dot.state_at(5.3)["opacity"] == 0
    return {
        "passed": True,
        "duration": DURATION,
        "cue_count": 819,
        "chapters": len(chapters),
        "visual_events": len(report["events"]),
        "audio_tracks": 1,
        "known_overlaps": overlaps,
        "bounds_checked": bounds_checked,
        "geometry_sample_times": len(samples),
        "collision_warnings": warnings,
        "prepared_assets": report["prepared_assets"],
        "source_hashes": {name: digest(PROJECT / name) for name in ("audio.mp3", "cue-per-word.srt", "voiceover.md")},
        "full_export_verified": False,
    }
