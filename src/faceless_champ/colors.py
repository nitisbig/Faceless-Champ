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
        "clean-flow": ColorScheme(
            name="clean-flow",
            background="#E8E6E2",
            surface="#FFFFFF",
            text="#111111",
            muted="#737373",
            axis="#A6A19B",
            border="#D9D6D0",
            grid="#E8E6E2",
            primary="#FF5A20",
            secondary="#73A6A2",
            tertiary="#E8B660",
            highlight="#A69AC6",
        ),
        "neon": ColorScheme(
            name="neon",
            background="#07070C",
            surface="#12121C",
            text="#F5F7FF",
            muted="#A3A8BF",
            axis="#5E6380",
            border="#2A2B40",
            grid="#1A1B2A",
            primary="#2EE6FF",
            secondary="#FF4FA3",
            tertiary="#B8FF4A",
            highlight="#9A8CFF",
        ),
        "documentary": ColorScheme(
            name="documentary",
            background="#0F0D0B",
            surface="#1B1815",
            text="#F4EEE5",
            muted="#B8AE9F",
            axis="#7D7466",
            border="#3A332B",
            grid="#26211C",
            primary="#E9A84C",
            secondary="#8FB5A9",
            tertiary="#D2724F",
            highlight="#D8C8A6",
        ),
        "whiteboard": ColorScheme(
            name="whiteboard",
            background="#FFFFFF",
            surface="#F5F7FA",
            text="#1E293B",
            muted="#5B6B82",
            axis="#94A3B8",
            border="#D5DCE6",
            grid="#EEF2F7",
            primary="#2563EB",
            secondary="#E2683C",
            tertiary="#0E9F6E",
            highlight="#7C3AED",
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


def relative_luminance(color: str) -> float:
    """WCAG relative luminance of a color (alpha ignored)."""
    r, g, b, _ = ImageColor.getcolor(color, "RGBA") if isinstance(color, str) else tuple(color)

    def channel(value):
        value /= 255
        return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(foreground: str, background: str) -> float:
    """WCAG contrast ratio (1-21). Body text needs >= 4.5, large text >= 3."""
    a, b = relative_luminance(foreground), relative_luminance(background)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def readable_color(background: str, light: str = "#FFFFFF", dark: str = "#111111") -> str:
    """Whichever of ``light``/``dark`` contrasts more with ``background``."""
    return light if contrast_ratio(light, background) >= contrast_ratio(dark, background) else dark
