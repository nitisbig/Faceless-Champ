from dataclasses import replace
from faceless_champ import Canvas
from facelesschamp_kit.templates import narrated


def build(ctx):
    ctx.theme = replace(ctx.theme, background="#000000", foreground="#F3F6FF")
    ctx.canvas = Canvas(ctx.canvas.width, ctx.canvas.height, "#000000")
    return narrated(
        ctx,
        audio="voiceover",
        subtitles="word_cues",
        markers={"hook": 1, "comparison": 2, "finish": 3},
    )
