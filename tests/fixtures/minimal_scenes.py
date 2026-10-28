"""Fixed-stack V1 wheel fixtures shared by source and minimal-wheel checks.

V1 rendered unspecified fonts with DejaVu Sans; V2 defaults to DM Sans, so the
parity scenes name the DejaVu ``fallback`` font explicitly.
"""

from pathlib import Path

from PIL import Image as PILImage

from faceless_champ import (
    Canvas,
    Captions,
    CircleMask,
    Group,
    Image,
    PathData,
    Rectangle,
    Scene,
    SubtitleCue,
    SubtitleTrack,
    Text,
    VectorPath,
    linear,
)


def scenes(directory, *, include_domains=True):
    shape = Rectangle(width=70, height=40, fill="#537ce8", position=(70, 60))
    plain = Scene(Canvas(320, 180, "#101522")).add(shape)
    plain.play(shape.animate.move_to(240, 120), run_time=2, rate_func=linear)
    group = Group(
        Group(Rectangle(width=90, height=60, fill="#db9944", position=(140, 90)), opacity=0.6),
        Text("V1 / AV 012", font="fallback", font_size=20, position=(150, 90)),
        mask=CircleMask(65),
        rotation=12,
        opacity=0.7,
    )
    nested = Scene(Canvas(320, 180, "#00000000")).add(group).wait(2)
    track = SubtitleTrack([SubtitleCue(1, 0.2, 0.9, "Source."), SubtitleCue(2, 1.1, 1.8, "Clock.")])
    captions = (
        Scene(Canvas(320, 180))
        .add(Captions(track, font="fallback", width=240, font_size=24, position=(160, 90)))
        .wait(2)
    )
    if include_domains:
        from facelesschamp_kit.charts import BarChart
        from facelesschamp_kit.diagrams import FlowChamp, FlowEdge, FlowGraph, FlowNode

        chart = (
            Scene(Canvas(320, 180, "white"))
            .add(BarChart(["A", "B"], {"s": [2, 4]}, width=300, height=160, position=(160, 90)))
            .wait(2)
        )
        graph = FlowGraph((FlowNode("a", label="Input"), FlowNode("b", label="Output")), (FlowEdge("ab", "a", "b"),))
        flow = Scene(Canvas(320, 180)).add(FlowChamp(graph, width=300, height=160, position=(160, 90))).wait(2)
    path = PathData().move_to(20, 100).cubic_to(90, 10, 210, 170, 300, 80)
    vector = Scene(Canvas(320, 180)).add(VectorPath(path, stroke="#61e2c4", stroke_width=4)).wait(2)
    gif = Path(directory) / "prepared.gif"
    PILImage.new("RGBA", (20, 20), "red").save(
        gif, save_all=True, append_images=[PILImage.new("RGBA", (20, 20), "blue")], duration=[200, 300], loop=0
    )
    prepared = Scene(Canvas(320, 180)).add(Image.from_source(gif, width=80, height=80, position=(160, 90))).wait(2)
    result = {
        "plain": plain,
        "nested": nested,
        "captions": captions,
        "path": vector,
        "prepared": prepared,
    }
    if include_domains:
        result.update(chart=chart, flow=flow)
    return result


def native_scenes():
    """M0 parity samples for optional text/path and scientific field sessions."""
    import numpy as np
    import pyvista as pv
    from facelesschamp_kit.engineering.clip import ArchChamp
    from facelesschamp_kit.engineering.script import ArchScript

    from faceless_champ.integrations.pyvista.model import ArchMesh, ArchPart, ArchStyle

    text = Text("Native AV 012", font="fallback", font_size=30, text_engine="skia", position=(160, 70))
    native = (
        Scene(Canvas(320, 180, "#101522"))
        .add(
            Group(
                text,
                VectorPath(PathData().move_to(25, 130).line_to(290, 130), stroke="cyan", stroke_width=3),
                mask=CircleMask(130),
            )
        )
        .wait(2)
    )
    data = pv.Cube().triangulate()
    data.point_data["temperature"] = np.linspace(0, 1, data.n_points)
    field = ArchChamp(
        [ArchPart("body", ArchMesh.from_data(data))],
        ArchScript().orbit(35, duration=2),
        style=ArchStyle(concept="heatmap", scalars="temperature", clim=(0, 1)),
        width=280,
        height=160,
        position=(160, 90),
    )
    scientific = Scene(Canvas(320, 180, "#101522")).add(field).wait(2)
    return {"native": ("skia", native), "scientific": ("pillow", scientific)}
