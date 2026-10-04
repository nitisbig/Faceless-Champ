"""Numeric chart contracts and deterministic rendering through the public timeline."""

import pytest

from faceless_champ import (
    Animation,
    Axis,
    BarChart,
    Canvas,
    ChartReveal,
    ChartStyle,
    ColorScheme,
    Grid,
    Heatmap,
    Histogram,
    Layer,
    LineChart,
    NetworkGraph,
    PieChart,
    PillowRenderer,
    SankeyChart,
    ScatterPlot,
    Scene,
    VectorField,
    linear,
)
from faceless_champ.charts.scales import domain, graph_positions, project, ticks


def charts():
    return [
        BarChart(["A", "B"], {"revenue": [2, -1]}, y_axis=Axis(limits=(-3, 4))),
        LineChart({"wave": [(0, 0), (1, 2), (2, 1)]}),
        ScatterPlot({"samples": [(0, 0), (1, 2)]}, sizes=[4, 8]),
        Histogram([0, 1, 2, 2, 3], bins=[0, 1, 2, 3]),
        Heatmap([[0, 1], [2, 3]]),
        NetworkGraph(["A", "B", "C"], [("A", "B"), ("B", "C")], directed=True),
        VectorField([(0, 0, 1, 1), (1, 1, -1, 0)]),
        SankeyChart(["A", "B", "C"], [("A", "B", 2), ("A", "C", 1)]),
        PieChart(["A", "B"], [2, 1], hole=0.3),
    ]


def test_scales_and_ticks():
    assert domain([3, 3], Axis()) == pytest.approx((2.7, 3.3))
    assert domain([2, 8], Axis(), zero=True) == (0, 8)
    assert project(10, (1, 100), "log") == 0.5
    assert ticks((0, 10), Axis()) == (0, 2, 4, 6, 8, 10)
    assert ticks((1, 1000), Axis(scale="log")) == (1, 10, 100, 1000)
    assert ticks((0, 10), Axis(ticks=(-1, 3, 11))) == (3,)
    assert Axis(unit="%", formatter=lambda v: f"{v:.1f}%").format(3) == "3.0%"
    with pytest.raises(ValueError, match="positive"):
        domain([0, 1], Axis(scale="log"))


def test_data_copy_bounds_and_histogram():
    series = {"one": [3, -2], "two": [4, -5]}
    c = BarChart(["a", "b"], series, stacked=True)
    series["one"][0] = 100
    assert c.data == (3, -2, 4, -5)
    assert c.y_bounds == (-7, 7)
    h = Histogram([0, 0.5, 1, 2, 3], bins=[0, 1, 2, 3])
    assert h.data == (2, 1, 2)
    assert h.transition_data([-1, 0, 3, 4]) == (1, 0, 1)
    assert Histogram([1, 1], bins=2).data == (0, 2)
    assert Heatmap([[5, 5]]).color_bounds == (4.5, 5.5)


def test_layout_and_vector_domains():
    nodes = ("a", "b", "c")
    edges = (("a", "b"), ("b", "c"))
    assert graph_positions(nodes, edges) == graph_positions(nodes, edges)
    positions = graph_positions(nodes, edges, flow=True)
    assert positions[0][0] < positions[1][0] < positions[2][0]
    v = VectorField([(0, 0, 2, -3)], vector_scale=2)
    assert v.x_bounds == (0, 4)
    assert v.y_bounds == (-6, 0)
    n = NetworkGraph(nodes, edges, positions={"a": (0.1, 0.2)})
    assert n.positions[0] == (0.1, 0.2)


