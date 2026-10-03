"""Reusable visual color roles for equations, diagrams, and video components."""

from dataclasses import dataclass, fields
from types import MappingProxyType

from PIL import ImageColor

from .components import finite


def with_alpha(color: str, opacity: float) -> str:
    """Return a Pillow-compatible RGBA hex color, multiplying any source alpha."""
    opacity = finite(opacity, "opacity", 0)
    if opacity > 1:
        raise ValueError("opacity must be <= 1")
    r, g, b, a = ImageColor.getcolor(color, "RGBA")
    return f"#{r:02x}{g:02x}{b:02x}{round(a * opacity):02x}"


@dataclass(frozen=True)
class ColorScheme:
    """Named color roles; construct a custom scheme or select a built-in preset."""

    name: str = "midnight"
    background: str = "#0b1017"
    surface: str = "#151e2a"
    text: str = "#f4f7fc"
    muted: str = "#bdcadb"
    axis: str = "#7b8ca3"
    border: str = "#394b61"
    grid: str = "#253549"
    primary: str = "#80caff"
    secondary: str = "#ffd17e"
    tertiary: str = "#7de3bb"
    highlight: str = "#cfb0ff"

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("ColorScheme needs a name")
        for field in fields(self):
            if field.name != "name":
                value = getattr(self, field.name)
                if not isinstance(value, str):
                    raise TypeError(f"{field.name} must be a color string")
                try:
                    ImageColor.getcolor(value, "RGBA")
                except ValueError as exc:
                    raise ValueError(f"Invalid {field.name} color: {value}") from exc

    @classmethod
    def named(cls, name: str) -> "ColorScheme":
        try:
            return COLOR_SCHEMES[name]
        except KeyError as exc:
            raise ValueError(f"Unknown color scheme {name!r}; choose {', '.join(COLOR_SCHEMES)}") from exc

    def color(self, role: str) -> str:
        if role == "name" or role not in self.__dataclass_fields__:
            raise ValueError(f"Unknown color role: {role}")
        return getattr(self, role)

    def series(self, index: int) -> str:
        """Cycle through four distinct graph series colors."""
        if not isinstance(index, int) or isinstance(index, bool) or index < 0:
            raise ValueError("series index must be a nonnegative integer")
        return (self.primary, self.secondary, self.tertiary, self.highlight)[index % 4]


COLOR_SCHEMES = MappingProxyType(
    {
        "midnight": ColorScheme(),
        "paper": ColorScheme(
            name="paper",
            background="#f2f0eb",
            surface="#ffffff",
            text="#14202e",
            muted="#455569",
            axis="#718095",
            border="#bdc8d5",
            grid="#dfe5ec",
            primary="#145a9c",
            secondary="#8d580a",
            tertiary="#0b6a54",
            highlight="#7540a5",
        ),
        "ocean": ColorScheme(
            name="ocean",
            background="#071a26",
            surface="#0e293b",
            text="#f2f7fc",
            muted="#b6cddd",
            axis="#789aaf",
            border="#35586e",
            grid="#204256",
            primary="#83d6ff",
            secondary="#ffcf83",
            tertiary="#84edc4",
            highlight="#d5b5ff",
        ),
    }
)
