"""Continuous source narration above a cut-only sequence of cue-based scenes."""

from copy import deepcopy

from faceless_champ import Canvas, CueScene, Layer, Scene, Sequence, SubtitleTrack

from .chapters import AUTHORS
from .design import CANVAS, CONFIG, PROJECT

CHAPTERS = [(c["id"], c["title"], c["cue"]) for c in CONFIG["chapters"]]


def stock_analysis_video(image_mode="auto"):
    track = SubtitleTrack.from_srt(PROJECT / "cue-per-word.srt")
    narration = Scene(Canvas(CANVAS.width, CANVAS.height, "#00000000"))
    narration.add_audio(PROJECT / "audio.mp3", start=0)
    total = max(track.duration, narration.duration)
    chapters = CHAPTERS
    starts = [0.0] + [track.cue(cue).start for _, _, cue in chapters[1:]]
    ends = starts[1:] + [total]
    boards, plan = [], []
    for (identifier, title, cue), start, end, author in zip(chapters, starts, ends, AUTHORS, strict=True):
        board = CueScene(track, CANVAS, start_time=start, end_time=end)
        author(board, image_mode)
        board.finish()
        boards.append(board)
        events = [
            {
                "source_time": round(start + entry.start, 6),
                "component": type(entry.component).__name__,
                "label": getattr(entry.component, "text", ""),
                "tracks": [
                    {"property": t.property, "source_time": round(start + t.start, 6), "duration": t.duration}
                    for t in entry.tracks
                ],
            }
            for entry in board.entries
        ]
        plan.append({"id": identifier, "title": title, "cue": cue, "start": start, "end": end, "events": events})
    video = Layer(Sequence(*boards, canvas=CANVAS), narration, canvas=CANVAS)
    video.story_plan = {
        "duration": video.duration,
        "canvas": [CANVAS.width, CANVAS.height],
        "chapters": plan,
        "word_cues": len(track.cues),
        "image_mode": image_mode,
        "subtitle_end": track.duration,
        "audio_duration": narration.duration,
        "visual_thesis": CONFIG["visual_thesis"],
        "palette": CONFIG["palette"],
        "source_notes": CONFIG["source_notes"],
        "revenue": CONFIG["revenue"],
        "storyboard_times": CONFIG["storyboard_times"],
    }
    return video


def timeline(video):
    return deepcopy(video.story_plan)
