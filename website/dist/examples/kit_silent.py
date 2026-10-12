from dataclasses import replace
from faceless_champ import Canvas
from facelesschamp_kit.templates import silent


def build(ctx):
    ctx.theme = replace(ctx.theme, background="#000000", foreground="#F3F6FF")
    ctx.canvas = Canvas(ctx.canvas.width, ctx.canvas.height, "#000000")
    return silent(ctx, value=3, label="Steps from idea to video")
