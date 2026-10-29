"""Typst math typesetting for ``Equation(..., engine="typst")``.

Typst (https://typst.app) is a fast, modern typesetter with excellent math:
matrices, cases, aligned systems, big operators, and its own bundled math
fonts (New Computer Modern Math), with no LaTeX installation. Expressions use
Typst math syntax, which is close to plain text::

    Equation("A = mat(1, 2; 3, 4)", engine="typst")
    Equation("integral_0^oo e^(-x^2) dif x = sqrt(pi) / 2", engine="typst")
    Equation("f(x) = cases(x^2 &x >= 0, -x &x < 0)", engine="typst")
    Equation("hat(f)(xi) = integral f(x) e^(-2 pi i x xi) dif x", engine="typst")

LaTeX -> Typst cheatsheet: ``\\frac{a}{b}`` -> ``a/b`` or ``frac(a, b)``;
``\\sqrt{x}`` -> ``sqrt(x)``; ``\\int_0^\\infty`` -> ``integral_0^oo``;
``\\sum_{n=1}^{N}`` -> ``sum_(n=1)^N``; ``\\alpha`` -> ``alpha``;
``\\begin{bmatrix}1&0\\\\0&1\\end{bmatrix}`` -> ``mat(1, 0; 0, 1)``;
``\\vec{v}`` -> ``arrow(v)``; ``\\mathbb{R}`` -> ``RR``; ``\\cdot`` -> ``dot``;
``\\to`` -> ``->``; multi-letter words need quotes: ``"loss"``.

The compiler is found in this order: the ``typst`` Python package
(``pip install typst``), the ``FC_TYPST`` environment variable (path to a
typst executable), then ``typst`` on PATH. Compiled SVGs are cached on disk
(``FC_CACHE_DIR`` or ``~/.cache/faceless_champ``), so parallel render workers
and resumed renders do not recompile. Rasterizing needs skia-python.
"""

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

from .layout import Group
from .paths import VectorPath

PT_PER_PX = 0.75  # SVG output is in points; 1 design px = 0.75 pt


def cache_dir():
    root = os.environ.get("FC_CACHE_DIR") or Path.home() / ".cache" / "faceless_champ"
    path = Path(root) / "typst"
    path.mkdir(parents=True, exist_ok=True)
    return path


def compiler():
    """Return ("module", module) or ("cli", executable path); raise with install help."""
    try:
        import typst  # type: ignore[import-not-found]

        if hasattr(typst, "compile"):
            return "module", typst
    except ImportError:
        pass
    exe = os.environ.get("FC_TYPST") or shutil.which("typst")
    if exe and Path(exe).exists():
        return "cli", exe
    raise RuntimeError(
        "Typst equations need the Typst compiler: `pip install typst`, or download the typst "
        "binary from https://github.com/typst/typst/releases and put it on PATH (or set FC_TYPST=/path/to/typst)."
    )


def version():
    kind, handle = compiler()
    if kind == "module":
        return f"typst-py {getattr(handle, '__version__', '?')}"
    return subprocess.run([handle, "--version"], capture_output=True, text=True, check=False).stdout.strip()


def document(expression, font_size, color, math_font=None):
    from PIL import ImageColor

    r, g, b, a = ImageColor.getcolor(color, "RGBA")
    lines = [
        "#set page(width: auto, height: auto, margin: 0pt, fill: none)",
        f'#set text(size: {font_size * PT_PER_PX:.4f}pt, fill: rgb("#{r:02x}{g:02x}{b:02x}{a:02x}"))',
    ]
    if math_font:
        escaped = math_font.replace('"', '\\"')
        lines.append(f'#show math.equation: set text(font: "{escaped}")')
    lines.append(f"$ {expression} $")
    return "\n".join(lines) + "\n"


def compile_svg(expression, font_size, color, math_font=None):
    """SVG bytes for the expression; cached on disk by source hash."""
    source = document(expression, font_size, color, math_font)
    kind, handle = compiler()
    digest = hashlib.sha256((kind + "\0" + source).encode()).hexdigest()[:32]
    cached = cache_dir() / f"{digest}.svg"
    if cached.is_file():
        return cached.read_bytes()
    if kind == "module":
        try:
            data = handle.compile(source.encode(), format="svg")
        except Exception as exc:  # noqa: BLE001 - the binding raises its own error types
            raise ValueError(f"Invalid Typst equation {expression!r}: {exc}") from None
        if isinstance(data, list):
            data = data[0]
    else:
        result = subprocess.run(
            [handle, "compile", "--format", "svg", "-", "-"],
            input=source.encode(),
            capture_output=True,
            check=False,
            timeout=60,
        )
        if result.returncode:
            message = result.stderr.decode(errors="replace").strip()
            raise ValueError(f"Invalid Typst equation {expression!r}:\n{message}")
        data = result.stdout
    temporary = cached.with_suffix(f".{os.getpid()}.tmp")
    temporary.write_bytes(data)
    temporary.replace(cached)
    return data


