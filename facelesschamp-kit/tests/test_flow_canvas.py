from types import SimpleNamespace

import pytest
from faceless_champ import Canvas, PillowRenderer
from facelesschamp_kit.diagrams import FlowEdge, FlowGraph, FlowNode, FlowScript, FlowTheme
from facelesschamp_kit.diagrams.examples import recipe

from facelesschamp_kit import Video
from facelesschamp_kit.blocks import FlowCanvas
from facelesschamp_kit.context import BuildContext
from facelesschamp_kit.diagnostics import KitError
from facelesschamp_kit.project import Project
from facelesschamp_kit.scaffold import init_project


@pytest.mark.parametrize("canvas", [Canvas(1920, 1080), Canvas(1080, 1920)])
def test_fresh_placement_theme_and_handle(tmp_path, canvas):
    ctx = BuildContext(tmp_path, canvas=canvas)
    graph, script = recipe()
    block = FlowCanvas(graph, script)
    a, b = block.compose(ctx, ctx.bounds), block.compose(ctx, ctx.bounds)
    assert a.root is not b.root
    assert a.children["diagram"] is a.root
    assert a.root.theme.accent == ctx.theme.accent
    assert a.root.theme.font_size == ctx.theme.body_size
    assert a.root.theme.minimum_font_size == ctx.theme.minimum_font_size
    assert a.root.theme.stroke == ctx.theme.muted
    assert a.bounds.left >= ctx.bounds.left
    assert a.bounds.bottom <= ctx.bounds.bottom
    video = Video(ctx)
    segment = video.segment("flow", duration=6)
    handle = segment.add(block)
    segment.play(handle["diagram"], lambda c: c.animate.opacity_to(0.5), at=5, duration=1)
    compiled = video.compile()
    PillowRenderer(1).frame(compiled.composition, 3, (320, 180))


def test_motion_window_and_tail(tmp_path):
    for voice in (None, SimpleNamespace(duration=8, track=None)):
        v = Video(BuildContext(tmp_path))
        v.voice = voice
        g, s = recipe()
        v.segment("flow", duration=2).add(FlowCanvas(g, s))
        with pytest.raises(KitError, match="MOTION_WINDOW"):
            v.compile()


def test_source_start_and_diagnostics(tmp_path):
    v = Video(BuildContext(tmp_path))
    g = FlowGraph((FlowNode("a", position=(200, 200)), FlowNode("b", position=(200, 200))))
    s = FlowScript().reveal("a", duration=3)
    v.segment("flow", duration=1).add(FlowCanvas(g, s, source_start=2))
    compiled = v.compile()
    assert compiled.duration == 1
    assert "FLOW_OVERLAP" in str(compiled.report)


def test_scaffold_build(tmp_path):
    root = tmp_path / "flow"
    init_project(root, template="flowchamp")
    compiled = Project(root).build("main")
    assert compiled.duration == 6
    assert "FlowCanvas" in (root / "videos/main.py").read_text()


def test_timed_diagnostics_translate_placement_and_source_offset(tmp_path):
    v = Video(BuildContext(tmp_path))
    g = FlowGraph((FlowNode("a", position=(200, 200)), FlowNode("b", position=(550, 200))), layout="manual")
    s = FlowScript().move("b", (200, 200), at=1, duration=2)
    segment = v.segment("diagram", start=10, duration=4)
    segment.add(FlowCanvas(g, s, source_start=1), at=1, duration=2)
    report = v.compile().report
    timed = [d for d in report["diagnostics"] if d["code"] == "FLOW_OVERLAP" and "script_time" in d]
    assert timed
    assert all(d["source_time"] == 11 + d["script_time"] - 1 for d in timed)
    assert all(d["segment"] == "diagram" and d["placement"] == "diagram/block-1" for d in timed)
    assert all(11 <= d["source_time"] <= 13 for d in timed)


def test_explicit_flow_theme_retains_legacy_accent_stroke(tmp_path):
    ctx = BuildContext(tmp_path)
    g = FlowGraph((FlowNode("a"),))
    built = FlowCanvas(g, theme=FlowTheme(accent="#C15F3C")).compose(ctx, ctx.bounds)
    assert built.root.theme.stroke is None


def test_adjusted_edge_labels_keep_compiler_diagnostic_scope(tmp_path):
    graph = FlowGraph(
        (FlowNode("a", position=(150, 150)), FlowNode("b", position=(450, 150))),
        (FlowEdge("read", "a", "b", label="Read", label_position=0.5, label_offset=(150, 0)),),
        layout="manual",
    )
    video = Video(BuildContext(tmp_path))
    video.segment("feed", start=2, duration=3).add(FlowCanvas(graph, viewport=(600, 400)))
    compiled = video.compile()
    warnings = [d for d in compiled.report["diagnostics"] if d["code"] == "FLOW_LABEL_OVERLAP"]
    assert warnings
    assert all(d["segment"] == "feed" and d["placement"] == "feed/block-1" for d in warnings)
    assert any(d.get("source_time") == 2 for d in warnings)
