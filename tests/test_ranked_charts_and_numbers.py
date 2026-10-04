"""Regression coverage for ranking motion, missing observations and live numbers."""

import pytest

from faceless_champ import (
    Animation,
    Axis,
    Canvas,
    ChartStyle,
    ColorScheme,
    Number,
    PillowRenderer,
    RankedBarChart,
    Scene,
    Text,
    linear,
)
from faceless_champ.charts.drawing import draw_chart
from faceless_champ.charts.scales import separate_positions


def style():
    return ChartStyle(scheme=ColorScheme.named("paper"), colors=("#ff0000", "#0000ff", "#00ff00"))


def test_rank_transitions_preserve_identity_and_interpolate_positions():
    chart = RankedBarChart({"A": 8, "B": 4, "C": 2}, style=style(), x_axis=Axis(limits=(0, 10)))
    scene = Scene(Canvas(640, 420)).play(chart.animate.data_to({"A": 2, "B": 8, "C": 4}), run_time=2, rate_func=linear)
    scene.play(chart.animate.data_to({"A": 9, "B": 6, "C": 3}), run_time=2, rate_func=linear)
    entry = scene.entries[0]
    assert entry.state_at(1)["data"][:6] == (5, 6, 3, 1, 0.5, 1.5)
    assert entry.state_at(2)["data"][:6] == (2, 8, 4, 2, 0, 1)
    assert entry.state_at(4)["data"][:6] == (9, 6, 3, 0, 1, 2)
    assert chart.data[:3] == (8, 4, 2)
    before = draw_chart(chart, entry.state_at(0), 1)
    after = draw_chart(chart, entry.state_at(2), 1)
    # A's red bar changes row but retains its category color.
    red_before = [y for y in range(420) if before.getpixel((250, y))[:3] == (255, 0, 0)]
    red_after = [y for y in range(420) if after.getpixel((250, y))[:3] == (255, 0, 0)]
    assert red_before and red_after and min(red_after) > max(red_before)


def test_missing_observation_appears_only_at_known_snapshot():
    chart = RankedBarChart({"A": 4, "B": None}, style=style(), x_axis=Axis(limits=(0, 10)))
    scene = Scene(Canvas(640, 420)).play(chart.animate.data_to({"A": 4, "B": 8}), run_time=2, rate_func=linear)
    entry = scene.entries[0]
    midpoint = draw_chart(chart, entry.state_at(1), 1)
    final = draw_chart(chart, entry.state_at(2), 1)
    # The blue identity dot is outside this region; only the bar is measured.
    region = (230, 0, 450, 340)
    assert (0, 0, 255, 255) not in {color for _, color in midpoint.crop(region).getcolors(region[2] * region[3])}
    assert (0, 0, 255, 255) in {color for _, color in final.crop(region).getcolors(region[2] * region[3])}
    zeros = RankedBarChart({"Zero": 0, "Missing": None})
    assert zeros.data[-2:] == (1, 0)


def test_ranked_and_number_frames_are_deterministic_without_sprite_accumulation():
    chart = RankedBarChart({"A": 1, "B": 2}, style=style(), position=(320, 210))
    number = Number(-10, prefix="$", suffix="B", width=180, font_size=25, position=(300, 100))
    scene = Scene(Canvas(640, 420)).play(
        chart.animate.data_to({"A": 12, "B": 3}),
        number.animate.value_to(20),
        run_time=2,
        rate_func=linear,
    )
    renderer = PillowRenderer(1)
    renderer.validate(scene)
    start = renderer.frame(scene, 0, (640, 420)).tobytes()
    end = renderer.frame(scene, 2, (640, 420)).tobytes()
    assert start != end
    for i in range(25):
        renderer.frame(scene, i / 12, (640, 420))
    assert renderer.frame(scene, 0, (640, 420)).tobytes() == start
    assert renderer.frame(scene, 2, (640, 420)).tobytes() == end
    assert not renderer._sprites


def test_number_chaining_signed_values_and_fixed_alignment():
    number = Number(10, font_size=32, width=220, align="right", formatter=lambda v: f"{v:.1f}%")
    scene = Scene().play(number.animate.value_to(-20), run_time=2, rate_func=linear)
    scene.play(number.animate.value_to(40), run_time=2, rate_func=linear)
    entry = scene.entries[0]
    assert entry.state_at(1)["value"] == -5
    assert entry.state_at(3)["value"] == 10
    assert number.value == 10
    renderer = PillowRenderer(1)
    first = renderer._sprite(entry.component, entry.state_at(0), 1, 0)
    second = renderer._sprite(entry.component, entry.state_at(2), 1, 2)
    assert first.width == second.width == 224
    assert number.format(-5) == "-5.0%"
    with pytest.raises(ValueError, match="fixed width"):
        renderer._sprite(Number(100000, width=1), Number(100000).state(), 1, 0)


@pytest.mark.parametrize(
    "values,kwargs",
    [
        ({"A": -1}, {}),
        ({"A": float("nan")}, {}),
        ({"A": 1}, {"top_n": True}),
        ({"A": 1}, {"top_n": 2}),
        ({"A": 1}, {"x_axis": Axis(scale="log")}),
        ({"A": 1}, {"x_axis": Axis(limits=(1, 3))}),
    ],
)
def test_ranked_invalid_input_is_rejected(values, kwargs):
    with pytest.raises(ValueError):
        RankedBarChart(values, **kwargs)


def test_structural_transitions_and_invalid_numeric_animation_are_rejected():
    chart = RankedBarChart({"A": 1, "B": 2})
    with pytest.raises(ValueError, match="order"):
        chart.animate.data_to({"B": 2, "A": 1})
    with pytest.raises(ValueError, match="structure"):
        Scene().play(Animation(chart, {"data": (1, 2)}))
    with pytest.raises(ValueError, match="finite"):
        Number(0).animate.value_to(float("inf"))
    with pytest.raises(TypeError, match="Number"):
        Text("a").animate.value_to(1)
    with pytest.raises(ValueError, match="single line"):
        Number(1, formatter=lambda v: "a\nb")


def test_top_n_and_label_overflow():
    chart = RankedBarChart({"A": 3, "B": 2, "C": 1}, top_n=1, style=style())
    image = draw_chart(chart, chart.state(), 1)
    assert (0, 0, 255, 255) not in {color for _, color in image.getcolors(image.width * image.height)}
    with pytest.raises(ValueError, match="label_width"):
        c = RankedBarChart({"A very long company name": 1}, label_width=20)
        draw_chart(c, c.state(), 1)


def test_crossing_labels_stay_separated_and_top_n_does_not_go_blank():
    desired = (70, 40, 40, 100)
    actual = separate_positions(desired, 20, (10, 110))
    assert min(actual) >= 10 and max(actual) <= 110
    assert all(b - a >= 20 for a, b in zip(sorted(actual), sorted(actual)[1:]))
    chart = RankedBarChart({"A": 8, "B": 2}, top_n=1, style=style())
    scene = Scene().play(chart.animate.data_to({"A": 2, "B": 8}), run_time=2, rate_func=linear)
    image = draw_chart(chart, scene.entries[0].state_at(1), 1)
    colors = {color for _, color in image.crop((230, 20, 440, 380)).getcolors(100000)}
    assert (255, 0, 0, 255) in colors or (0, 0, 255, 255) in colors
