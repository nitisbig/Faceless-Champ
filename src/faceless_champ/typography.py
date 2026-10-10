"""Shared font loading for text and chart components."""

from pathlib import Path

from PIL import ImageFont

DEFAULT_FONT = str(Path(__file__).parent / "assets" / "DejaVuSans.ttf")


def fit_text(
    text,
    bounds,
    *,
    font_size=64,
    min_font_size=24,
    font=None,
    font_weight=None,
    color="white",
    align="center",
    spacing=8,
):
    """Wrap and shrink text into design-pixel bounds, returning an unowned Text.

    Explicit newline breaks are preserved. Unbreakable words are shrunk rather
    than split. A failed fit raises ValueError instead of clipping text.
    """
    from .components import Text, finite
    from .layout import Bounds

    if not isinstance(bounds, Bounds) or bounds.width <= 0 or bounds.height <= 0:
        raise ValueError("fit_text needs positive Bounds")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("fit_text needs nonempty text")
    maximum = finite(font_size, "font_size", 1)
    minimum = finite(min_font_size, "min_font_size", 1)
    if minimum > maximum:
        raise ValueError("min_font_size must not exceed font_size")
    size = maximum
    while True:

        def make(value, size=size):
            return Text(
                value,
                font=font,
                font_weight=font_weight,
                font_size=size,
                color=color,
                align=align,
                spacing=spacing,
                position=bounds.center,
            )

        lines = []
        for paragraph in text.split("\n"):
            line = ""
            for word in paragraph.split():
                candidate = f"{line} {word}".strip()
                if line and make(candidate).bounds.width > bounds.width:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
        result = make("\n".join(lines))
        measured = result.bounds
        if measured.width <= bounds.width and measured.height <= bounds.height:
            return result
        if size == minimum:
            raise ValueError("Text cannot fit at min_font_size; shorten it or allocate more space")
        size = max(minimum, size - 2)


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
