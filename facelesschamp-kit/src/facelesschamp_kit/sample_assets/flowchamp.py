"""Editable FlowChamp starter: reveal, signals and context highlighting."""

from facelesschamp_kit import Video
from facelesschamp_kit.blocks import FlowCanvas
from facelesschamp_kit.diagrams.examples import recipe


def build(ctx):
    # FlowCanvas uses ctx.theme.muted for structure and accent for packets/highlights.
    video = Video(ctx)
    portrait = ctx.canvas.height > ctx.canvas.width
    viewport = (600, 1000) if portrait else (1200, 675)
    graph, script = recipe("workflow", portrait=portrait)
    video.segment("flowchamp", duration=6).add(FlowCanvas(graph, script, viewport=viewport))
    return video