@pytest.mark.parametrize(
    "factory",
    [
        lambda: LineChart({"a": []}),
        lambda: LineChart({"a": [(1, 2, 3)]}),
        lambda: BarChart(["a"], {"b": [float("nan")]}),
        lambda: BarChart(["a"], {"b": [1]}, stacked=True, y_axis=Axis(scale="log")),
        lambda: BarChart(["a"], {"b": [0]}, y_axis=Axis(scale="log")),
        lambda: Heatmap([[1], [2, 3]]),
        lambda: Histogram([1], bins=[0, 0]),
        lambda: PieChart(["a"], [0]),
        lambda: PieChart(["a"], [-1]),
        lambda: NetworkGraph(["a"], [("a", "b")]),
        lambda: SankeyChart(["a", "b"], [("a", "b", 1), ("b", "a", 1)]),
        lambda: SankeyChart(["a"], [("a", "a", 1)]),
        lambda: VectorField([(1, 2, 3)]),
    ],
)
def test_reject_invalid_inputs(factory):
    with pytest.raises((ValueError, TypeError)):
        factory()


def test_chained_data_transitions_and_rejected_shapes():
    chart = BarChart(["a", "b"], {"s": [0, 2]})
    scene = Scene().add(chart)
    scene.play(chart.animate.data_to({"s": [4, 6]}), run_time=2, rate_func=linear)
    scene.play(chart.animate.data_to({"s": [8, 10]}), run_time=2, rate_func=linear)
    entry = scene.entries[0]
    assert entry.state_at(0)["data"] == (0, 2)
    assert entry.state_at(1)["data"] == (2, 4)
    assert entry.state_at(2)["data"] == (4, 6)
    assert entry.state_at(3)["data"] == (6, 8)
    assert entry.state_at(4)["data"] == (8, 10)
    assert chart.data == (0, 2)
    for data in ({"s": [1]}, {"other": [1, 2]}):
        with pytest.raises(ValueError):
            chart.animate.data_to(data)
    with pytest.raises(ValueError):
        Scene().play(Animation(chart, {"data": (1,)}))
    with pytest.raises(ValueError):
        LineChart({"a": [(1, 1)]}, x_axis=Axis(scale="log")).animate.data_to({"a": [(0, 1)]})


@pytest.mark.parametrize("chart", charts(), ids=lambda c: type(c).__name__)
def test_reveal_rendering_composition_and_cache(chart):
    chart.move_to(320, 210)
    scene = Scene(Canvas(640, 420))
    scene.play(ChartReveal(chart), run_time=1).wait(1)
    cached, uncached = PillowRenderer(1), PillowRenderer(1, frame_cache_mb=0)
    cached.validate(scene)
    blank = cached.frame(scene, 0, (640, 420)).tobytes()
    full = cached.frame(scene, 1, (640, 420)).tobytes()
    assert blank != full
    for time in (1, 0.5, 0, 1.5, 0.5):
        assert cached.frame(scene, time, (640, 420)).tobytes() == uncached.frame(scene, time, (640, 420)).tobytes()
    assert not cached._sprites
    for node in (Grid(scene, rows=1, columns=1), Layer(scene)):
        cached.validate(node)
        assert cached.frame(node, 1, (640, 420)).tobytes() == full


@pytest.mark.parametrize(
    "chart,target",
    [
        (BarChart(["a", "b"], {"s": [1, 3]}), {"s": [3, 1]}),
        (LineChart({"s": [(0, 0), (1, 1)]}), {"s": [(0, 1), (1, 0)]}),
        (ScatterPlot({"s": [(0, 0), (1, 1)]}), {"s": [(0, 1), (1, 0)]}),
        (Histogram([0, 0, 1], bins=[0, 1, 2]), [0, 1, 1]),
        (Heatmap([[0, 1]]), [[1, 0]]),
        (NetworkGraph(["a", "b"], [("a", "b")]), [6]),
        (SankeyChart(["a", "b", "c"], [("a", "b", 1), ("a", "c", 3)]), [3, 1]),
        (VectorField([(0, 0, 1, 1)]), [(0, 0, 1, 0)]),
        (PieChart(["a", "b"], [1, 3]), [3, 1]),
    ],
)
def test_data_animation_changes_pixels_without_stale_cache(chart, target):
    chart.move_to(320, 210)
    scene = Scene(Canvas(640, 420)).add(chart)
    scene.play(chart.animate.data_to(target), run_time=1)
    renderer = PillowRenderer(1)
    initial = renderer.frame(scene, 0, (640, 420)).tobytes()
    final = renderer.frame(scene, 1, (640, 420)).tobytes()
    assert initial != final
    assert renderer.frame(scene, 0, (640, 420)).tobytes() == initial
    assert renderer.frame(scene, 1, (640, 420)).tobytes() == final


