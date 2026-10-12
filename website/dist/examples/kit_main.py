from dataclasses import replace
from faceless_champ import Canvas
from facelesschamp_kit import Video
from facelesschamp_kit.blocks import MetricCard, Comparison, StepList

def build(ctx):
    ctx.theme = replace(ctx.theme, background="#000000", foreground="#F3F6FF")
    ctx.canvas = Canvas(ctx.canvas.width, ctx.canvas.height, "#000000")
    video = Video(ctx)
    with video.segment("hook", duration=3) as segment:
        card = segment.add(MetricCard(42, "Reusable components"), enter="pop")
        segment.play(card["value"], lambda number: number.animate.value_to(100),
                     at=1, duration=1)
    with video.segment("comparison", duration=4) as segment:
        segment.add(Comparison("Repeated setup", "Shared building blocks"),
                    enter="fade")
    with video.segment("finish", duration=3) as segment:
        segment.add(StepList(("Compose", "Preview", "Export")), enter="stagger")
    return video
