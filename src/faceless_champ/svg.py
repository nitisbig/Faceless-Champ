"""SVG import: render vector artwork (icons, logos, diagrams exported from
Figma/Illustrator/Inkscape, Typst output) crisply at any resolution via Skia SVGDOM.

``SVG("logo.svg", width=400)`` keeps the artwork's aspect ratio when only one
side is given. ``color="#FFD166"`` recolors every visible pixel (monochrome
icons). The SVG is re-rasterized at output density, so 4K stays sharp.
Requires skia-python (faceless-champ[skia]); works with every backend.
"""

import hashlib
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any

from .components import Component, finite

_DOMS = OrderedDict()
_SPRITES = OrderedDict()
_LENGTH = re.compile(r"^\s*([0-9.eE+-]+)\s*(px|pt|mm|cm|in)?\s*$")
_UNITS = {None: 1, "px": 1, "pt": 4 / 3, "mm": 96 / 25.4, "cm": 96 / 2.54, "in": 96}


def _length(value):
    if value is None:
        return None
    match = _LENGTH.match(value)
    if not match:
        return None
    return float(match.group(1)) * _UNITS[match.group(2)]


def intrinsic_size(data: bytes):
    """(width, height) in CSS pixels from the root width/height or viewBox."""
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid SVG: {exc}") from None
    if not root.tag.endswith("svg"):
        raise ValueError("SVG root element must be <svg>")
    width, height = _length(root.get("width")), _length(root.get("height"))
    box = root.get("viewBox")
    if box:
        values = [float(v) for v in re.split(r"[\s,]+", box.strip())]
        if len(values) == 4 and values[2] > 0 and values[3] > 0:
            if width is None and height is None:
                return values[2], values[3]
            if width is None:
                return height * values[2] / values[3], height
            if height is None:
                return width, width * values[3] / values[2]
    if width and height:
        return width, height
    raise ValueError("SVG needs width/height or a viewBox")


_SVG_NS = "http://www.w3.org/2000/svg"
_XLINK = "{http://www.w3.org/1999/xlink}href"


def inline_uses(data: bytes) -> bytes:
    """Expand <use href="#id"> references (Skia's SVGDOM skips <symbol> instances).

    Typst, Figma and icon sprite sheets emit glyphs/icons as <symbol> + <use>.
    """
    import copy
    import xml.etree.ElementTree as ET

    if b"<use" not in data:
        return data
    ET.register_namespace("", _SVG_NS)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    root = ET.fromstring(data)
    ids = {el.get("id"): el for el in root.iter() if el.get("id")}
    parents = {child: parent for parent in root.iter() for child in parent}
    for _ in range(8):  # nested uses
        uses = [el for el in root.iter() if el.tag in {f"{{{_SVG_NS}}}use", "use"}]
        if not uses:
            break
        for use in uses:
            href = use.get(_XLINK) or use.get("href") or ""
            target = ids.get(href.lstrip("#"))
            parent = parents.get(use)
            if target is None or parent is None:
                if parent is not None:
                    parent.remove(use)
                continue
            group = ET.Element(f"{{{_SVG_NS}}}g")
            transform = use.get("transform", "")
            x, y = use.get("x", "0"), use.get("y", "0")
            if x not in {"0", ""} or y not in {"0", ""}:
                transform = f"{transform} translate({x} {y})".strip()
            if transform:
                group.set("transform", transform)
            for key, value in use.attrib.items():
                if key not in {"x", "y", "width", "height", "transform", "href", _XLINK, "id"}:
                    group.set(key, value)
            is_symbol = target.tag in {f"{{{_SVG_NS}}}symbol", "symbol"}
            for child in list(target) if is_symbol else [target]:
                clone = copy.deepcopy(child)
                if not is_symbol:
                    clone.attrib.pop("id", None)
                group.append(clone)
            index = list(parent).index(use)
            parent.remove(use)
            parent.insert(index, group)
            for child in group.iter():
                for grandchild in child:
                    parents[grandchild] = child
            parents.update({child: group for child in group})
    return ET.tostring(root)


def _dom(data, digest):
    from ._skia_fx import skia

    s = skia()
    dom = _DOMS.get(digest)
    if dom is None:
        markup = inline_uses(data)  # keep a reference: MemoryStream does not copy its bytes
        stream = s.MemoryStream(markup)
        dom = s.SVGDOM.MakeFromStream(stream)
        del stream, markup
        if dom is None:
            raise ValueError("Skia could not parse this SVG")
        _DOMS[digest] = dom
        while len(_DOMS) > 64:
            _DOMS.popitem(last=False)
    return dom


def rasterize(data, digest, intrinsic, size, color=None):
    """RGBA PIL image of the SVG scaled to ``size`` pixels."""
    from PIL import Image as PILImage

    from ._skia_fx import skia, surface, to_pillow

    key = digest, size, color
    cached = _SPRITES.get(key)
    if cached is not None:
        _SPRITES.move_to_end(key)
        return cached.copy()
    s = skia()
    dom = _dom(data, digest)
    dom.setContainerSize(s.Size(*intrinsic))
    out = surface(size)
    canvas = out.getCanvas()
    canvas.scale(size[0] / intrinsic[0], size[1] / intrinsic[1])
    dom.render(canvas)
    image = to_pillow(out.makeImageSnapshot())
    if color is not None:
        alpha = image.getchannel("A")
        from PIL import ImageColor

        rgba = ImageColor.getcolor(color, "RGBA")
        image = PILImage.new("RGBA", image.size, rgba)
        image.putalpha(alpha.point(lambda a: round(a * rgba[3] / 255)))
    _SPRITES[key] = image
    while sum(im.width * im.height * 4 for im in _SPRITES.values()) > 128 * 1024**2 and len(_SPRITES) > 1:
        _SPRITES.popitem(last=False)
    return image.copy()


class SVG(Component):
    """Vector artwork from an .svg file path or SVG markup string."""

    def __init__(
        self,
        source: str | Path | bytes,
        *,
        width: float | None = None,
        height: float | None = None,
        color: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if isinstance(source, bytes):
            data = source
        elif isinstance(source, str) and source.lstrip().startswith("<"):
            data = source.encode()
        else:
            path = Path(source)
            if not path.is_file():
                raise FileNotFoundError(f"SVG file not found: {path}")
            data = path.read_bytes()
        self.source_bytes = data
        self.digest = hashlib.sha256(data).hexdigest()
        self.intrinsic = intrinsic_size(data)
        iw, ih = self.intrinsic
        if width is None and height is None:
            width, height = iw, ih
        elif height is None:
            height = finite(width, "width", 1) * ih / iw
        elif width is None:
            width = finite(height, "height", 1) * iw / ih
        self.width, self.height = finite(width, "width", 1), finite(height, "height", 1)
        if color is not None:
            from PIL import ImageColor

            ImageColor.getcolor(color, "RGBA")
        self.color = color

    def validate_render(self, backend, painter):
        _dom(self.source_bytes, self.digest)
        return True

    def render_raster(self, state, factor, age, painter):
        from ._portable import guard_size

        size = max(1, round(self.width * factor)), max(1, round(self.height * factor))
        guard_size(size)
        return rasterize(self.source_bytes, self.digest, self.intrinsic, size, self.color)


__all__ = ["SVG"]
