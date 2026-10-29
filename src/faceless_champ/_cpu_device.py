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

    def blit(self, target, source, box, world=IDENTITY, opacity=1, blend="normal", perspective=None):
        from ._rendering.evaluate import transformed_box

        if box.width <= 0 or box.height <= 0:
            return
        if blend != "normal" or perspective is not None:
            self._blend_blit(target, source, box, world, opacity, blend, perspective)
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

    def _blend_blit(self, target, source, box, world, opacity, blend, perspective=None):
        """Composite through a tight local tile: optional perspective warp, then a
        Skia blend mode (stencil/silhouette affect the whole target)."""
        from ._rendering.evaluate import transformed_box
        from .blending import UNBOUNDED_BLENDS
        from .motion import inverse3

        area = transformed_box(box, world)
        l, t = max(0, math.floor(area.left) - 1), max(0, math.floor(area.top) - 1)
        r, b = min(target.width, math.ceil(area.right) + 1), min(target.height, math.ceil(area.bottom) + 1)
        if perspective is not None:
            # The warp may move content anywhere; render the whole affine footprint first.
            l, t = max(0, math.floor(area.left) - 1), max(0, math.floor(area.top) - 1)
            r, b = math.ceil(area.right) + 1, math.ceil(area.bottom) + 1
        if r <= l or b <= t:
            if blend == "stencil":  # an empty matte hides everything beneath it
                target.paste((0, 0, 0, 0), (0, 0, *target.size))
            return
        with self.surface((r - l, b - t)) as tile:
            self.blit(tile, source, box, multiply((1, 0, 0, 1, -l, -t), world), opacity)
            if perspective is not None:
                corners = []
                for x, y in ((l, t), (r, t), (r, b), (l, b)):
                    w = perspective[2][0] * x + perspective[2][1] * y + perspective[2][2]
                    if w <= 1e-6:
                        raise ValueError(
                            "Perspective tilt is too steep for this layer; reduce tilt or raise perspective"
                        )
                    corners.append(
                        (
                            (perspective[0][0] * x + perspective[0][1] * y + perspective[0][2]) / w,
                            (perspective[1][0] * x + perspective[1][1] * y + perspective[1][2]) / w,
                        )
                    )
                left = max(0, math.floor(min(p[0] for p in corners)) - 1)
                top = max(0, math.floor(min(p[1] for p in corners)) - 1)
                right = min(target.width, math.ceil(max(p[0] for p in corners)) + 1)
                bottom = min(target.height, math.ceil(max(p[1] for p in corners)) + 1)
                if right <= left or bottom <= top:
                    return
                # Output (x, y) -> canvas (x + left, y + top) -> Pinv -> tile (u - l, v - t).
                inv = inverse3(perspective)
                rows = []
                for row in inv:
                    rows.append((row[0], row[1], row[0] * left + row[1] * top + row[2]))
                m = (
                    tuple(rows[0][j] - l * rows[2][j] for j in range(3)),
                    tuple(rows[1][j] - t * rows[2][j] for j in range(3)),
                    rows[2],
                )
                k = m[2][2]
                coeffs = [v / k for row in m for v in row][:8]
                warped = tile.transform(
                    (right - left, bottom - top), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC
                )
                piece, (l, t) = warped, (left, top)
            else:
                r, b = min(r, target.width), min(b, target.height)
                piece = tile.crop((0, 0, r - l, b - t))
            try:
                if blend == "normal":
                    target.alpha_composite(piece, (l, t))
                    return
                from ._skia_fx import blend_images

                if blend in UNBOUNDED_BLENDS:
                    with self.surface(target.size) as full:
                        full.paste(piece, (l, t))
                        target.paste(blend_images(target, full, blend))
                    return
                region = target.crop((l, t, l + piece.width, t + piece.height))
                target.paste(blend_images(region, piece, blend), (l, t))
            finally:
                piece.close()

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
        from ._effects_cpu import background
        from ._rendering.evaluate import component_ink_box, density

        q = density(world)
        box = component_ink_box(c, Bounds(-c.width / 2, -c.height / 2, c.width / 2, c.height / 2))
        size = max(1, math.ceil(box.width * q)), max(1, math.ceil(box.height * q))
        guard_size(size)
        with background(c, age, size, bounds=box) as sprite:
            self.blit(target, sprite, box, world, opacity)
        return True

    def finish(self, target, size):
        return target.resize(size, Image.Resampling.LANCZOS) if target.size != size else target.copy()

    def close(self):
        pass
