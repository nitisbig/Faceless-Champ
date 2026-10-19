"""Shaped paragraphs with explicit fonts and renderer-owned native lifetimes."""

import math
import unicodedata
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path

from ..components import Number
from ..motion import rgba
from ..typography import DEFAULT_FONT, load_font
from ._native import load_skia


class TextSession:
    def __init__(self):
        self.skia = load_skia()
        self.layouts = OrderedDict()
        self.fonts = {}
        self._reset_fonts()

    def _reset_fonts(self):
        s = self.skia
        self.provider = s.textlayout.TypefaceFontProvider()
        self.collection = s.textlayout.FontCollection()
        self.collection.setDefaultFontManager(self.provider)
        self.unicode = s.Unicodes.ICU.Make()

    def _font(self, c):
        path = str(Path(c.font or DEFAULT_FONT).resolve())
        key = path, c.font_weight
        if key not in self.fonts:
            if len(self.fonts) >= 64:
                self.close()
                self._reset_fonts()
            # Keep the same variable-weight validation as legacy typography.
            load_font(path, max(1, round(c.font_size)), c.font_weight)
            s = self.skia
            tf = s.Typeface.MakeFromFile(path)
            if tf is None:
                raise ValueError(f"Cannot load native font: {path}")
            if c.font_weight is not None:
                coordinates = s.FontArguments.VariationPosition.Coordinates()
                coordinates.append(
                    s.FontArguments.VariationPosition.Coordinate(int.from_bytes(b"wght", "big"), c.font_weight)
                )
                args = s.FontArguments().setVariationDesignPosition(s.FontArguments.VariationPosition(coordinates))
                tf = tf.makeClone(args)
                if tf is None:
                    raise ValueError(f"Cannot instantiate variable font: {path}")
            alias = f"FacelessFont{len(self.fonts)}"
            self.provider.registerTypeface(tf, alias)
            self.fonts[key] = tf, alias
        return self.fonts[key]

    def layout(self, c, state):
        full = c.format(state["value"]) if isinstance(c, Number) else c.text
        if len(full) > 65536:
            raise ValueError("Native text exceeds 65536 characters")
        color = rgba(state.get("color", c.color))
        key = (
            full,
            c.font,
            c.font_weight,
            c.font_size,
            c.spacing,
            c.align,
            getattr(c, "width", None),
            state["reveal"],
            color,
        )
        cached = self.layouts.get(key)
        if cached is not None:
            self.layouts.move_to_end(key)
            return cached
        tf, alias = self._font(c)
        chars = [ch for ch in full if not ch.isspace() and unicodedata.category(ch) not in {"Cf", "Cc"}]
        if any(g == 0 for g in tf.unicharsToGlyphs([ord(ch) for ch in chars])):
            raise ValueError(f"Native font {c.font or DEFAULT_FONT} lacks a requested glyph; supply an explicit font")
        s = self.skia

        def paragraph(value):
            ts = s.textlayout.TextStyle()
            ts.setFontFamilies([alias])
            ts.setFontSize(c.font_size)
            ts.setColor(s.ColorSetARGB(color[3], *color[:3]))
            ps = s.textlayout.ParagraphStyle()
            ps.setTextStyle(ts)
            b = s.textlayout.ParagraphBuilder.make(ps, self.collection, self.unicode)
            b.addText(value or " ")
            p = b.Build()
            p.layout(max(1, p.MaxIntrinsicWidth) if p.MaxIntrinsicWidth else 1_000_000)
            # Layout once to establish intrinsic width, then reserve an unwrapped line.
            p.layout(max(1, math.ceil(p.MaxIntrinsicWidth) + 2))
            return p

        full_lines = full.split("\n")
        measured = [paragraph(line) for line in full_lines]
        width = max((p.LongestLine if line else 0 for p, line in zip(measured, full_lines)), default=0)
        fixed = c.width if isinstance(c, Number) else None
        if fixed is not None:
            if width > fixed + 1e-5:
                raise ValueError("Number text exceeds its fixed width")
            width = fixed
        visible = full[: math.floor(len(full) * state["reveal"] + 1e-9)].split("\n")
        lines, y = [], 2
        for i, (line, base) in enumerate(zip(full_lines, measured)):
            shown = visible[i] if i < len(visible) else ""
            p = paragraph(shown) if shown != line else base
            advance = p.LongestLine if shown else 0
            x = 0 if c.align == "left" else width - advance if c.align == "right" else (width - advance) / 2
            if shown:
                lines.append((p, 2 + x, y))
            y += math.ceil(base.Height) + c.spacing
        result = ((max(1, math.ceil(width)) + 4, max(1, math.ceil(y - c.spacing + 2))), tuple(lines))
        self.layouts[key] = result
        while len(self.layouts) > 128:
            self.layouts.popitem(last=False)
        return result

    def paint(self, canvas, c, state):
        size, lines = self.layout(c, state)
        for paragraph, x, y in lines:
            paragraph.paint(canvas, x, y)
        return size

    def close(self):
        self.layouts.clear()
        self.fonts.clear()
        self.collection = self.provider = self.unicode = None


@lru_cache(maxsize=128)
def _measured(text, font, stamp, size, weight, spacing, align, width):
    from ..components import Text

    session = TextSession()
    try:
        c = Text(text, font=font, font_size=size, font_weight=weight, spacing=spacing, align=align, text_engine="skia")
        measured = session.layout(c, c.state())[0]
        return (max(measured[0], math.ceil(width) + 4), measured[1]) if width is not None else measured
    finally:
        session.close()


def text_size(c, state):
    path = Path(c.font or DEFAULT_FONT).resolve()
    stamp = path.stat().st_mtime_ns, path.stat().st_size
    text = c.format(state["value"]) if isinstance(c, Number) else c.text
    return _measured(text, str(path), stamp, c.font_size, c.font_weight, c.spacing, c.align, getattr(c, "width", None))