def test_style_and_transforms():
    c = PieChart(
        ["one", "two"],
        [1, 2],
        style=ChartStyle(scheme=ColorScheme.named("paper")),
        position=(40, 30),
        anchor="top_left",
        scale=0.5,
        rotation=15,
        opacity=0.5,
    )
    scene = Scene(Canvas(640, 420)).add(c).wait(1)
    frame = PillowRenderer().frame(scene, 0, (640, 420))
    assert frame.getbbox() == (0, 0, 640, 420)


def test_sankey_width_conservation_and_color_clamping():
    from faceless_champ.charts.scales import palette_color, sankey_geometry

    heights, ribbons = sankey_geometry(
        ("a", "b", "c"),
        (("a", "b"), ("a", "c")),
        (2, 3),
        {"a": (0, 50), "b": (100, 25), "c": (100, 75)},
        100,
    )
    assert ribbons[0][2] / ribbons[1][2] == pytest.approx(2 / 3)
    assert heights["a"] == pytest.approx(ribbons[0][2] + ribbons[1][2])
    assert heights["b"] == ribbons[0][2]
    assert ribbons[1][0] == pytest.approx(ribbons[0][0] + ribbons[0][2])
    palette = ((0, 0, 0, 255), (100, 200, 100, 255))
    assert palette_color(0.5, (0, 1), palette) == (50, 100, 50, 255)
    assert palette_color(-1, (0, 1), palette) == palette[0]
    assert palette_color(2, (0, 1), palette) == palette[1]


def test_dense_histogram_log_chart_and_clipped_transition():
    charts = [
        Histogram([i / 100 for i in range(100)], bins=400),
        BarChart(["a", "b"], {"s": [1, 10]}, y_axis=Axis(scale="log")),
        LineChart({"s": [(1, 1), (10, 100)]}, x_axis=Axis(scale="log"), y_axis=Axis(scale="log")),
    ]
    for chart in charts:
        chart.move_to(320, 210)
        scene = Scene(Canvas(640, 420)).play(ChartReveal(chart), run_time=1)
        PillowRenderer(1).frame(scene, 0.5, (640, 420))
    bar = BarChart(["a"], {"s": [1]}, y_axis=Axis(limits=(0, 2)), position=(320, 210))
    scene = Scene(Canvas(640, 420)).play(bar.animate.data_to({"s": [100]}), run_time=1)
    assert scene.entries[0].component.y_bounds == (0, 2)
    PillowRenderer(1).frame(scene, 1, (640, 420))


def test_raw_data_keyframes_and_structural_rejection():
    pie = PieChart(["a", "b"], [1, 2])
    with pytest.raises(ValueError):
        Scene().play(Animation(pie, {"data": (2, 1)}, keyframes={"data": ((0, (1, 2)), (0.5, (-1, 4)), (1, (2, 1)))}))
    for chart, target in [
        (Heatmap([[1, 2], [3, 4]]), [[1, 2, 3, 4]]),
        (VectorField([(0, 0, 1, 1)]), [(0, 0, 1, 1), (1, 1, 2, 2)]),
        (LineChart({"a": [(0, 0)], "b": [(1, 1)]}), {"a": [(0, 0), (1, 1)], "b": []}),
        (NetworkGraph(["a", "b"], [("a", "b")]), [-1]),
    ]:
        with pytest.raises(ValueError):
            chart.animate.data_to(target)
