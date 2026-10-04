"""Reusable styling and typography behavior introduced by the company-growth scene."""

from dataclasses import replace
from pathlib import Path

import pytest

from faceless_champ import (
    Axis,
    Canvas,
    ChartReveal,
    ChartStyle,
    ColorScheme,
    Ellipse,
    LineChart,
    PillowRenderer,
    RankedBarChart,
    Scene,
    Text,
)
from faceless_champ.charts.drawing import draw_chart

SERIF = Path(__file__).parents[1] / "assets" / "fonts" / "CormorantGaramond[wght].ttf"


@pytest.mark.skipif(not SERIF.is_file(), reason="Optional example font is unavailable")
def test_chart_custom_variable_font_weights_do_not_share_mutable_font_state():
    style = ChartStyle(
        scheme=ColorScheme.named("paper"),
        font=SERIF,
        font_weight=300,
        title_font=SERIF,
        title_font_weight=600,
        font_size=34,
    )
    chart = RankedBarChart(
        {"Company Alpha": 8, "Company Beta": 4}, style=style, title="Company value", width=800, label_width=280
    )
    heavier = RankedBarChart(
        {"Company Alpha": 8, "Company Beta": 4},
        style=replace(style, font_weight=700),
        title="Company value",
        width=800,
        label_width=280,
    )
    before = draw_chart(chart, chart.state(), 1).tobytes()
    assert draw_chart(heavier, heavier.state(), 1).tobytes() != before
    assert draw_chart(chart, chart.state(), 1).tobytes() == before
    assert chart.style.font == str(SERIF)


def test_invalid_fonts_are_reported_for_both_text_and_charts(tmp_path):
    chart = LineChart({"A": [(0, 1), (1, 2)]}, style=ChartStyle(font=tmp_path / "missing.ttf"))
    with pytest.raises(ValueError, match="Cannot load font"):
        draw_chart(chart, chart.state(), 1)
    with pytest.raises(ValueError, match="variable font"):
        c = RankedBarChart({"A": 1}, style=ChartStyle(font_weight=400))
        draw_chart(c, c.state(), 1)
    with pytest.raises(ValueError, match="variable font"):
        PillowRenderer().validate(Scene().add(Text("A", font_weight=400)).wait(1))


def test_line_endpoint_labels_are_outside_the_plot_and_wait_for_reveal():
    chart = LineChart(
        {"Alpha": [(0, 1), (1, 5)], "Beta": [(0, 9), (0.75, 5)]},
        end_labels=True,
        x_axis=Axis(limits=(0, 1)),
        y_axis=Axis(limits=(0, 10)),
        style=ChartStyle(scheme=ColorScheme.named("paper"), colors=("red", "blue"), legend=False, grid=False),
    )
    scene = Scene().play(ChartReveal(chart), run_time=1)
    before = draw_chart(chart, scene.entries[0].state_at(0.5), 1)
    after = draw_chart(chart, scene.entries[0].state_at(1), 1)
    band = (560, 0, 640, 420)
    before_colors = {c for _, c in before.crop(band).getcolors(40000)}
    after_colors = {c for _, c in after.crop(band).getcolors(40000)}
    assert (255, 0, 0, 255) not in before_colors and (0, 0, 255, 255) not in before_colors
    assert (255, 0, 0, 255) in after_colors and (0, 0, 255, 255) in after_colors


def test_ranked_bar_thickness_and_optional_identity_markers():
    kwargs = {
        "values": {"A": 8, "B": 4},
        "x_axis": Axis(limits=(0, 10)),
        "style": ChartStyle(scheme=ColorScheme.named("paper"), colors=("red", "blue")),
    }
    regular = RankedBarChart(**kwargs)
    thin = RankedBarChart(**kwargs, bar_height=7, corner_radius=0, show_markers=False)
    a, b = draw_chart(regular, regular.state(), 1), draw_chart(thin, thin.state(), 1)
    normal_rows = [y for y in range(420) if a.getpixel((250, y)) == (255, 0, 0, 255)]
    thin_rows = [y for y in range(420) if b.getpixel((250, y)) == (255, 0, 0, 255)]
    assert 0 < len(thin_rows) <= 9 < len(normal_rows)
    colors = {c for _, c in b.crop((20, 20, 40, 360)).getcolors(7000)}
    assert (255, 0, 0, 255) not in colors and (0, 0, 255, 255) not in colors


def test_ellipse_retains_independent_width_and_height():
    scene = (
        Scene(Canvas(220, 100, "white"))
        .add(
            Ellipse(width=180, height=36, fill="red", stroke=None, position=(110, 50)),
        )
        .wait(1)
    )
    renderer = PillowRenderer(1)
    renderer.validate(scene)
    frame = renderer.frame(scene, 0, (220, 100))
    pixels = [(x, y) for x in range(220) for y in range(100) if frame.getpixel((x, y)) == (255, 0, 0, 255)]
    assert max(x for x, _ in pixels) - min(x for x, _ in pixels) >= 178
    assert max(y for _, y in pixels) - min(y for _, y in pixels) <= 38
    assert frame.getpixel((110, 50)) == (255, 0, 0, 255)
    assert frame.getpixel((20, 32)) == (255, 255, 255, 255)


@pytest.mark.parametrize(
    "factory",
    [
        lambda: ChartStyle(line_width=0),
        lambda: ChartStyle(font_weight=-1),
        lambda: ChartStyle(title_font_weight=float("nan")),
        lambda: RankedBarChart({"A": 1}, bar_height=0),
        lambda: RankedBarChart({"A": 1}, corner_radius=-1),
    ],
)
def test_invalid_styling_is_rejected(factory):
    with pytest.raises(ValueError):
        factory()
