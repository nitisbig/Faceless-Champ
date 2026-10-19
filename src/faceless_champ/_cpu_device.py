"""Bounded local Pillow operations for opt-in effects and procedural content."""

import math
from contextlib import contextmanager

from PIL import Image, ImageChops, ImageFilter

from ._portable import guard_size
from .layout import Bounds
from .motion import IDENTITY, inverse, multiply


class CPUDevice:
    def __init__(self, working_mb=512):
        self.limit = round(working_mb * 1024**2)
        self.bytes = 0

    @contextmanager
    def surface(self, size, color="#00000000"):
        guard_size(size)
        cost = size[0] * size[1] * 4
        if self.bytes + cost > self.limit:
            raise ValueError("Local composition exceeds working_mb; reduce bounds, AA or scale")
        self.bytes += cost
        image = Image.new("RGBA", size, color)
        try:
            yield image
        finally:
            image.close()
            self.bytes -= cost

    def clear(self, target, color="#00000000"):
        target.paste(color, (0, 0, *target.size))

    def upload(self, image, key=None):
        return image

    def blit(self, target, source, box, world=IDENTITY, opacity=1):
        from ._render_state import transformed_box

        if box.width <= 0 or box.height <= 0:
            return
        area = transformed_box(box, world)
        l, t = max(0, math.floor(area.left)), max(0, math.floor(area.top))
        r, b = min(target.width, math.ceil(area.right)), min(target.height, math.ceil(area.bottom))
        if l >= r or t >= b:
            return
        transform = multiply(world, (box.width / source.width, 0, 0, box.height / source.height, box.left, box.top))
        if transform[:4] == (1, 0, 0, 1) and all(v == round(v) for v in transform[4:]):
            if opacity == 1:
                target.alpha_composite(source, tuple(round(v) for v in transform[4:]))
            else:
                with source.copy() as tile:
                    tile.putalpha(tile.getchannel("A").point(lambda a: round(a * opacity)))
                    target.alpha_composite(tile, tuple(round(v) for v in transform[4:]))
            return
        transform = multiply((1, 0, 0, 1, -l, -t), transform)
        with source.transform(
            (r - l, b - t), Image.Transform.AFFINE, inverse(transform), Image.Resampling.BICUBIC
        ) as tile:
            if opacity != 1:
                tile.putalpha(tile.getchannel("A").point(lambda a: round(a * opacity)))
            target.alpha_composite(tile, (l, t))

    def mask(self, target, mask):
        target.putalpha(ImageChops.multiply(target.getchannel("A"), mask.getchannel("A")))

    def content(self, target, stack, scale, time, content_box=None):
        from ._effects_cpu import content

        with content(target, stack, scale, time, content_box) as result:
            target.paste(result)

    def halos(self, target, stack, scale):
        from ._effects_cpu import halos

        with halos(target, stack, scale) as result:
            target.paste(result)

    def shadow(self, target, shadow, scale, include_content=True):
        from PIL import ImageColor

        if shadow is None:
            return
        color = ImageColor.getcolor(shadow.color, "RGBA")
        with self.surface(target.size) as under:
            alpha = target.getchannel("A").filter(ImageFilter.GaussianBlur(shadow.blur * scale))
            alpha = alpha.transform(
                target.size,
                Image.Transform.AFFINE,
                (1, 0, -shadow.offset[0] * scale, 0, 1, -shadow.offset[1] * scale),
                Image.Resampling.BICUBIC,
            )
            under.paste((*color[:3], 255), (0, 0, *target.size))
            under.putalpha(alpha.point(lambda a: round(a * color[3] / 255)))
            if include_content:
                under.alpha_composite(target)
            target.paste(under)

    def mix(self, target, first, second, progress, transition):
        from ._effects_cpu import crossfade

        with crossfade(first, second, progress, transition) as result:
            target.paste(result)

    def component(self, target, c, state, box, world, opacity, age):
        if not getattr(c, "_procedural", False):
            return False
        from ._compositor import density
        from ._effects_cpu import background

        q = density(world)
        size = max(1, math.ceil(c.width * q)), max(1, math.ceil(c.height * q))
        guard_size(size)
        with background(c, age, size) as sprite:
            self.blit(target, sprite, Bounds(-c.width / 2, -c.height / 2, c.width / 2, c.height / 2), world, opacity)
        return True

    def finish(self, target, size):
        return target.resize(size, Image.Resampling.LANCZOS) if target.size != size else target.copy()

    def close(self):
        pass
