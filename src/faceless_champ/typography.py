"""Shared font loading for text and chart components."""

from pathlib import Path

from PIL import ImageFont

DEFAULT_FONT = str(Path(__file__).parent / "assets" / "DejaVuSans.ttf")


def load_font(path, size, weight=None):
    path = str(path) if path else DEFAULT_FONT
    try:
        font = ImageFont.truetype(path, size)
    except OSError as exc:
        raise ValueError(f"Cannot load font: {path}") from exc
    if weight is not None:
        try:
            axes = font.get_variation_axes()
        except OSError as exc:
            raise ValueError("font_weight requires a variable font with a Weight axis") from exc
        axis = next((i for i, a in enumerate(axes) if a["name"].lower() == b"weight"), None)
        if axis is None or not axes[axis]["minimum"] <= weight <= axes[axis]["maximum"]:
            raise ValueError("font_weight must fit the variable font's Weight axis")
        values = [a["default"] for a in axes]
        values[axis] = weight
        font.set_variation_by_axes(values)
    return font
