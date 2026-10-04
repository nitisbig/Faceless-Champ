"""Full narration on one source clock, with audio above a scene sequence."""

from copy import deepcopy

from faceless_champ import Canvas, Layer, Scene, Sequence, SubtitleTrack

from .chapters import AUTHORS
from .design import CANVAS, INK, IVORY, PROJECT, RUST, TAUPE, Board

# Each boundary is an original one-based SRT cue. No scene transition retimes audio.
CHAPTERS = [
    ("opening", "Can a country run out of money?", 1),
    ("household", "A country is not a household", 54),
    ("budget", "Where government money goes", 129),
    ("deficit", "The $10 billion gap", 168),
    ("bonds", "A bond is a promise", 189),
    ("debt", "Debt grows. Can payments keep up?", 237),
    ("shocks", "When confidence starts to break", 292),
    ("interest-loop", "The debt feedback loop", 351),
    ("currency", "Whose currency is the debt in?", 415),
    ("reserves", "Foreign currency has to come from somewhere", 519),
    ("conversion", "Same debt. Twice the local cost.", 610),
    ("policies", "Four difficult choices", 664),
    ("aftermath", "Default changes trust", 809),
    ("recap", "What really runs out?", 892),
]


def country_economy_video(image_mode="auto"):
    track = SubtitleTrack.from_srt(PROJECT / "cue-per-word.srt", overlap_tolerance=0.001)
    starts = [0.0] + [track.cue(cue).start for _, _, cue in CHAPTERS[1:]]
    ends = starts[1:] + [track.duration]
    chapters, boards = [], []
    for (identifier, title, cue), start, end, author in zip(CHAPTERS, starts, ends, AUTHORS):
        chapter = {"id": identifier, "title": title, "cue": cue, "start": start, "end": end}
        board = Board(track, chapter, image_mode)
        author(board)
        board.finish()
        chapter["events"] = board.events
        chapter["preview"] = min(end - 0.1, start + (end - start) * 0.7)
        chapters.append(chapter)
        boards.append(board)
    overlay = Scene(Canvas(1920, 1080, "#00000000"))
    overlay.add_audio(PROJECT / "audio.mp3", start=0)
    overlay.wait_until(track.duration)
    video = Layer(Sequence(*boards, canvas=CANVAS), overlay, canvas=CANVAS)
    video.story_plan = {
        "duration": video.duration,
        "canvas": [1920, 1080],
        "image_mode": image_mode,
        "chapters": chapters,
        "word_cues": len(track.cues),
        "subtitle_overlap_tolerance": 0.001,
        "palette": {"background": CANVAS.bg, "accent": RUST, "muted": TAUPE, "surface": IVORY, "ink": INK},
        "storyboard_times": sorted(
            {round(chapter["preview"], 4) for chapter in chapters}
            | {
                8.2,
                24.8,
                53.8,
                62.9,
                76.8,
                94.8,
                123.5,
                126.8,
                139.9,
                168.6,
                182.8,
                195.5,
                206.9,
                218.5,
                232.8,
                250.9,
                266.0,
                287.7,
                314.4,
                325.9,
                337.4,
                350.4,
                359.95,
            }
        ),
    }
    return video


def timeline(video):
    return deepcopy(video.story_plan)
