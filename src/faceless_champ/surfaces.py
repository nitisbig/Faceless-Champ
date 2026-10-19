"""Offline card and backdrop surfaces, rasterized once in design pixels."""

import math
from contextlib import closing
from dataclasses import dataclass

from PIL import Image as PILImage
from PIL import ImageColor, ImageDraw, ImageFilter

from .components import Component, Image, finite
from .gradients import LinearGradient, RadialGradient
from .layout import Bounds

_RASTER_SCALE = 2


@dataclass(frozen=True)
class ShadowStyle:
    """Soft card shadow; blur and offset are measured in design pixels."""

    color: str = "#00000026"
    blur: float = 16
    offset: tuple[float, float] = (0, 12)

    def __post_init__(self):
        ImageColor.getcolor(self.color, "RGBA")
        object.__setattr__(self, "blur", finite(self.blur, "shadow blur", 0))
        try:
            offset = tuple(finite(value, "shadow offset") for value in self.offset)
        except TypeError as exc:
            raise ValueError("Shadow offset needs two coordinates") from exc
        if len(offset) != 2:
            raise ValueError("Shadow offset needs two coordinates")
        object.__setattr__(self, "offset", offset)


class Surface(Component):
    """Retained card/backdrop description. Layout includes shadow clearance.

    Use the existing factories with render_mode='vector'. No pixels or native
    handles are stored in this component; renderers own all raster caches.
    """

    def __init__(self, bounds, *, fill, radius=0, shadow=None, pattern=None, spacing=28, dot_radius=1, **options):
        _check_bounds(bounds)
        _check_component_options(options)
        self.width, self.height = bounds.width, bounds.height
        self.fill = fill
        if not isinstance(fill, (str, LinearGradient, RadialGradient)):
            raise TypeError("Surface fill must be a color or gradient")
        if isinstance(fill, str):
            ImageColor.getcolor(fill, "RGBA")
        self.radius = finite(radius, "surface radius", 0)
        card_content_bounds(bounds, shadow=shadow, padding=0)
        if shadow and (shadow.blur > 4096 or any(abs(v) > 4096 for v in shadow.offset)):
            raise ValueError("Surface shadow exceeds the allocation budget")
        self.surface_shadow = shadow
        self.pattern, self.spacing, self.dot_radius = pattern, spacing, dot_radius
        super().__init__(position=bounds.center, **options)


def _check_bounds(bounds):
    if not isinstance(bounds, Bounds):
        raise TypeError("Surface needs Bounds")
    if bounds.width < 1 or bounds.height < 1:
        raise ValueError("Surface bounds need at least one design pixel per side")


def _shadow_padding(shadow):
    if shadow is None:
        return 0
    if not isinstance(shadow, ShadowStyle):
        raise TypeError("shadow must be a ShadowStyle or None")
    return math.ceil(3 * shadow.blur + max(abs(value) for value in shadow.offset))


def card_content_bounds(bounds, *, shadow=None, padding=28):
    """Inset allocated card bounds by shadow clearance and content padding.

    Shadow clearance remains inside the allocated viewport. Raise when the
    allocation cannot leave a positive content area rather than clipping it.
    """
    _check_bounds(bounds)
    inset = _shadow_padding(shadow) + finite(padding, "card padding", 0)
    if 2 * inset >= min(bounds.width, bounds.height):
        raise ValueError("Card bounds are too small for shadow and padding")
    return Bounds(bounds.left + inset, bounds.top + inset, bounds.right - inset, bounds.bottom - inset)


def _check_component_options(component_options):
    reserved = {"width", "height", "position", "anchor", "fit", "trim"} & component_options.keys()
    if reserved:
        raise TypeError(f"Surface bounds reserve geometry options: {', '.join(sorted(reserved))}")


def _image(source, bounds, component_options):
    _check_component_options(component_options)
    return Image.from_source(
        source,
        width=bounds.width,
        height=bounds.height,
        position=bounds.center,
        trim=False,
        **component_options,
    )


