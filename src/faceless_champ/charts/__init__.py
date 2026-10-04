"""Data-driven chart components; all dimensions are design pixels."""

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field

from PIL import ImageColor

from ..colors import ColorScheme
from ..components import Component, finite
from .scales import Axis, domain, graph_positions, histogram


@dataclass(frozen=True)
class ChartStyle:
    scheme: ColorScheme = field(default_factory=ColorScheme)
    colors: tuple[str, ...] = ()
    font_size: float = 16
    title_size: float = 24
    grid: bool = True
    legend: bool = True

    def __post_init__(self):
        object.__setattr__(self, "colors", tuple(self.colors))
        finite(self.font_size, "font_size", 1)
        finite(self.title_size, "title_size", 1)
        for color in self.colors:
            ImageColor.getcolor(color, "RGBA")

    def color(self, i):
        return self.colors[i % len(self.colors)] if self.colors else self.scheme.series(i)


def numbers(values, name="data"):
    result = tuple(finite(v, name) for v in values)
    if not result:
        raise ValueError(f"{name} must not be empty")
    return result


def labels(values):
    result = tuple(str(v) for v in values)
    if not result or len(set(result)) != len(result):
        raise ValueError("Labels must be nonempty and unique")
    return result


class Chart(Component):
    """Base class with immutable, flat numeric animation state."""

    cartesian = False

    def __init__(self, *, width=640, height=420, title="", style=None, x_axis=None, y_axis=None, **kwargs):
        super().__init__(**kwargs)
        self.width = finite(width, "width", 160)
        self.height = finite(height, "height", 120)
        self.title = str(title)
        self.style = deepcopy(style or ChartStyle())
        self.x_axis, self.y_axis = deepcopy(x_axis or Axis()), deepcopy(y_axis or Axis())

    def state(self):
        return {**super().state(), "data": self.data}

    def transition_data(self, data):
        values = self.normalize(data)
        if len(values) != len(self.data):
            raise ValueError("Data transitions must retain chart structure")
        self.validate_data(values)
        return values

    def validate_data(self, values):
        if len(values) != len(self.data):
            raise ValueError("Data transitions must retain chart structure")
        numbers(values)


class BarChart(Chart):
    cartesian = True

    def __init__(self, categories, series, *, stacked=False, **kwargs):
        super().__init__(**kwargs)
        self.categories, self.names = labels(categories), labels(series)
        self.stacked = bool(stacked)
        if stacked and self.y_axis.scale == "log":
            raise ValueError("Stacked bars cannot use log axes")
        self.data = self.normalize(series)
        self.validate_data(self.data)
        n = len(self.categories)
        bounds = self.data
        if stacked:
            bounds = tuple(sum(max(0, self.data[j * n + i]) for j in range(len(self.names))) for i in range(n)) + tuple(
                sum(min(0, self.data[j * n + i]) for j in range(len(self.names))) for i in range(n)
            )
        self.x_bounds = (-0.5, n - 0.5)
        self.y_bounds = domain(bounds, self.y_axis, zero=True)

    def normalize(self, data):
        if not isinstance(data, Mapping) or tuple(data) != self.names:
            raise ValueError("Series names and order must remain unchanged")
        rows = tuple(numbers(data[name]) for name in self.names)
        if any(len(row) != len(self.categories) for row in rows):
            raise ValueError("Each series needs one value per category")
        return tuple(v for row in rows for v in row)

    def validate_data(self, values):
        super().validate_data(values)
        domain(values, self.y_axis)


