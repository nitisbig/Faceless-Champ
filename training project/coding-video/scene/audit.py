"""Structural checks across the full composition; no video export."""

import math

from faceless_champ import Captions, Number, SubtitleTrack
from faceless_champ.export import _audio_events

from .story import PROJECT


def check(video, report):
    track = SubtitleTrack.from_srt(PROJECT / "cue-per-word.srt")
    assert len(track.cues) == 447 and math.isclose(track.duration, 151.28)
    assert math.isclose(video.duration, report["duration"])
    audio = _audio_events(video)
    assert len(audio) == 1 and audio[0][1] == 0
    assert audio[0][0].path == PROJECT / "audio.mp3"
    assert math.isclose(audio[0][0].duration, video.duration)
    sequence = video.children[0]
    bounds_checked = 0
    for chapter, scene in zip(report["chapters"], sequence.children):
        assert math.isclose(scene.duration, chapter["end"] - chapter["start"])
        for original, entry in scene._objects.items():
            assert not isinstance(entry.component, Captions)
            end = entry.end if entry.end is not None else scene.duration
            assert 0 <= entry.start < end <= scene.duration + 1e-8
            samples = {entry.start, (entry.start + end) / 2, max(entry.start, end - 1e-6)}
            for motion in entry.tracks:
                assert motion.start >= entry.start
                assert motion.start + motion.duration <= end + 1e-8
                samples.update((motion.start, motion.start + motion.duration / 2, motion.start + motion.duration))
            if entry.parent is None:
                for t in samples:
                    b = scene.bounds_at(original, min(t, end - 1e-6))
                    assert b.left >= 35 and b.right <= 1885 and b.top >= 35 and b.bottom <= 1045, (chapter["id"], b)
                    bounds_checked += 1
    assert all(e["start"] <= e["motion_end"] <= e["end"] for e in report["events"])
    assert all(math.isclose(e["start"], track.cue(e["cue"]).start) or e["start"] == 0 for e in report["events"])
    actions = sequence.children[7]
    numbers = [e for e in actions.entries if isinstance(e.component, Number)]
    assert [e.state_at(actions.duration - 1e-6)["value"] for e in numbers] == [85, 90]
    assert math.isclose(sequence.duration, video.duration)
    return {
        "passed": True,
        "cue_count": len(track.cues),
        "duration": video.duration,
        "chapters": len(sequence.children),
        "visual_events": len(report["events"]),
        "bounds_checked": bounds_checked,
        "audio_tracks": 1,
        "final_health": {"Alex": 85, "Sam": 90},
        "full_export_verified": False,
    }
