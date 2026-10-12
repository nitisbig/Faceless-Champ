from dataclasses import replace
from faceless_champ import Canvas
"""Editable FlowChamp starter: reveal, signals and context highlighting."""

from faceless_champ.flow.examples import recipe

from facelesschamp_kit import Video
from facelesschamp_kit.blocks import FlowCanvas


def build(ctx):
    ctx.theme = replace(ctx.theme, background="#000000", foreground="#F3F6FF")
    ctx.canvas = Canvas(ctx.canvas.width, ctx.canvas.height, "#000000")
    # FlowCanvas uses ctx.theme.muted for structure and accent for packets/highlights.
    video = Video(ctx)
    portrait = ctx.canvas.height > ctx.canvas.width
    viewport = (600, 1000) if portrait else (1200, 675)
    graph, script = recipe("workflow", portrait=portrait)
    video.segment("flowchamp", duration=6).add(FlowCanvas(graph, script, viewport=viewport))
    return video
