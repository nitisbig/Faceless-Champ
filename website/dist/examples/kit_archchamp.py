from dataclasses import replace
from faceless_champ import Canvas
from facelesschamp_kit import Video
from facelesschamp_kit.recipes import apply_recipe


def build(ctx):
    ctx.theme = replace(ctx.theme, background="#000000", foreground="#F3F6FF")
    ctx.canvas = Canvas(ctx.canvas.width, ctx.canvas.height, "#000000")
    video = Video(ctx)
    with video.segment("assembly", duration=6) as segment:
        apply_recipe(segment, "arch-design", {"design": {
            "units": "m",
            "parts": [
                {"id": "base", "mesh": {"primitive": "cube", "params": {"x_length": 2, "y_length": 1, "z_length": .4}}},
                {"id": "roof", "mesh": {"primitive": "cube", "params": {"x_length": 2, "y_length": 1, "z_length": .15}},
                 "position": [0, 0, .6], "explode_vector": [0, 0, .8]},
            ],
            "script": {"actions": [
                {"kind": "explode", "targets": ["roof"], "factor": 1, "at": 1, "duration": 2},
                {"kind": "orbit", "degrees": 45, "at": 3, "duration": 2}], "duration": 6},
            "dimensions": [{"start": [-1, -.5, -.2], "end": [1, -.5, -.2], "part": "base"}],
        }})
    return video
