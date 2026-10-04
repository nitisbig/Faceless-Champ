import pytest

from faceless_champ import Canvas, Captions, PillowRenderer, Scene, Sequence, SubtitleCue, SubtitleTrack

SRT = "1\n00:00:00,070 --> 00:00:00,330\nThere\n\n2\n00:00:00,330 --> 00:00:00,570\nwas\n\n"


def test_srt_exact_boundaries_bom_crlf_and_gaps(tmp_path):
    path = tmp_path / "words.srt"
    path.write_bytes(
        ("\ufeff" + SRT + "\n3\n00:00:00,700 --> 00:00:01,040\na student.\n").replace("\n", "\r\n").encode()
    )
    track = SubtitleTrack.from_srt(path)
    assert track.duration == 1.04
    assert track.cue(1).start == 0.07
    assert track.cue(3).text == "a student."
    assert track.active_at(0.069) is None
    assert track.active_at(0.07) == track.cue(1)
    assert track.active_at(0.33) == track.cue(2)
    assert track.active_at(0.57) is None
    assert track.active_at(0.69) is None
    assert track.active_at(1.04) is None


@pytest.mark.parametrize(
    "srt",
    [
        "",
        "bad",
        SRT.replace("00:00:00,330", "00:00:00,000", 1),
        SRT.replace("00:00:00,570", "00:00:60,570"),
        SRT.replace("was", ""),
        SRT.replace("2\n", "1\n"),
        SRT.replace("00:00:00,330 -->", "00:00:00,200 -->"),
    ],
)
def test_invalid_srt_rejected(srt):
    with pytest.raises(ValueError):
        SubtitleTrack.parse_srt(srt)


def test_multiline_sentence_cues_and_phrase_limits():
    track = SubtitleTrack.parse_srt(
        "1\n00:00:01.000-->00:00:02.000\nHello\nworld!\n\n\n"
        "2\n00:00:02,000 --> 00:00:03,000\nThink\n\n"
        "3\n00:00:03,000 --> 00:00:04,000\nfirst.\n"
    )
    assert track.cue(1).text == "Hello\nworld!"
    assert [[cue.index for cue in p] for p in track.phrases(max_words=2)] == [[1], [2, 3]]
    assert [[cue.index for cue in p] for p in track.phrases(max_duration=1)] == [[1], [2], [3]]
    for kwargs in ({"max_words": 0}, {"max_words": True}, {"max_duration": 0}, {"max_duration": float("nan")}):
        with pytest.raises(ValueError):
            track.phrases(**kwargs)


def test_caption_highlight_and_lifetime_are_deterministic():
    track = SubtitleTrack.parse_srt(SRT)
    scene = Scene(Canvas(320, 180))
    with scene.at(0.5):
        scene.add(
            Captions(
                track,
                position=(160, 90),
                width=280,
                font_size=26,
                color="white",
                highlight_color="red",
                future_color="gray",
            )
        )
    assert scene.duration == pytest.approx(1.07)
    renderer = PillowRenderer(1)
    renderer.validate(scene)
    early = renderer.frame(scene, 0.6, (320, 180)).convert("RGB")
    later = renderer.frame(scene, 0.9, (320, 180)).convert("RGB")
    raw = early.tobytes()
    assert any(r > 100 and g < 20 and b < 20 for r, g, b in zip(raw[::3], raw[1::3], raw[2::3]))
    assert early.tobytes() != later.tobytes()
    assert renderer.frame(scene, 0.6, (320, 180)).convert("RGB").tobytes() == early.tobytes()
    assert renderer.frame(scene, 0.55, (320, 180)).convert("RGB").getbbox() is None
    assert renderer.frame(scene, 1.07, (320, 180)).convert("RGB").getbbox() is None
    sequence = Sequence(Scene(Canvas(320, 180)).wait(1), scene)
    assert renderer.frame(sequence, 1.6, (320, 180)).convert("RGB").tobytes() == early.tobytes()


def test_caption_wrap_and_width_validation():
    track = SubtitleTrack([SubtitleCue(1, 0, 1, "one two three four")])
    scene = Scene(Canvas(160, 120))
    caption = Captions(track, width=90, font_size=20, position=(80, 60))
    scene.add(caption)
    renderer = PillowRenderer(1)
    renderer.validate(scene)
    box = renderer.frame(scene, 0.5, (160, 120)).convert("RGB").getbbox()
    assert box[2] - box[0] <= 90
    assert box[3] - box[1] > 20
    narrow = Scene().add(Captions(track, width=5))
    with pytest.raises(ValueError, match="exceeds width"):
        renderer.validate(narrow)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"index": 0},
        {"index": True},
        {"start": -1},
        {"end": float("nan")},
        {"end": 0},
        {"text": ""},
    ],
)
def test_cue_validation(kwargs):
    values = {"index": 1, "start": 0, "end": 1, "text": "hello"} | kwargs
    with pytest.raises(ValueError):
        SubtitleCue(**values)


def test_small_overlaps_opt_in_preserve_source_and_latest_cue(tmp_path):
    srt = SRT.replace("00:00:00,330 -->", "00:00:00,329 -->")
    with pytest.raises(ValueError, match="overlap"):
        SubtitleTrack.parse_srt(srt)
    path = tmp_path / "overlap.srt"
    path.write_text(srt)
    track = SubtitleTrack.from_srt(path, overlap_tolerance=0.001)
    assert track.cue(1).end == 0.33
    assert track.cue(2).start == 0.329
    assert track.active_at(0.3289) == track.cue(1)
    assert track.active_at(0.329) == track.cue(2)
    assert track.duration == 0.57
    with pytest.raises(ValueError):
        SubtitleTrack.parse_srt(srt, overlap_tolerance=0.0005)
    with pytest.raises(ValueError):
        SubtitleTrack([SubtitleCue(1, 1, 2, "a"), SubtitleCue(2, 0.5, 3, "b")], overlap_tolerance=10)
    for invalid in (-1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            SubtitleTrack.parse_srt(srt, overlap_tolerance=invalid)


def test_caption_cache_bounded_equivalent_and_reuses_held_frames():
    track = SubtitleTrack([SubtitleCue(i + 1, i / 2, (i + 1) / 2, f"word{i}.") for i in range(80)])
    scene = Scene(Canvas(320, 180, "white")).add(Captions(track, font_size=22, width=280, position=(160, 90)))
    cached = PillowRenderer(1, caption_cache_mb=0.05)
    uncached = PillowRenderer(1, frame_cache_mb=0, caption_cache_mb=0)
    for i in range(80):
        time = i / 2 + 0.1
        assert cached.frame(scene, time, (320, 180)).tobytes() == uncached.frame(scene, time, (320, 180)).tobytes()
        assert cached._caption_cache_bytes <= cached._caption_cache_limit
    assert len(cached._caption_sprites) < 80
    assert not uncached._caption_sprites and not uncached._caption_layouts
    cached.frame(scene, 0.1, (320, 180))
    held = cached._scene_frames[scene][1]
    cached.frame(scene, 0.2, (320, 180))
    assert cached._scene_frames[scene][1] is held
