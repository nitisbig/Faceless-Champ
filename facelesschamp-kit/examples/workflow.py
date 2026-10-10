"""Save as videos/main.py in a kit project; supports either canvas format."""

from faceless_champ import Draw

from facelesschamp_kit import Video
from facelesschamp_kit.blocks import FlowDiagram


def build(ctx):
    video = Video(ctx)
    segment = video.segment("workflow", duration=5)
    direction = "horizontal" if ctx.canvas.width > ctx.canvas.height else "vertical"
    flow = segment.add(
        FlowDiagram(("Input", "Transform", "Useful output"), direction),
        at=0.5,
        duration=4,
        enter="fade",
        enter_duration=0.4,
    )
    segment.play(flow["edge-0"], Draw, at=1, duration=0.6)
    segment.play(flow["node-1"], lambda c: c.animate.scale_to(0.94), at=2, duration=0.5)
    segment.play(flow["label-2"], lambda c: c.animate.color_to(ctx.theme.accent), at=3, duration=0.5)
    segment.play(flow, lambda c: c.animate.opacity_to(0), at=4, duration=0.5)
    return video
