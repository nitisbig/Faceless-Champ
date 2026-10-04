# Data-driven charts

Charts are ordinary Faceless Champ components, rendered with Pillow. No additional
runtime dependency is required. Supply Python sequences and mappings; load files or
compute samples in your application. All examples below use synthetic data.

```python
from faceless_champ import Axis, BarChart, Canvas, ChartReveal, Scene

chart = BarChart(
    ["Q1", "Q2", "Q3"],
    {"Revenue": [3, 5, 4], "Costs": [-2, -3, -2]},
    width=1000, height=580, position=(640, 360),
    title="Quarterly cash flow",
    y_axis=Axis(limits=(-4, 8), unit="M", label="USD millions"),
)
scene = Scene(Canvas(1280, 720))
scene.play(ChartReveal(chart), run_time=1)
scene.play(chart.animate.data_to({"Revenue": [5, 6, 7], "Costs": [-3, -2, -3]}), run_time=2)
scene.wait(1)
scene.render("output/revenue.mp4", width=1280, height=720, fps=24, overwrite=True)
```

## Constructors and data contracts

Every chart accepts `width=640`, `height=420`, `title=""`, `style=ChartStyle()`,
plus component `position`, `anchor`, `scale`, `rotation`, `opacity`, and `z_index`.
Width and height include the plot, labels, title and legend. Minimum dimensions are
160 by 120 design pixels; use larger charts when labels need more space. Layout
measures labels and raises a useful error if they leave no usable plot area.

```python
from faceless_champ import (
    Axis, BarChart, Heatmap, Histogram, LineChart, NetworkGraph,
    PieChart, SankeyChart, ScatterPlot, VectorField,
)

bars = BarChart(["A", "B"], {"One": [2, -1], "Two": [3, -2]}, stacked=True)
line = LineChart({"f(x)": [(0, 0), (1, 1), (2, 4)]})
scatter = ScatterPlot({"Measured": [(0, 1), (1, 2)]}, sizes=[4, 8])
histogram = Histogram([0, .2, .7, 1, 2], bins=[0, 1, 2])
heatmap = Heatmap([[1, .4], [.4, 1]], row_labels=["A", "B"],
                  column_labels=["A", "B"], color_limits=(-1, 1))
network = NetworkGraph(["A", "B", "C"], [("A", "B"), ("B", "C")],
                       weights=[2, 1], directed=True)
field = VectorField([(0, 0, 1, 0), (1, 1, 0, -1)], vector_scale=.5)
sankey = SankeyChart(["Income", "Spend", "Save"],
                     [("Income", "Spend", 70), ("Income", "Save", 30)])
pie = PieChart(["Equity", "Bonds", "Cash"], [50, 35, 15], hole=.5)
```

- **BarChart(categories, series, stacked=False):** series is an insertion-ordered
  mapping of string names to values, one per category. Stacks accumulate positive
  and negative values separately. Linear bars include zero in automatic limits.
  Categories use evenly spaced positions; numeric `x_axis` limits/scales/ticks do
  not apply to this categorical axis. Its label can still be set.
- **RankedBarChart(values, top_n=None, label_width=180, value_width=100,
  value_formatter=None, missing_label="No data"):** a mapping of category names
  to nonnegative values or `None`. Bars sort by value, with stable ties and colors.
  `chart.animate.data_to(mapping)` animates both values and row positions, retaining
  category names and order. Crossing labels are separated to remain readable.
  Missing values have labels but no bar; a new observation appears at the known
  endpoint of a transition. `top_n` limits visible rows. Automatic x limits follow
  the largest visible value; `x_axis=Axis(limits=(0, maximum))` fixes the scale.
  Ranked bars require linear axes starting at zero. Label widths are design pixels;
  increase them when formatted labels do not fit. The value formatter defaults
  to `x_axis.format`. Ranked bars have inline labels, without a separate legend.
- **LineChart(series):** each named series contains nonempty `(x, y)` pairs.
  Points connect in supplied order; they are not sorted. Single points are shown
  as dots. Functions must be sampled by the caller.
- **ScatterPlot(series, sizes=None):** same point data. Optional sizes are
  nonnegative radii in design pixels, flattened in series insertion order.
- **Histogram(samples, bins=10):** bins is a positive integer or increasing edge
  sequence. Intervals include their left edge; the final interval also includes
  its right edge. Samples outside explicit edges are ignored. Constant samples
  receive a nonzero automatic span. Counts require a linear y axis.
- **Heatmap(matrix, row_labels=None, column_labels=None, color_limits=None,
  palette=(...), colorbar=True):** a nonempty rectangular matrix. Row zero is at
  the top. Default labels are indices. Palette accepts two or more color strings;
  intermediate colors interpolate, with out-of-range values clamped to endpoints.
- **NetworkGraph(nodes, edges, weights=None, positions=None, directed=False):**
  unique node IDs and `(source, target)` edges. Weights default to 1 and control
  line width, capped at 12 design pixels. Positions are optional node-to-`(x,y)`
  mappings in normalized `[0,1]` coordinates, with y increasing downward.
  Unspecified nodes use a deterministic circular layout. Cycles are supported;
  self-links and unknown node references are rejected.
- **VectorField(samples, vector_scale=1, equal_units=True):** nonempty
  `(x, y, dx, dy)` samples. Arrow endpoints are `(x + dx * vector_scale,
  y + dy * vector_scale)`. Linear spatial axes and equal units preserve directions
  and relative lengths. `equal_units=False` allows independent axis stretching.
