from facelesschamp_kit import Video
from facelesschamp_kit.blocks import Heading, MetricCard
from facelesschamp_kit.layouts import Stack

def build(ctx):
    video = Video(ctx)
    with video.segment("summary", duration=4) as segment:
        segment.add(Stack(
            Heading("Make the idea visible"),
            MetricCard(3, "Purposeful visual beats"),
            gap=40,
        ), enter="stagger")
    return video