def sprite(c, factor):
    """Tightly cropped RGBA sprite of a typst Equation at ``factor`` pixels per design px."""
    import math

    from ._portable import guard_size
    from .svg import intrinsic_size, rasterize

    data = compile_svg(c.expression, c.font_size, c.color, c.math_font)
    intrinsic = intrinsic_size(data)
    size = max(1, math.ceil(intrinsic[0] * factor)), max(1, math.ceil(intrinsic[1] * factor))
    guard_size(size)
    digest = hashlib.sha256(data).hexdigest()
    image = rasterize(data, digest, intrinsic, size)
    box = image.getbbox()
    return image.crop(box) if box else image


def _parse_transform(text):
    """SVG transform attribute -> affine (a, b, c, d, e, f)."""
    import math
    import re

    from .motion import IDENTITY, multiply

    result = IDENTITY
    for name, args in re.findall(r"(matrix|translate|scale|rotate)\s*\(([^)]*)\)", text or ""):
        v = [float(x) for x in re.split(r"[\s,]+", args.strip()) if x]
        if name == "matrix" and len(v) == 6:
            m = tuple(v)
        elif name == "translate":
            m = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == "scale":
            m = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == "rotate":
            a = math.radians(v[0])
            m = (math.cos(a), math.sin(a), -math.sin(a), math.cos(a), 0, 0)
            if len(v) == 3:
                m = multiply(multiply((1, 0, 0, 1, v[1], v[2]), m), (1, 0, 0, 1, -v[1], -v[2]))
        else:
            continue
        result = multiply(result, m)
    return result


def glyph_paths(expression, font_size=64, color="#FFFFFF", math_font=None):
    """[(PathData, fill, stroke, stroke_width)] in design pixels, document order (left to right)."""
    import xml.etree.ElementTree as ET

    from .motion import multiply
    from .paths import PathData
    from .svg import inline_uses

    root = ET.fromstring(inline_uses(compile_svg(expression, font_size, color, math_font)))
    px = 1 / PT_PER_PX
    pieces = []

    def walk(element, matrix, fill, stroke, width):
        tag = element.tag.rsplit("}", 1)[-1]
        if tag in {"defs", "symbol", "clipPath", "mask"}:
            return
        matrix = multiply(matrix, _parse_transform(element.get("transform")))
        fill = element.get("fill", fill)
        stroke = element.get("stroke", stroke)
        width = float(element.get("stroke-width", width))
        if tag == "path" and element.get("d"):
            path = PathData.from_svg(element.get("d")).affine(*matrix)
            if len(path.commands) > 1:
                pieces.append((path, fill, stroke, width))
        for child in element:
            walk(child, matrix, fill, stroke, width)

    walk(root, (px, 0, 0, px, 0, 0), color, "none", 1.0)
    return pieces


class MathGlyphs(Group):
    """A Typst equation as one VectorPath per symbol, for symbol-level animation.

    ``eq.glyphs`` lists the symbols left to right (fraction bars and matrix
    brackets included). Reveal them one by one, color some before adding,
    or write them by hand with ``outline=True`` (strokes draw, then fill)::

        eq = MathGlyphs("e^(i pi) + 1 = 0", font_size=96, position=(960, 540))
        eq.glyphs[0].fill = "#FFD166"          # color the "e" before scene.add
        scene.add(eq)                          # or scene.reveal(*eq.glyphs, stagger=0.06)
        scene.play(*[Draw(g) for g in eq.glyphs], run_time=2)   # with outline=True

    Needs backend="skia" (glyphs are compound paths) and the Typst compiler.
    """

    def __init__(
        self,
        expression,
        *,
        font_size=64,
        color="#FFFFFF",
        math_font=None,
        position=(960, 540),
        outline=False,
        stroke_width=1.5,
        **kwargs,
    ):
        pieces = glyph_paths(expression, font_size, color, math_font)
        if not pieces:
            raise ValueError(f"Typst produced no glyphs for {expression!r}")
        boxes = [p.bounds for p, *_ in pieces]
        cx = (min(b.left for b in boxes) + max(b.right for b in boxes)) / 2
        cy = (min(b.top for b in boxes) + max(b.bottom for b in boxes)) / 2
        dx, dy = position[0] - cx, position[1] - cy
        glyphs = []
        for path, fill, stroke, width in pieces:
            path = path.transformed(dx=dx, dy=dy)
            filled = fill not in {None, "none"}
            stroked = stroke not in {None, "none"}
            glyphs.append(
                VectorPath(
                    path,
                    fill=fill if filled else None,
                    stroke=(fill if filled else stroke) if (outline or not filled) else None,
                    stroke_width=stroke_width if filled else width / PT_PER_PX,
                    line_cap="round",
                )
                if filled or stroked
                else None
            )
        self.glyphs = [g for g in glyphs if g is not None]
        self.expression = expression
        super().__init__(*self.glyphs, **kwargs)


__all__ = ["MathGlyphs", "compile_svg", "compiler", "glyph_paths", "version"]