class LineChart(Chart):
    cartesian = True

    def __init__(self, series, **kwargs):
        super().__init__(**kwargs)
        self.names = labels(series)
        rows = tuple(tuple(tuple(point) for point in series[name]) for name in self.names)
        self.lengths = tuple(len(row) for row in rows)
        self.data = self.normalize(dict(zip(self.names, rows)))
        self.validate_data(self.data)
        self.x_bounds = domain(self.data[::2], self.x_axis)
        self.y_bounds = domain(self.data[1::2], self.y_axis)

    def normalize(self, data):
        if not isinstance(data, Mapping) or tuple(data) != self.names:
            raise ValueError("Series names and order must remain unchanged")
        rows = tuple(tuple(numbers(point) for point in data[name]) for name in self.names)
        if tuple(len(row) for row in rows) != self.lengths or any(not row for row in rows):
            raise ValueError("Point counts must remain nonzero and unchanged")
        if any(len(point) != 2 for row in rows for point in row):
            raise ValueError("Points must be (x, y) pairs")
        return tuple(v for row in rows for point in row for v in point)

    def validate_data(self, values):
        super().validate_data(values)
        domain(values[::2], self.x_axis)
        domain(values[1::2], self.y_axis)


class ScatterPlot(LineChart):
    def __init__(self, series, *, sizes=None, **kwargs):
        super().__init__(series, **kwargs)
        self.sizes = tuple(5.0 for _ in range(sum(self.lengths))) if sizes is None else numbers(sizes, "sizes")
        if len(self.sizes) != sum(self.lengths) or any(v < 0 for v in self.sizes):
            raise ValueError("sizes needs one nonnegative radius per point in series order")


class Histogram(Chart):
    cartesian = True
    names = ()

    def __init__(self, samples, *, bins=10, **kwargs):
        super().__init__(**kwargs)
        samples = numbers(samples)
        if isinstance(bins, int) and not isinstance(bins, bool):
            if bins < 1:
                raise ValueError("bins must be positive")
            lo, hi = domain(samples, Axis())
            self.edges = tuple(lo + (hi - lo) * i / bins for i in range(bins + 1))
        else:
            self.edges = numbers(bins, "bin edges")
        if len(self.edges) < 2 or any(a >= b for a, b in zip(self.edges, self.edges[1:])):
            raise ValueError("Bin edges must increase strictly")
        if self.y_axis.scale == "log":
            raise ValueError("Histogram counts require a linear y axis")
        self.data = self.normalize(samples)
        self.x_bounds = domain(self.edges, self.x_axis)
        self.y_bounds = domain(self.data, self.y_axis, zero=True)

    def normalize(self, data):
        return histogram(numbers(data), self.edges)

    def validate_data(self, values):
        super().validate_data(values)
        if any(v < 0 for v in values):
            raise ValueError("Histogram counts must be nonnegative")


