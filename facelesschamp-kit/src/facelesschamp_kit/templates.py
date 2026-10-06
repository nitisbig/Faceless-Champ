"""Callable templates; scaffolds remain editable copies owned by the user."""

from .blocks import Comparison, Heading, MetricCard, StepList
from .video import Video


def silent(ctx, *, value=42, label="Reusable components"):
    video = Video(ctx)
    with video.segment("hook", duration=3) as segment:
        segment.add(MetricCard(value, label), enter="pop")
    with video.segment("comparison", duration=4) as segment:
        segment.add(Comparison("Repeated setup", "Shared building blocks"), enter="fade")
    with video.segment("finish", duration=3) as segment:
        segment.add(StepList(("Compose", "Preview", "Export")), enter="stagger")
    return video


def narrated(ctx, *, audio="voiceover", subtitles="word_cues", markers=None):
    video = Video(ctx)
    if ctx.assets.entries.get(audio, {}).get("source") == "Synthetic demonstration speech":
        from faceless_champ import Bounds

        video.segment("sample-label", start=0, duration=30).add(
            Heading("SYNTHETIC DEMO AUDIO", variant="muted"),
            bounds=Bounds(64, 8, ctx.canvas.width - 64, 58),
            z_index=10001,
        )
    voice = video.narration(
        audio=ctx.assets.audio(audio),
        subtitles=ctx.assets.subtitle(subtitles),
        markers=markers or {"hook": 1, "comparison": 2, "finish": 3},
    )
    with video.segment("hook", window=voice.between("hook", "comparison")) as segment:
        segment.add(Heading("Build once. Reuse everywhere.", variant="accent"), enter="fade")
    with video.segment("comparison", window=voice.between("comparison", "finish")) as segment:
        segment.add(Comparison("Repeated setup", "Shared building blocks"), enter="fade")
    with video.segment("finish", window=voice.between("finish")) as segment:
        segment.add(StepList(("Compose", "Preview", "Export")), enter="stagger")
    return video
