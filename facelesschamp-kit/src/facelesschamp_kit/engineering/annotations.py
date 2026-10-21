"""Engineering label and dimension presentation records."""

from dataclasses import dataclass

from faceless_champ.integrations.pyvista.model import ArchDataError, color, number, text, vector


def _format_dimension(distance, precision, units):
    return f"{distance:.{precision}f} {units}"


@dataclass(frozen=True)
class ArchLabel:
    text: str
    point: tuple
    part: str | None = None
    offset: tuple = (24, -24)
    color: str = "#ffffff"
    font_size: float = 28

    def __post_init__(self):
        text(self.text, "label.text")
        object.__setattr__(self, "point", vector(self.point, "label.point"))
        if len(self.offset) != 2:
            raise ArchDataError("label.offset", "expected two coordinates")
        object.__setattr__(self, "offset", tuple(number(v, "offset") for v in self.offset))
        color(self.color)
        number(self.font_size, "font_size", 1)


@dataclass(frozen=True)
class ArchDimension:
    start: tuple
    end: tuple
    part: str | None = None
    offset: tuple = (0, 32)
    color: str = "#63d3ff"
    font_size: float = 24
    precision: int = 2

    def __post_init__(self):
        object.__setattr__(self, "start", vector(self.start, "dimension.start"))
        object.__setattr__(self, "end", vector(self.end, "dimension.end"))
        if len(self.offset) != 2:
            raise ArchDataError("dimension.offset", "expected two coordinates")
        object.__setattr__(self, "offset", tuple(number(v, "offset") for v in self.offset))
        color(self.color)
        number(self.font_size, "font_size", 1)
        if isinstance(self.precision, bool) or not isinstance(self.precision, int) or not 0 <= self.precision <= 8:
            raise ArchDataError("precision", "expected integer 0 to 8")
