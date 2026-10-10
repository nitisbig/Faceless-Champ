import wave

import pytest
from faceless_champ import Bounds, Canvas, ImageSlot, PillowRenderer, SubtitleTrack
from PIL import Image as PILImage

from facelesschamp_kit import BuildContext, KitError, Video
from facelesschamp_kit.assets import AssetRegistry
from facelesschamp_kit.blocks import FlowDiagram, Heading, ImageCard, TextPanel
from facelesschamp_kit.themes import LIGHT


def context(tmp_path):
    return BuildContext(tmp_path, Canvas(1920, 1080, "white"), LIGHT)


def test_delayed_lifetime_and_motion(tmp_path):
    v = Video(context(tmp_path))
    s = v.segment("one", start=5, duration=5)
    h = s.add(Heading("Delayed"), at=2, duration=2, enter="fade", enter_duration=0.5)
    s.play(h, lambda c: c.animate.opacity_to(0), at=3, duration=1)
    compiled = v.compile()
    assert [(e.start, e.end) for e in compiled.composition.entries] == [(7, 9)]
    assert compiled.report["segments"][0]["placements"][0]["start"] == 7
    with pytest.raises(KitError, match="MOTION_WINDOW"):
        s.play(h, lambda c: c.animate.scale_to(1.1), at=1, duration=1)
    with pytest.raises(KitError, match="PLACEMENT_WINDOW"):
        s.add(Heading("Overflow"), at=4, duration=2)


def test_cue_edges_original_indices_and_overlap(tmp_path):
    v = Video(context(tmp_path))
    s = v.segment("one", start=10, duration=3)
    s._track = SubtitleTrack.parse_srt(
        "7\n00:00:10,000 --> 00:00:11,001\nHello\n\n19\n00:00:11,000 --> 00:00:12,000\nWorld\n",
        overlap_tolerance=0.001,
    )
    assert s.cue_time(7) == 0
    assert s.cue_time(19, edge="end", offset=0.5) == 2.5
    with pytest.raises(KitError, match="CUE_INDEX"):
        s.cue_time(8)
    with pytest.raises(KitError, match="CUE_WINDOW"):
        s.cue_time(7, offset=-1)


@pytest.mark.parametrize("direction", ["horizontal", "vertical"])
def test_flow_children_and_independent_compilations(tmp_path, direction):
    v = Video(context(tmp_path))
    s = v.segment("flow", duration=3)
    h = s.add(FlowDiagram(("Input", "Transform", "Output"), direction), enter="fade")
    s.play(h["node-1"], lambda c: c.animate.scale_to(0.9), at=1, duration=0.5)
    a, b = v.compile(), v.compile()
    assert a.composition.entries[0].component is not b.composition.entries[0].component
    assert "edge-0" in a.report["segments"][0]["placements"][0]["children"]
    PillowRenderer(1).validate(a.composition)


def test_image_card_uses_named_box_then_actual_image(tmp_path):
    asset = tmp_path / "images/1.png"
    ctx = context(tmp_path)
    ctx.assets = AssetRegistry(tmp_path, {"art": {"type": "image", "path": "images/1.png"}})
    block = ImageCard("art", mode="auto")
    first = block.compose(ctx, Bounds(100, 100, 1000, 900))
    assert isinstance(first.children["image"], ImageSlot)
    assert first.children["image"].label == "1.png"
    box = first.children["image"].bounds
    asset.parent.mkdir()
    PILImage.new("RGB", (100, 100), "red").save(asset)
    second = block.compose(ctx, Bounds(100, 100, 1000, 900))
    assert second.children["image"].bounds == box
    assert not ctx.assets.resolved["art:auto"]["placeholder"]


def test_attach_narration_after_segment_and_hold_audio_tail(tmp_path):
    audio = tmp_path / "voice.wav"
    with wave.open(str(audio), "wb") as output:
        output.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
        output.writeframes(b"\0\0" * 24000)
    (tmp_path / "cues.srt").write_text("7\n00:00:00,500 --> 00:00:01,000\nHello\n")
    v = Video(context(tmp_path))
    s = v.segment("one", duration=2)
    with pytest.raises(KitError, match="NARRATION"):
        s.cue_time(7)
    v.narration(audio="voice.wav", subtitles="cues.srt", markers={"one": 7})
    assert s.cue_time(7) == 0.5
    s.add(Heading("Hold"), at=s.cue_time(7))
    s.add(Heading("Finite"), at=1, duration=0.5)
    compiled = v.compile()
    assert compiled.duration == 3
    assert [(e.start, e.end) for e in compiled.composition.entries] == [(0.5, 3), (1, 1.5)]
    assert len(compiled.composition.audio) == 1
    assert compiled.composition.audio[0].start == 0
    # The audio tail extends a hold, not the authored entrance/motion window.
    too_short = Video(context(tmp_path))
    too_short.narration(audio="voice.wav", subtitles="cues.srt", markers={"one": 7})
    too_short.segment("one", duration=1).add(Heading("Late"), at=0.8, enter="fade")
    with pytest.raises(KitError, match="MOTION_WINDOW"):
        too_short.compile()


def test_short_card_title_does_not_consume_body_area(tmp_path):
    ctx = context(tmp_path)
    box = Bounds(0, 0, 450, 180)
    built = TextPanel("Customer requests", title="Receive").compose(ctx, box)
    title, text = built.children["title"].bounds, built.children["text"].bounds
    assert title.bottom < text.top
    assert built.root.bounds.bottom <= box.bottom


@pytest.mark.parametrize("at,duration", [(float("nan"), None), (-1, 1), (True, 1), (0, 0), (3, None)])
def test_invalid_placement_windows(tmp_path, at, duration):
    with pytest.raises(KitError):
        Video(context(tmp_path)).segment("one", duration=3).add(Heading("No"), at=at, duration=duration)


def test_default_entry_must_fit_remaining_lifetime(tmp_path):
    v = Video(context(tmp_path))
    v.segment("one", duration=1).add(Heading("No"), at=0.8, enter="fade")
    with pytest.raises(KitError, match="MOTION_WINDOW"):
        v.compile()


def test_corrupt_image_auto_errors_but_forced_placeholder_works(tmp_path):
    (tmp_path / "1.png").write_bytes(b"corrupt")
    ctx = context(tmp_path)
    ctx.assets = AssetRegistry(tmp_path, {"art": {"type": "image", "path": "1.png"}})
    v = Video(ctx)
    v.segment("one", duration=1).add(ImageCard("art", mode="auto"))
    with pytest.raises(ValueError, match="Cannot decode image"):
        PillowRenderer(1).validate(v.compile().composition)
    v = Video(ctx)
    v.segment("one", duration=1).add(ImageCard("art", mode="placeholder"))
    PillowRenderer(1).validate(v.compile().composition)


def test_flow_rejects_invalid_content_or_too_small_allocation(tmp_path):
    with pytest.raises(KitError, match="BLOCK_PROPS"):
        FlowDiagram(())
    with pytest.raises(KitError, match="BLOCK_PROPS"):
        FlowDiagram(("Input",), direction="diagonal")
    with pytest.raises(KitError, match="LAYOUT"):
        FlowDiagram(("Input", "Output")).compose(context(tmp_path), Bounds(0, 0, 100, 100))
