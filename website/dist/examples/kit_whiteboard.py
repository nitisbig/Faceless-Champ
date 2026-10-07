from facelesschamp_kit.blocks import (
    WhiteboardArrow, WhiteboardCircle, WhiteboardDrawing,
    WhiteboardLine, WhiteboardPath, WhiteboardRectangle,
)
from facelesschamp_kit.templates import WhiteboardScene, whiteboard_basic


def build(ctx):
    return whiteboard_basic(
        ctx,
        theme=ctx.theme,
        draw_fraction=0.7,
        scenes=[
            WhiteboardScene(
                name="connect",
                duration=5,
                drawing=WhiteboardDrawing(
                    viewbox=(1400, 700),
                    drawings=(
                        WhiteboardCircle(center=(350, 350), radius=140, stroke_width=8),
                        WhiteboardArrow(start=(540, 350), end=(860, 350),
                                        color="#2563EB", stroke_width=8),
                        WhiteboardCircle(center=(1050, 350), radius=140, stroke_width=8),
                    ),
                ),
            ),
            WhiteboardScene(
                name="progress",
                duration=5,
                drawing=WhiteboardDrawing(
                    viewbox=(1400, 700),
                    drawings=(
                        WhiteboardRectangle(x=200, y=120, width=1000, height=460,
                                            stroke_width=8),
                        WhiteboardLine(start=(300, 480), end=(1100, 480),
                                       color="#64748B", stroke_width=6),
                        WhiteboardPath(points=((300, 440), (500, 400), (700, 320),
                                               (900, 300), (1100, 200)),
                                       color="#2563EB", stroke_width=10),
                    ),
                ),
            ),
        ],
    )