class Heatmap(Chart):
    def __init__(
        self,
        matrix,
        *,
        row_labels=None,
        column_labels=None,
        color_limits=None,
        palette=("#16324f", "#48e0cb", "#fff2b0"),
        colorbar=True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        rows = tuple(tuple(row) for row in matrix)
        if not rows or not rows[0]:
            raise ValueError("Heatmap matrix must not be empty")
        self.rows, self.columns = len(rows), len(rows[0])
        self.row_labels = labels(row_labels if row_labels is not None else range(self.rows))
        self.column_labels = labels(column_labels if column_labels is not None else range(self.columns))
        if len(self.row_labels) != self.rows or len(self.column_labels) != self.columns:
            raise ValueError("Heatmap labels must match matrix dimensions")
        self.data = self.normalize(rows)
        self.color_bounds = domain(self.data, Axis(limits=color_limits))
        self.palette = tuple(ImageColor.getcolor(c, "RGBA") for c in palette)
        if len(self.palette) < 2:
            raise ValueError("Palette needs at least two colors")
        self.colorbar = bool(colorbar)

    def normalize(self, data):
        rows = tuple(numbers(row) for row in data)
        if len(rows) != self.rows or any(len(row) != self.columns for row in rows):
            raise ValueError("Heatmap matrix shape must remain unchanged")
        return tuple(v for row in rows for v in row)


class NetworkGraph(Chart):
    flow = False

    def __init__(self, nodes, edges, *, weights=None, positions=None, directed=False, **kwargs):
        super().__init__(**kwargs)
        self.nodes = labels(nodes)
        self.edges = tuple(tuple(str(n) for n in edge) for edge in edges)
        if any(len(e) != 2 or any(n not in self.nodes for n in e) for e in self.edges):
            raise ValueError("Edges need two known node IDs")
        if any(a == b for a, b in self.edges):
            raise ValueError("Self-links are unsupported")
        if not self.edges:
            raise ValueError("At least one edge is required")
        auto = graph_positions(self.nodes, self.edges, flow=self.flow)
        positions = positions or {}
        if set(positions) - set(self.nodes):
            raise ValueError("Unknown positioned node")
        self.positions = tuple(
            numbers(positions[n], "position") if n in positions else p for n, p in zip(self.nodes, auto)
        )
        if any(len(p) != 2 or any(v < 0 or v > 1 for v in p) for p in self.positions):
            raise ValueError("Node positions must be normalized (x, y) pairs in [0, 1]")
        self.directed = bool(directed)
        self.data = self.normalize(weights if weights is not None else [1] * len(self.edges))

    def normalize(self, data):
        values = numbers(data, "weights")
        if len(values) != len(self.edges) or any(v < 0 for v in values):
            raise ValueError("Need one nonnegative weight per existing edge")
        return values

    def validate_data(self, values):
        super().validate_data(values)
        self.normalize(values)


class SankeyChart(NetworkGraph):
    flow = True

    def __init__(self, nodes, links, **kwargs):
        links = tuple(tuple(link) for link in links)
        if any(len(link) != 3 for link in links):
            raise ValueError("Sankey links must be (source, target, weight)")
        super().__init__(
            nodes, [(a, b) for a, b, _ in links], weights=[v for _, _, v in links], directed=True, **kwargs
        )


class VectorField(Chart):
    cartesian = True
    names = ()

    def __init__(self, samples, *, vector_scale=1, equal_units=True, **kwargs):
        super().__init__(**kwargs)
        if self.x_axis.scale == "log" or self.y_axis.scale == "log":
            raise ValueError("Vector fields require linear spatial axes")
        self.vector_scale = finite(vector_scale, "vector_scale", 0)
        self.equal_units = bool(equal_units)
        self.data = self.normalize(samples)
        self.x_bounds = domain(
            self.data[::4] + tuple(x + dx * self.vector_scale for x, dx in zip(self.data[::4], self.data[2::4])),
            self.x_axis,
        )
        self.y_bounds = domain(
            self.data[1::4] + tuple(y + dy * self.vector_scale for y, dy in zip(self.data[1::4], self.data[3::4])),
            self.y_axis,
        )

    def normalize(self, data):
        rows = tuple(numbers(row) for row in data)
        if not rows or any(len(row) != 4 for row in rows):
            raise ValueError("Vector samples must be (x, y, dx, dy)")
        return tuple(v for row in rows for v in row)


class PieChart(Chart):
    def __init__(self, categories, values, *, hole=0, **kwargs):
        super().__init__(**kwargs)
        self.categories = labels(categories)
        self.hole = finite(hole, "hole", 0)
        if self.hole >= 1:
            raise ValueError("hole must be less than 1")
        self.data = self.normalize(values)

    def normalize(self, data):
        values = numbers(data)
        if len(values) != len(self.categories) or any(v < 0 for v in values) or sum(values) <= 0:
            raise ValueError("Pie values must match categories, be nonnegative and have positive total")
        return values

    def validate_data(self, values):
        super().validate_data(values)
        self.normalize(values)


__all__ = [
    "Axis",
    "BarChart",
    "Chart",
    "ChartStyle",
    "Heatmap",
    "Histogram",
    "LineChart",
    "NetworkGraph",
    "PieChart",
    "SankeyChart",
    "ScatterPlot",
    "VectorField",
]