- **SankeyChart(nodes, links, positions=None):** `(source, target, weight)` links
  with nonnegative weights. Uses deterministic topological layers; cycles and
  self-links are rejected. Optional positions use the network coordinate system.
  Ribbons share a weight scale and node heights use the greater incoming/outgoing
  total, allowing sources, sinks, and unequal totals. Numeric amounts are never
  silently rebalanced. All-zero flows show only minimal node markers.
- **PieChart(categories, values, hole=0):** nonnegative values with a positive
  total. `hole` is a radius fraction in `[0,1)`; positive values create a donut.

Labels must be unique. Inputs are copied and normalized to immutable numeric tuples;
empty, ragged and nonfinite numeric data is rejected. These are charting tools, not
financial calculations or statistical estimators beyond histogram counts.

## Axes and themes

Cartesian charts accept `x_axis=Axis(...)` and `y_axis=Axis(...)`. `Axis` supports
`scale="linear"` or `"log"`, increasing `limits=(low, high)`, explicit `ticks`,
`label`, `unit`, and a numeric-to-string `formatter`. Without a formatter, units
are appended to tick values. Log axes require strictly positive values, limits,
and ticks. Stacked bars cannot use log axes; ordinary log bars reveal from the
lower axis bound. Tick labels are thinned horizontally to avoid collisions.

```python
from faceless_champ import Axis, ChartStyle, ColorScheme, LineChart

chart = LineChart(
    {"Growth": [(1, 10), (2, 100), (3, 1000)]},
    y_axis=Axis(scale="log", limits=(1, 10000), label="Value"),
    style=ChartStyle(scheme=ColorScheme.named("paper"),
                     colors=("#145a9c", "#8d580a"),
                     font_size=18, title_size=28, grid=True, legend=True),
)
```

Themes include `midnight`, `paper`, and `ocean`. Series colors cycle through the
provided colors or the theme's four series colors. Legends wrap into rows. Charts
use the bundled font and theme surface background. Transform the chart as a whole
using the standard component animation builder.

## Animation and fixed domains

`ChartReveal(chart)` grows bars from their baselines, traces lines by path length,
grows scatter radii, fades heatmap cells, draws edges/arrows, extends flow ribbons,
and sweeps pie sectors. Axes, legends, labels, and graph nodes remain visible.

`chart.animate.data_to(data)` interpolates numeric values using `Scene.play` timing
and easing. Supply the same data shape as the constructor, except:

- For histograms, supply new **samples**; the original bin edges produce target counts.
- For network and Sankey charts, supply **weights in original edge/link order**.

Category/series order, point counts, matrix dimensions, and graph topology stay
fixed. Positions and scatter radii are configuration, not transition data. Structural
changes are rejected before rendering. Successive transitions start from the preceding
timeline state; they do not mutate the source component. Built-in easing functions
keep interpolation within valid endpoints; custom easing should stay within `[0,1]`.

Except for ranked bars, automatic axis and heatmap color limits are derived once from the initial data and
remain fixed. Set explicit limits to cover all animation keyframes. Marks outside
axis limits are clipped; labels are drawn separately. Sankey layout positions stay
fixed while ribbon and node sizes recompute from the interpolated weights.

Charts work in `Scene`, `Grid`, `Layer`, and `Sequence`. Rendering any frame out of
order is deterministic. Chart sprites are not accumulated per frame; held scene
frames use the renderer's existing bounded cache.

## Ranking races and live numbers

`Number` displays an interpolated numeric value, using the normal scene animation
builder. Its `format_spec`, `prefix`, `suffix`, or callable `formatter` control text.
An optional `width` keeps the alignment box stable as digits change. Signed values
are supported. Width overflow is rejected rather than silently clipping text.
Dynamic number sprites are not retained in the renderer's sprite cache; chart fonts
use a bounded cache shared by chart types.

```python
from faceless_champ import Canvas, ColorScheme, ChartStyle, Number, RankedBarChart, Scene

chart = RankedBarChart(
    {"Alpha": 8, "Beta": 4, "New entrant": None},
    style=ChartStyle(scheme=ColorScheme.named("paper")),
    position=(400, 300),
)
year = Number(2010, format_spec=".0f", width=180, font_size=50, color="#14202e", position=(960, 100))
scene = Scene(Canvas(1280, 720, "#f2f0eb"))
scene.add(chart, year)
scene.play(chart.animate.data_to({"Alpha": 12, "Beta": 18, "New entrant": 6}),
           year.animate.value_to(2011), run_time=2)
```

The [`company-growth` training project](../training%20project/company-growth/README.md)
composes these public APIs into a 45-second light-mode video with a sourced offline
data snapshot, ranking race, trend lines, and summary. Render it with:

```bash
uv run python 'training project/company-growth/render.py' --preview
uv run python 'training project/company-growth/render.py' --frames
```

## Showcase

Run from the repository root using the installed environment:

```bash
uv run python examples/charts/render.py --preview
uv run python examples/charts/render.py --storyboard
uv run python examples/charts/render.py --theme paper --frame 3.5
uv run python examples/charts/render.py --theme ocean --output output/charts.mp4 --overwrite
```

The 36-second showcase covers every chart with a reveal and data transition.
Preview renders at 640×360/12 fps; default video is 1280×720/24 fps. Storyboards
include reveal, transition midpoint, and final frames for each chart. `--output`
selects a video file, frame PNG, or storyboard directory according to mode.
