"""Six-second POC. Run fc-kit prepare explicitly before frame/preview/render."""

import os

from facelesschamp_kit import EquationTransform, Video
from facelesschamp_kit.blocks import ManimCanvas

from faceless_champ import Rectangle
from faceless_champ.integrations.manim import ManimRenderOptions


def build(ctx):
    preset = EquationTransform((r"{{x}}^2+2{{x}}+1", r"({{x}}+1)^2"), transform_time=2, hold_time=1.5)
    source = ctx.manim(
        preset.scene_spec(),
        python=os.environ.get("FC_MANIM_PYTHON"),
        options=ManimRenderOptions(width=640, height=360, fps=15),
    )
    video = Video(ctx)
    segment = video.segment("algebra", duration=source.duration)
    segment.add_core(
        lambda context, bounds: Rectangle(
            width=bounds.width - 16, height=bounds.height - 16, position=bounds.center, fill="#172235", stroke=None
        ),
        id="panel",
        enter=None,
        exit=None,
    )
    segment.add(ManimCanvas(source), id="equation", enter=None, exit=None)
    return video
