"""Deterministic editor visuals with optional, source-preserving syntax highlighting."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from itertools import pairwise
from pathlib import Path
from types import MappingProxyType

from PIL import Image, ImageColor, ImageDraw

from .animation import Animation, linear
from .components import Component, finite
from .typography import load_font

MONO_FONT = Path(__file__).parent / "assets/DejaVuSansMono.ttf"


@dataclass(frozen=True)
class CodeTheme:
    """Editor colors; syntax keys are Pygments token names without ``Token.``."""

    background: str = "#141B2B"
    chrome: str = "#202A3E"
    foreground: str = "#EDF2FA"
    muted: str = "#91A1B8"
    accent: str = "#65D6E8"
    highlight: str = "#283C56"
    syntax: Mapping[str, str] = field(
        default_factory=lambda: {
            "Keyword": "#C6A0F6",
            "Name.Builtin": "#65D6E8",
            "Name.Function": "#89B4FA",
            "Name.Class": "#F5C879",
            "Literal.String": "#A6DA95",
            "Literal.Number": "#F5A97F",
            "Comment": "#91A1B8",
            "Operator": "#7DC4E4",
        }
    )

    def __post_init__(self):
        colors = dict(self.syntax)
        for color in [
            self.background,
            self.chrome,
            self.foreground,
            self.muted,
            self.accent,
            self.highlight,
            *colors.values(),
        ]:
            ImageColor.getcolor(color, "RGBA")
        object.__setattr__(self, "syntax", MappingProxyType(colors))

    def __deepcopy__(self, memo):
        # All fields, including the copied syntax mapping, are immutable.
        return self

    @classmethod
    def named(cls, name: str) -> CodeTheme:
        if name == "midnight":
            return cls()
        if name == "ocean":
            return cls(background="#062C38", chrome="#104352", accent="#5DE4C7", highlight="#175064")
        if name == "paper":
            return cls(
                background="#F6F8FC",
                chrome="#E4EAF2",
                foreground="#202C40",
                muted="#52647B",
                accent="#006B86",
                highlight="#DAE9FA",
                syntax={
                    "Keyword": "#7437A5",
                    "Name.Builtin": "#006B86",
                    "Name.Function": "#145DAD",
                    "Name.Class": "#885200",
                    "Literal.String": "#287537",
                    "Literal.Number": "#AA4518",
                    "Comment": "#52647B",
                    "Operator": "#006B86",
                },
            )
        raise ValueError("Unknown code theme; use midnight, ocean, or paper")

    def token_color(self, name):
        name = name.removeprefix("Token.")
        while name:
            if name in self.syntax:
                return self.syntax[name]
            name = name.rpartition(".")[0]
        return self.foreground


class CodingChamp(Component):
    """A fixed-size editor. Configure before adding to a scene, like other components.

    ``block_ends`` contains increasing, inclusive 1-based line numbers, including
    the final line. ``highlighted_lines`` uses the same local line numbering.
    Tabs advance to the next multiple of ``tab_size``; source text is never changed.
    """

    def __init__(
        self,
        code: str,
        *,
        language="text",
        theme="midnight",
        width=1200,
        height=720,
        font_size=32,
        font=None,
        filename="",
        chrome=True,
        line_numbers=True,
        highlighted_lines=(),
        reveal_mode="typewriter",
        block_ends=None,
        first_line=1,
        tab_size=4,
        padding=28,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if not isinstance(code, str):
            raise TypeError("code must be a string")
        if not isinstance(language, str):
            raise TypeError("language must be a string")
        if reveal_mode not in {"typewriter", "word", "block"}:
            raise ValueError("reveal_mode must be typewriter, word, or block")
        for value, name in [(first_line, "first_line"), (tab_size, "tab_size")]:
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        self.code, self.language = code, language
        self.theme = CodeTheme.named(theme) if isinstance(theme, str) else theme
        if not isinstance(self.theme, CodeTheme):
            raise TypeError("theme must be a CodeTheme or a named theme")
        self.width, self.height = finite(width, "width", 1), finite(height, "height", 1)
        self.font_size, self.padding = finite(font_size, "font_size", 1), finite(padding, "padding", 0)
        self.font = str(font or MONO_FONT)
        self.filename, self.chrome, self.line_numbers = str(filename), bool(chrome), bool(line_numbers)
        self.reveal_mode, self.first_line, self.tab_size = reveal_mode, first_line, tab_size
        lines = code.splitlines(keepends=True) or [""]
        self.highlighted_lines = tuple(highlighted_lines)
        ends = tuple(block_ends) if block_ends is not None else tuple(range(1, len(lines) + 1))
        for value in (*self.highlighted_lines, *ends):
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= len(lines):
                raise ValueError("Line numbers must be integers within the code excerpt")
        if not ends or ends[-1] != len(lines) or any(a >= b for a, b in pairwise(ends)):
            raise ValueError("block_ends must increase and include the final code line")
        self.block_ends = ends
        offsets, total = [], 0
        for line in lines:
            total += len(line)
            offsets.append(total)
        self._boundaries = (
            tuple(range(1, len(code) + 1))
            if reveal_mode == "typewriter"
            else tuple(m.end() for m in re.finditer(r"\S+\s*", code))
            if reveal_mode == "word"
            else tuple(offsets[end - 1] for end in ends)
        )
        self.tokens = self._tokenize()
        self._rows = self._layout(lines)

    def _tokenize(self):
        if self.language in {"text", "plain", "plaintext"}:
            return ((0, self.code, self.theme.foreground),)
        try:
            from pygments.lexers import get_lexer_by_name
            from pygments.util import ClassNotFound
        except ImportError as exc:
            raise ImportError("Syntax highlighting requires pip install 'faceless-champ[coding]'") from exc
        try:
            lexer = get_lexer_by_name(self.language, stripnl=False, stripall=False, ensurenl=False)
        except ClassNotFound as exc:
            raise ValueError(f"Unknown coding language: {self.language!r}; use 'text' for plain text") from exc
        # The unprocessed API preserves offsets/newlines even for partial code.
        tokens = tuple(
            (i, text, self.theme.token_color(str(kind))) for i, kind, text in lexer.get_tokens_unprocessed(self.code)
        )
        if "".join(text for _, text, _ in tokens) != self.code:
            raise ValueError("Lexer did not preserve the source code")
        return tokens

    def _layout(self, lines):
        font = load_font(self.font, round(self.font_size))
        ascent, descent = font.getmetrics()
        self.line_height = max(self.font_size * 1.45, ascent + descent + 4)
        self.header_height = max(42, self.font_size * 1.6) if self.chrome else 0
        self.gutter = font.getlength(str(self.first_line + len(lines) - 1)) + 24 if self.line_numbers else 0
        self.code_x = self.padding + self.gutter
        self.code_y = self.header_height + self.padding
        if self.code_y + len(lines) * self.line_height > self.height - self.padding:
            raise ValueError("Code exceeds editor height; show a shorter excerpt, enlarge height, or reduce font_size")
        if self.chrome and font.getlength(self.filename) + 110 > self.width - self.padding:
            raise ValueError("Filename exceeds editor width; shorten it or enlarge width")
        colors = [self.theme.foreground] * len(self.code)
        for start, text, color in self.tokens:
            colors[start : start + len(text)] = [color] * len(text)
        rows, offset = [], 0
        space = font.getlength(" ")
        for line in lines:
            glyphs, x = [], self.code_x
            for char in line:
                if char not in {"\n", "\r"}:
                    advance = (
                        (
                            (math.floor((x - self.code_x) / (space * self.tab_size)) + 1) * space * self.tab_size
                            - (x - self.code_x)
                        )
                        if char == "\t"
                        else font.getlength(char)
                    )
                    glyphs.append((offset, x, advance, char, colors[offset]))
                    x += advance
                offset += 1
            if x > self.width - self.padding:
                raise ValueError(
                    "Code exceeds editor width; show a shorter excerpt, enlarge width, or reduce font_size"
                )
            rows.append(tuple(glyphs))
        return tuple(rows)

    def visible_count(self, progress):
        p = finite(progress, "reveal", 0)
        if p > 1:
            raise ValueError("reveal must be <= 1")
        if p == 1:
            return len(self.code)
        count = math.floor(p * len(self._boundaries) + 1e-9)
        return self._boundaries[count - 1] if count else 0


def CodeReveal(panel: CodingChamp, start=0, end=1) -> Animation:
    """Reveal source with explicit normalized endpoints and linear timing."""
    if not isinstance(panel, CodingChamp):
        raise TypeError("CodeReveal requires CodingChamp")
    start, end = finite(start, "start", 0), finite(end, "end", 0)
    if not 0 <= start <= end <= 1:
        raise ValueError("CodeReveal requires 0 <= start <= end <= 1")
    return Animation(panel, {"reveal": end}, {"reveal": start}, rate_func=linear)


def draw_code(panel, state, factor, renderer):
    """Cache two full layers per editor, never intermediate reveal frames."""
    key = (panel, factor)
    cached = renderer._code_sprites.get(key)
    if cached is not None:
        renderer._code_sprites.move_to_end(key)
        base, ink = cached
    else:
        size = (max(1, round(panel.width * factor)), max(1, round(panel.height * factor)))
        base = Image.new("RGBA", size)
        ink = Image.new("RGBA", size)
        d, text_draw = ImageDraw.Draw(base), ImageDraw.Draw(ink)
        t = panel.theme
        d.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=round(18 * factor), fill=t.background)
        font = load_font(panel.font, max(1, round(panel.font_size * factor)))
        small = load_font(panel.font, max(1, round(panel.font_size * 0.65 * factor)))
        if panel.chrome:
            d.rounded_rectangle(
                (0, 0, size[0] - 1, round(panel.header_height * factor)), radius=round(18 * factor), fill=t.chrome
            )
            for i, color in enumerate(("#F07078", "#E9BF6A", "#75C991")):
                x, y, r = (24 + i * 22) * factor, panel.header_height * factor / 2, 5 * factor
                d.ellipse((x - r, y - r, x + r, y + r), fill=color)
            d.text(
                (100 * factor, panel.header_height * factor / 2), panel.filename, font=small, fill=t.muted, anchor="lm"
            )
        for row, glyphs in enumerate(panel._rows):
            y = panel.code_y + row * panel.line_height
            if row + 1 in panel.highlighted_lines:
                d.rectangle(
                    (
                        panel.padding * factor / 2,
                        y * factor,
                        (panel.width - panel.padding / 2) * factor,
                        (y + panel.line_height) * factor,
                    ),
                    fill=t.highlight,
                )
            if panel.line_numbers:
                d.text(
                    ((panel.code_x - 16) * factor, y * factor),
                    str(panel.first_line + row),
                    font=font,
                    fill=t.muted,
                    anchor="ra",
                )
            for _, x, _, char, color in glyphs:
                if char not in {" ", "\t"}:
                    text_draw.text((x * factor, y * factor), char, font=font, fill=color, anchor="la")
        cost = size[0] * size[1] * 8
        if cost <= renderer._code_cache_limit:
            while renderer._code_sprites and renderer._code_cache_bytes + cost > renderer._code_cache_limit:
                _, (old, _) = renderer._code_sprites.popitem(last=False)
                renderer._code_cache_bytes -= old.width * old.height * 8
            renderer._code_sprites[key] = (base, ink)
            renderer._code_cache_bytes += cost
    result = base.copy()
    count = panel.visible_count(state["reveal"])
    if count == len(panel.code):
        result.alpha_composite(ink)
        return result
    for row, glyphs in enumerate(panel._rows):
        visible = [g for g in glyphs if g[0] < count]
        if visible:
            last = visible[-1]
            y = (panel.code_y + row * panel.line_height) * factor
            box = (
                0,
                max(0, math.floor(y)),
                min(ink.width, math.ceil((last[1] + last[2]) * factor)),
                min(ink.height, math.ceil(y + panel.line_height * factor)),
            )
            result.alpha_composite(ink.crop(box), (box[0], box[1]))
    return result
