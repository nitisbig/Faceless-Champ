"""Fonts, type roles and text fitting shared by text, captions and charts.

Three ideas keep on-screen text premium without per-scene tuning:

* **Named fonts.** ``font="sans" | "display" | "serif" | "mono"`` (or a family
  name such as ``"space-grotesk"``) resolves to a bundled OFL font. Paths still work.
* **Type roles.** ``Text("Revenue doubled", role="title")`` takes size, weight,
  line height and tracking from a :class:`TypeScale`. Explicit arguments win.
* **Text budgets.** :func:`fit_text` shrinks at most one step and raises
  :class:`TextBudgetError` when copy is too long, instead of silently producing
  tiny text. Split the beat or move the words into narration.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, fields, replace
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType

from PIL import ImageFont

ASSETS = Path(__file__).parent / "assets"

# ---------------------------------------------------------------------------
# Font registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FontFamily:
    """A bundled font file with sensible defaults for video typography."""

    name: str
    file: str
    default_weight: float | None = None
    weight_range: tuple[float, float] | None = None
    description: str = ""

    @property
    def path(self) -> str:
        return str(ASSETS / self.file)


FONTS = MappingProxyType(
    {
        family.name: family
        for family in (
            FontFamily(
                "dm-sans",
                "DMSans[opsz,wght].ttf",
                400,
                (100, 1000),
                "Neutral geometric sans; default for body, UI and headings.",
            ),
            FontFamily(
                "space-grotesk",
                "SpaceGrotesk[wght].ttf",
                500,
                (300, 700),
                "Technical display sans with character; tech/product titles.",
            ),
            FontFamily(
                "cormorant",
                "CormorantGaramond[wght].ttf",
                500,
                (300, 700),
                "High-contrast editorial serif; history, culture, quotes.",
            ),
            FontFamily(
                "cormorant-italic",
                "CormorantGaramond-Italic[wght].ttf",
                500,
                (300, 700),
                "Italic companion of cormorant for emphasis and quotes.",
            ),
            FontFamily(
                "dejavu-sans", "DejaVuSans.ttf", None, None, "Wide-coverage fallback (symbols, Greek, Cyrillic)."
            ),
            FontFamily("dejavu-mono", "DejaVuSansMono.ttf", None, None, "Monospace for code and numbers in tables."),
        )
    }
)

FONT_ALIASES = MappingProxyType(
    {
        "sans": "dm-sans",
        "body": "dm-sans",
        "display": "space-grotesk",
        "serif": "cormorant",
        "serif-italic": "cormorant-italic",
        "mono": "dejavu-mono",
        "fallback": "dejavu-sans",
    }
)

DEFAULT_FONT = FONTS["dm-sans"].path
FALLBACK_FONT = FONTS["dejavu-sans"].path
CLEAN_FLOW_FONT = FONTS["dm-sans"].path


def _family_for_name(name: str) -> FontFamily | None:
    key = FONT_ALIASES.get(name.lower(), name.lower())
    return FONTS.get(key)


def font_path(font: str | Path | None) -> str:
    """Resolve a font name, alias or file path to a font file path.

    ``None`` gives the default sans (DM Sans). Names: ``sans``, ``display``,
    ``serif``, ``serif-italic``, ``mono``, ``fallback`` or any key of ``FONTS``.
    """
    if font is None:
        return DEFAULT_FONT
    text = str(font)
    family = _family_for_name(text) if "/" not in text and "\\" not in text and "." not in text else None
    if family is not None:
        return family.path
    if Path(text).suffix.lower() in {".ttf", ".otf", ".ttc", ".otc", ".woff", ".woff2"} or Path(text).exists():
        return text
    names = ", ".join([*FONT_ALIASES, *FONTS])
    raise ValueError(f"Unknown font {text!r}; use a font file path or one of: {names}")


@lru_cache(maxsize=1)
def _coverage():
    try:
        data = json.loads((ASSETS / "font-coverage.json").read_text())
    except (OSError, ValueError):
        return {}
    return {name: tuple(tuple(r) for r in ranges) for name, ranges in data.items()}


def _covers(ranges, codepoint):
    lo, hi = 0, len(ranges) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        start, end = ranges[mid]
        if codepoint < start:
            hi = mid - 1
        elif codepoint > end:
            lo = mid + 1
        else:
            return True
    return False


def missing_glyphs(path: str, text: str) -> str:
    """Characters of ``text`` a bundled font cannot draw ('' if unknown/complete)."""
    ranges = _coverage().get(Path(path).name)
    if not ranges or Path(path).resolve().parent != ASSETS.resolve():
        return ""
    return "".join(sorted({ch for ch in text if not ch.isspace() and ord(ch) >= 32 and not _covers(ranges, ord(ch))}))


def resolve_font(font, text: str = "", weight=None):
    """Return ``(path, weight)`` for a component's font request and text.

    Named families supply their default weight when ``weight`` is None. When a
    bundled font lacks glyphs used by ``text`` (arrows, Greek, check marks...),
    the wide-coverage DejaVu Sans fallback is used and the variable weight is
    dropped, because DejaVu is not a variable font.
    """
    path = font_path(font)
    # Only named fonts get an implicit weight; paths keep the file's default.
    family = _family_for_name(str(font)) if font is not None else None
    if weight is None and family is not None and family.default_weight is not None:
        weight = family.default_weight
    missing = missing_glyphs(path, text) if text else ""
    if missing:
        _warn_fallback(Path(path).name, missing)
        return FALLBACK_FONT, None
    return path, weight


@lru_cache(maxsize=256)
def _warn_fallback(name, missing):
    import warnings

    warnings.warn(
        f"{name} has no glyphs for {missing!r}; this text uses the DejaVu Sans fallback without variable weight. "
        "Pass font='fallback' explicitly or avoid these symbols to keep the design font.",
        UserWarning,
        stacklevel=4,
    )


# ---------------------------------------------------------------------------
# Type roles
# ---------------------------------------------------------------------------


class TextBudgetError(ValueError):
    """Copy is too long for its role or box; shorten, split, or narrate it.

    ``kind`` is "words" or "lines" (role budget exceeded) or "fit" (the box is
    too small even at the minimum size).
    """

    def __init__(self, message, kind="fit"):
        super().__init__(message)
        self.kind = kind


@dataclass(frozen=True)
class TextStyle:
    """Typographic settings for one role, in design pixels at a 1080p reference.

    ``line_height`` is a multiple of the font size. ``tracking`` is letter
    spacing in em (``-0.02`` tightens large display type). ``max_words`` and
    ``max_lines`` are budgets enforced by :func:`fit_text`.
    """

    font_size: float
    font_weight: float | None = None
    font: str | None = None
    line_height: float = 1.25
    tracking: float = 0.0
    max_words: int | None = None
    max_lines: int | None = None

    def __post_init__(self):
        if not math.isfinite(self.font_size) or self.font_size <= 0:
            raise ValueError("TextStyle.font_size must be positive")
        if not math.isfinite(self.line_height) or self.line_height <= 0:
            raise ValueError("TextStyle.line_height must be positive")
        if not math.isfinite(self.tracking) or abs(self.tracking) > 0.5:
            raise ValueError("TextStyle.tracking must be an em value between -0.5 and 0.5")
        for name in ("max_words", "max_lines"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 1):
                raise ValueError(f"TextStyle.{name} must be a positive integer or None")


ROLES = ("display", "title", "heading", "body", "label", "caption")


@dataclass(frozen=True)
class TypeScale:
    """Six text roles. Sizes target 1080p; use ``for_canvas`` for other sizes.

    Pick a font pairing with ``TypeScale.named("modern" | "tech" | "editorial")``
    or ``scale.with_fonts(heading="serif", body="sans")``.
    """

    display: TextStyle = TextStyle(120, 700, None, 1.0, -0.015, 6, 2)
    title: TextStyle = TextStyle(84, 700, None, 1.06, -0.01, 8, 2)
    heading: TextStyle = TextStyle(60, 600, None, 1.12, -0.01, 10, 2)
    body: TextStyle = TextStyle(42, 400, None, 1.35, 0.0, 22, 3)
    label: TextStyle = TextStyle(32, 500, None, 1.2, 0.01, 5, 1)
    caption: TextStyle = TextStyle(32, 400, None, 1.3, 0.0, 14, 2)

    def style(self, role: str) -> TextStyle:
        if role not in ROLES:
            raise ValueError(f"Unknown text role {role!r}; choose {', '.join(ROLES)}")
        return getattr(self, role)

    def scaled(self, factor: float) -> TypeScale:
        """Multiply every size, e.g. 2.0 for 4K design pixels."""
        if not math.isfinite(factor) or factor <= 0:
            raise ValueError("scale factor must be positive")
        return replace(self, **{r: replace(self.style(r), font_size=self.style(r).font_size * factor) for r in ROLES})

    def for_canvas(self, canvas, reference: float = 1080) -> TypeScale:
        """Scale sizes by the canvas short side relative to 1080 px."""
        return self.scaled(min(canvas.width, canvas.height) / reference)

    def with_fonts(self, *, heading=None, body=None) -> TypeScale:
        """Use ``heading`` for display/title/heading and ``body`` for the rest."""
        changes = {}
        for role in ROLES:
            font = heading if role in {"display", "title", "heading"} else body
            if font is not None:
                font_path(font)  # validate early
                style = self.style(role)
                weight = style.font_weight
                family = _family_for_name(str(font))
                if family is not None and family.weight_range is not None and weight is not None:
                    weight = min(max(weight, family.weight_range[0]), family.weight_range[1])
                elif family is not None and family.weight_range is None:
                    weight = None
                changes[role] = replace(style, font=str(font), font_weight=weight)
        return replace(self, **changes)

    @classmethod
    def named(cls, name: str) -> TypeScale:
        try:
            return TYPE_PAIRINGS[name]
        except KeyError:
            raise ValueError(f"Unknown type pairing {name!r}; choose {', '.join(TYPE_PAIRINGS)}") from None


TYPE_SCALE = TypeScale()
TYPE_PAIRINGS = MappingProxyType(
    {
        "modern": TYPE_SCALE.with_fonts(heading="sans", body="sans"),
        "tech": TYPE_SCALE.with_fonts(heading="display", body="sans"),
        "editorial": TYPE_SCALE.with_fonts(heading="serif", body="sans"),
    }
)


def role_style(role: str | None, type_scale: TypeScale | None = None) -> TextStyle | None:
    """Style for a role from ``type_scale``, the active Theme, or TYPE_SCALE."""
    if role is None:
        return None
    if type_scale is None:
        from .theme import active_theme

        theme = active_theme()
        type_scale = theme.type_scale if theme is not None else TYPE_SCALE
    return type_scale.style(role)


# ---------------------------------------------------------------------------
# Font loading and line metrics
# ---------------------------------------------------------------------------


def optical_size(design_font_size: float) -> float:
    """Optical-size axis value for a design-pixel font size (display cuts for big type)."""
    return design_font_size * 0.5


def axis_name(axis) -> str:
    """Normalized Pillow variation-axis name ("weight", "optical size", ...)."""
    name = axis["name"]
    return (name.decode("latin-1") if isinstance(name, bytes) else str(name)).lower()


OPSZ_NAMES = frozenset({"optical size", "optical_size", "opsz"})


def load_font(path, size, weight=None, *, opsz=None):
    """Load a font at a pixel size, applying variable weight and optical size.

    ``opsz`` defaults from ``size``; pass the *design* size when rendering at a
    supersampled raster size so 1080p and 4K exports pick the same optical cut.
    """
    path = str(path) if path else DEFAULT_FONT
    try:
        font = ImageFont.truetype(path, size)
    except OSError as exc:
        raise ValueError(f"Cannot load font: {path}") from exc
    try:
        axes = font.get_variation_axes()
    except OSError:
        axes = None
    if weight is not None and axes is None:
        raise ValueError("font_weight requires a variable font with a Weight axis")
    if axes:
        values = [a["default"] for a in axes]
        changed = False
        names = [axis_name(a) for a in axes]
        if weight is not None:
            axis = next((i for i, n in enumerate(names) if n == "weight"), None)
            if axis is None or not axes[axis]["minimum"] <= weight <= axes[axis]["maximum"]:
                raise ValueError("font_weight must fit the variable font's Weight axis")
            values[axis], changed = weight, True
        axis = next((i for i, n in enumerate(names) if n in OPSZ_NAMES), None)
        if axis is not None:
            value = optical_size(size if opsz is None else opsz)
            values[axis] = min(max(value, axes[axis]["minimum"]), axes[axis]["maximum"])
            changed = True
        if changed:
            font.set_variation_by_axes(values)
    return font


def pillow_line_spacing(font, font_px: float, line_height: float | None, spacing_px: float) -> int:
    """Extra pixels Pillow's multiline layout needs between lines.

    Pillow advances lines by ``bbox("A").bottom + spacing``. With a
    ``line_height`` ratio the advance becomes ``line_height * font_px``.
    """
    if line_height is None:
        return round(spacing_px)
    natural = font.getbbox("A")[3]
    return round(line_height * font_px - natural)


def tracking_px(tracking: float, font_px: float) -> float:
    return tracking * font_px


def _line_width(font, line: str, track: float) -> float:
    return font.getlength(line) + track * max(0, len(line) - 1)


def tracked_layout(draw, font, text: str, *, spacing: int, align: str, track: float):
    """Layout for tracked multiline text: ``(bbox, [(x, y, line), ...])``.

    Positions use anchor "la" like Pillow's multiline text. Kerning is kept by
    positioning each glyph at ``getlength(prefix) + index * track``.
    """
    lines = text.split("\n")
    advance = font.getbbox("A")[3] + spacing
    widths = [_line_width(font, line, track) for line in lines]
    widest = max(widths, default=0)
    placed, box = [], None
    for i, (line, width) in enumerate(zip(lines, widths)):
        x = 0 if align == "left" else widest - width if align == "right" else (widest - width) / 2
        y = i * advance
        placed.append((x, y, line))
        left, top, _, bottom = draw.textbbox((x, y), line or " ", font=font, anchor="la")
        line_box = (left, top, x + max(width, 1), bottom)
        box = (
            line_box
            if box is None
            else (
                min(box[0], line_box[0]),
                min(box[1], line_box[1]),
                max(box[2], line_box[2]),
                max(box[3], line_box[3]),
            )
        )
    return box or (0, 0, 1, 1), placed


def draw_tracked(draw, origin, placed, font, *, fill, track: float, limit: int | None = None):
    """Draw glyph-by-glyph; ``limit`` reveals only the first N characters."""
    ox, oy = origin
    remaining = math.inf if limit is None else limit
    for x, y, line in placed:
        if remaining <= 0:
            return
        for i, ch in enumerate(line):
            if remaining <= 0:
                return
            if not ch.isspace():
                draw.text(
                    (ox + x + font.getlength(line[:i]) + i * track, oy + y), ch, font=font, fill=fill, anchor="la"
                )
            remaining -= 1
        remaining -= 1  # the newline


# ---------------------------------------------------------------------------
# Text fitting
# ---------------------------------------------------------------------------


def _wrap(words, width, measure):
    lines, line = [], []
    for word in words:
        candidate = " ".join([*line, word])
        if line and measure(candidate) > width:
            lines.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    lines.append(" ".join(line))
    return lines


def _wrap_paragraphs(text, width, measure, balance):
    result = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            result.append("")
            continue
        lines = _wrap(words, width, measure)
        if balance and len(lines) > 1:
            # Narrowest width that keeps the same line count gives even lines
            # and avoids a lonely last word.
            lo, hi = max(measure(w) for w in words), width
            for _ in range(14):
                mid = (lo + hi) / 2
                if len(_wrap(words, mid, measure)) <= len(lines):
                    hi = mid
                else:
                    lo = mid
            lines = _wrap(words, hi, measure)
        result.extend(lines)
    return result


@lru_cache(maxsize=64)
def _metric_font(path, size, weight, opsz):
    return load_font(path, size, weight, opsz=opsz)


def fit_text(
    text,
    bounds,
    *,
    role=None,
    type_scale=None,
    font_size=None,
    min_font_size=None,
    font=None,
    font_weight=None,
    color=None,
    align="center",
    spacing=8,
    line_height=None,
    tracking=None,
    text_engine="pillow",
    max_words=None,
    max_lines=None,
    budget=True,
    balance=True,
):
    """Wrap text into design-pixel bounds and return an unowned :class:`Text`.

    * ``role`` ("title", "body", ...) supplies size, weight, font, line height,
      tracking and word/line budgets; explicit arguments override it.
    * Without ``min_font_size`` the text may shrink by one step (to 85%) only.
      Pass ``min_font_size`` explicitly to allow more shrinking.
    * Budgets: more words than ``max_words`` or more lines than ``max_lines``
      raise :class:`TextBudgetError`. ``budget=False`` disables role budgets.
    * ``balance`` evens line lengths. Explicit newlines are preserved.
    """
    from .components import Text, finite
    from .layout import Bounds

    if not isinstance(bounds, Bounds) or bounds.width <= 0 or bounds.height <= 0:
        raise ValueError("fit_text needs positive Bounds")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("fit_text needs nonempty text")
    style = role_style(role, type_scale)
    if style is not None:
        font_size = style.font_size if font_size is None else font_size
        font = style.font if font is None else font
        font_weight = style.font_weight if font_weight is None else font_weight
        line_height = style.line_height if line_height is None else line_height
        tracking = style.tracking if tracking is None else tracking
        if budget:
            max_words = style.max_words if max_words is None else max_words
            max_lines = style.max_lines if max_lines is None else max_lines
    maximum = finite(64 if font_size is None else font_size, "font_size", 1)
    minimum = finite(maximum * 0.85 if min_font_size is None else min_font_size, "min_font_size", 1)
    if minimum > maximum:
        raise ValueError("min_font_size must not exceed font_size")
    finite(spacing, "spacing", 0)
    tracking = 0.0 if tracking is None else tracking
    words = len(text.split())
    if max_words is not None and words > max_words:
        raise TextBudgetError(
            f"{words} words exceed the {role or 'text'} budget of {max_words}; "
            "shorten the copy, split it across beats, or leave it to narration",
            "words",
        )

    path, weight = resolve_font(font, text, font_weight)

    def make(value, size):
        return Text(
            value,
            font=path,
            font_weight=weight,
            font_size=size,
            color=color,
            align=align,
            spacing=spacing,
            line_height=line_height,
            tracking=tracking,
            text_engine=text_engine,
            position=bounds.center,
        )

    size, lines = maximum, []
    while True:
        metric = _metric_font(path, max(1, round(size)), weight, size)
        track = tracking * size
        widths = {}

        def measure(value, metric=metric, track=track, widths=widths):
            if value not in widths:
                widths[value] = _line_width(metric, value, track)
            return widths[value]

        # Leave the Text sprite padding (4px) inside the box.
        lines = _wrap_paragraphs(text, bounds.width - 6, measure, balance)
        if max_lines is None or len(lines) <= max_lines:
            result = make("\n".join(lines), size)
            measured = result.bounds
            if measured.width <= bounds.width and measured.height <= bounds.height:
                return result
        if size <= minimum:
            break
        size = max(minimum, size - 2)
    if max_lines is not None and len(lines) > max_lines:
        raise TextBudgetError(
            f"Text needs {len(lines)} lines at {size:g}px; the {role or 'text'} budget is {max_lines}. "
            "Shorten the copy or give it a wider box",
            "lines",
        )
    raise TextBudgetError(
        f"Text cannot fit at min_font_size {minimum:g}px; shorten it, split the beat, or allocate more space",
        "fit",
    )


def text_style_fields():
    """Names a TextStyle sets on Text (for documentation and validation)."""
    return tuple(f.name for f in fields(TextStyle) if f.name not in {"max_words", "max_lines"})