def card_surface(bounds, *, fill="#FFFFFF", radius=44, shadow=None, render_mode="raster", **component_options):
    """Return an Image containing a rounded card and optional blurred shadow.

    ``bounds`` includes transparent shadow clearance, so the face is smaller
    than the image viewport. Use ``card_content_bounds`` for content placement.
    Pixels are generated once at 2x design resolution; ordinary image motion,
    opacity, masks, and z-index apply without a new renderer path.
    """
    _check_bounds(bounds)
    if render_mode not in {"raster", "vector"}:
        raise ValueError("render_mode must be raster or vector")
    if render_mode == "vector":
        return Surface(bounds, fill=fill, radius=radius, shadow=shadow, **component_options)
    if isinstance(fill, (LinearGradient, RadialGradient)):
        from ._surface_raster import _allocation, gradient_card

        _check_component_options(component_options)
        _allocation(bounds.width, bounds.height)
        radius = finite(radius, "card radius", 0)
        if shadow is not None:
            if not isinstance(shadow, ShadowStyle):
                raise TypeError("shadow must be a ShadowStyle or None")
            if shadow.blur > 4096 or any(abs(v) > 4096 for v in shadow.offset):
                raise ValueError("Gradient shadow exceeds the allocation budget")
        card_content_bounds(bounds, shadow=shadow, padding=0)
        with closing(gradient_card(bounds, fill, radius, shadow, _shadow_padding(shadow))) as source:
            return _image(source, bounds, component_options)
    if not isinstance(fill, str):
        raise TypeError("Surface fill must be a color string, LinearGradient or RadialGradient")
    color = ImageColor.getcolor(fill, "RGBA")
    radius = finite(radius, "card radius", 0)
    face = card_content_bounds(bounds, shadow=shadow, padding=0)
    inset = _shadow_padding(shadow)
    size = (round(bounds.width * _RASTER_SCALE), round(bounds.height * _RASTER_SCALE))
    source = PILImage.new("RGBA", size)
    box = (
        inset * _RASTER_SCALE,
        inset * _RASTER_SCALE,
        (bounds.width - inset) * _RASTER_SCALE - 1,
        (bounds.height - inset) * _RASTER_SCALE - 1,
    )
    corner = min(radius, face.width / 2, face.height / 2) * _RASTER_SCALE
    if shadow is not None:
        layer = PILImage.new("RGBA", size)
        dx, dy = (value * _RASTER_SCALE for value in shadow.offset)
        shifted = (box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy)
        ImageDraw.Draw(layer).rounded_rectangle(shifted, radius=corner, fill=ImageColor.getcolor(shadow.color, "RGBA"))
        source.alpha_composite(layer.filter(ImageFilter.GaussianBlur(shadow.blur * _RASTER_SCALE)))
    ImageDraw.Draw(source).rounded_rectangle(box, radius=corner, fill=color)
    return _image(source, bounds, component_options)


def gradient_surface(bounds, *, fill, **component_options):
    """Return a rectangular 2x gradient Image, with no rounded corners or shadow.

    Paint is static, premultiplied encoded-sRGB, and bounded to 8,388,608 source
    pixels / a 192 MiB working-set estimate. Reuse through ordinary Image motion.
    """
    if not isinstance(fill, (LinearGradient, RadialGradient)):
        raise TypeError("gradient_surface fill must be LinearGradient or RadialGradient")
    return card_surface(bounds, fill=fill, radius=0, shadow=None, **component_options)


def dot_grid(bounds, *, color="#B7B3AE55", spacing=28, radius=1, render_mode="raster", **component_options):
    """Return a transparent, evenly spaced dot-grid Image for a backdrop."""
    _check_bounds(bounds)
    spacing = finite(spacing, "dot spacing", 1)
    radius = finite(radius, "dot radius", 0.001)
    if render_mode not in {"raster", "vector"}:
        raise ValueError("render_mode must be raster or vector")
    if render_mode == "vector":
        return Surface(bounds, fill=color, pattern="dots", spacing=spacing, dot_radius=radius, **component_options)
    color = ImageColor.getcolor(color, "RGBA")
    size = (round(bounds.width * _RASTER_SCALE), round(bounds.height * _RASTER_SCALE))
    source = PILImage.new("RGBA", size)
    draw = ImageDraw.Draw(source)
    r = radius * _RASTER_SCALE
    for row in range(math.ceil(bounds.height / spacing)):
        y = (row + 0.5) * spacing * _RASTER_SCALE
        for column in range(math.ceil(bounds.width / spacing)):
            x = (column + 0.5) * spacing * _RASTER_SCALE
            draw.ellipse((x - r, y - r, x + r, y + r), fill=color)
    return _image(source, bounds, component_options)
