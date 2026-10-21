"""Pillow pixel kernels; scene traversal, visibility and identities live in the shared plan.

Rounded sprite placement and full-canvas affine sampling are separate paint
kernels to preserve existing Pillow pixels, not separate timeline evaluators.
"""

import math

from PIL import Image as PILImage
from PIL import ImageChops, ImageColor, ImageDraw, ImageFilter

from .._rendering.execute import walk_frame
from ..layout import Bounds, Group, transform_point
from ..motion import inverse, matrix, multiply, point


def paint_leaf(result, entry, parents, factor, raster):
    c, state, age = entry.component, entry.state, entry.age
    sprite = raster.sprite(c, state, factor, age)
    w, h = sprite.size
    x, y = state["position"]
    if c.anchor == "top_left":
        # Preserve the existing pixel-rounded unrotated anchor box.
        x += max(1, round(w * state["scale"])) / factor / 2
        y += max(1, round(h * state["scale"])) / factor / 2
    scale = state["scale"]
    rotation, opacity = state["rotation"], state["opacity"]
    for origin, parent in parents:
        x, y = transform_point((x, y), origin, parent)
        scale *= parent["scale"]
        rotation += parent["rotation"]
        opacity *= parent["opacity"]
    if scale != 1:
        sprite = sprite.resize((max(1, round(w * scale)), max(1, round(h * scale))), PILImage.Resampling.LANCZOS)
    x, y = x * factor, y * factor
    if rotation:
        sprite = sprite.rotate(-rotation, resample=PILImage.Resampling.BICUBIC, expand=True)
    if opacity < 1:
        sprite = sprite.copy()
        sprite.putalpha(sprite.getchannel("A").point(lambda a, opacity=opacity: round(a * opacity)))
    result.alpha_composite(sprite, (round(x - sprite.width / 2), round(y - sprite.height / 2)))


def paint_scene(frame, size, antialias, raster):
    big = size[0] * antialias, size[1] * antialias
    factor = min(big[0] / frame.scene.canvas.width, big[1] / frame.scene.canvas.height)
    result = PILImage.new("RGBA", big, frame.scene.canvas.bg)
    if frame.affine:
        paint = affine_painter(big, factor, raster)
        for layer in walk_frame(frame, paint, ((factor, 0, 0, factor, 0, 0), 1)):
            result.alpha_composite(layer)
    else:

        def paint(entry, children, parents):
            if isinstance(entry.component, Group):
                for _ in children(((entry.component._origin, entry.state),) + parents):
                    pass
            else:
                paint_leaf(result, entry, parents, factor, raster)

        for _ in walk_frame(frame, paint, ()):
            pass
    return result.resize(size, PILImage.Resampling.LANCZOS) if antialias > 1 else result


def affine_painter(size, factor, raster):
    def warp(sprite, transform):
        return sprite.transform(size, PILImage.Transform.AFFINE, inverse(transform), PILImage.Resampling.BICUBIC)

    def paint_affine(entry, children, context):
        parent, inherited_opacity = context
        c, state = entry.component, entry.state
        layer = PILImage.new("RGBA", size)
        if isinstance(c, Group) and c.drop_shadow is not None:
            raise ValueError("Group shadows are not supported; attach a shadow to a surface or leaf")
        if isinstance(c, Group):
            world = multiply(parent, matrix(state, c._origin))
            for image in children((world, inherited_opacity * state["opacity"])):
                layer.alpha_composite(image)
            if state["clip"] != (0, 0, 1, 1):
                boxes = [raster.measurement.entry_bounds(child, entry.time) for child in entry.children]
                box = Bounds(
                    min(b.left for b in boxes),
                    min(b.top for b in boxes),
                    max(b.right for b in boxes),
                    max(b.bottom for b in boxes),
                )
            local_center = c._origin
        else:
            sprite = raster.sprite(c, state, factor, entry.age)
            w, h = sprite.width / factor, sprite.height / factor
            local = dict(state)
            if c.anchor == "top_left":
                local["position"] = (
                    state["position"][0] + w * state["scale"] * state["scale_x"] / 2,
                    state["position"][1] + h * state["scale"] * state["scale_y"] / 2,
                )
            world = multiply(parent, matrix(local))
            transform = multiply(world, (1 / factor, 0, 0, 1 / factor, -w / 2, -h / 2))
            layer = warp(sprite, transform)
            box = Bounds(-w / 2, -h / 2, w / 2, h / 2)
            local_center = (0, 0)

        def apply_mask(points):
            mask = PILImage.new("L", size)
            draw = ImageDraw.Draw(mask)
            if points:
                draw.polygon([point(world, x, y) for x, y in points], fill=255)
            layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))

        if c.mask is not None:
            if c.mask.kind == "path":
                raise ValueError("PathMask requires backend='skia'")
            mw, mh = state["mask_width"], state["mask_height"]
            mx, my = state["mask_position"]
            mx += local_center[0]
            my += local_center[1]
            if not mw or not mh:
                points = []
            elif c.mask.kind == "ellipse":
                points = [
                    (mx + mw / 2 * math.cos(i * math.tau / 180), my + mh / 2 * math.sin(i * math.tau / 180))
                    for i in range(180)
                ]
            else:
                normalized = c.mask.points if c.mask.kind == "polygon" else ((0, 0), (1, 0), (1, 1), (0, 1))
                points = [(mx + (x - 0.5) * mw, my + (y - 0.5) * mh) for x, y in normalized]
            apply_mask(points)
        if state["clip"] != (0, 0, 1, 1):
            l, t, r, b = state["clip"]
            apply_mask(
                []
                if l == r or t == b
                else [(box.left + x * box.width, box.top + y * box.height) for x, y in ((l, t), (r, t), (r, b), (l, b))]
            )
        if c.drop_shadow is not None:
            from .._portable import guard_size

            guard_size(size)
            shadow = c.drop_shadow
            a, b, cc, d, _, _ = world
            dx, dy = shadow.offset
            offset = (a * dx + cc * dy, b * dx + d * dy)
            alpha = layer.getchannel("A").filter(
                ImageFilter.GaussianBlur(shadow.blur * max(math.hypot(a, b), math.hypot(cc, d)))
            )
            alpha = alpha.transform(
                size,
                PILImage.Transform.AFFINE,
                (1, 0, -offset[0], 0, 1, -offset[1]),
                resample=PILImage.Resampling.BICUBIC,
            )
            color = ImageColor.getcolor(shadow.color, "RGBA")
            cast = PILImage.new("RGBA", size, (*color[:3], 255))
            cast.putalpha(alpha.point(lambda v: round(v * color[3] / 255)))
            cast.alpha_composite(layer)
            layer = cast
        opacity = inherited_opacity * state["opacity"]
        if not isinstance(c, Group) and opacity < 1:
            layer.putalpha(layer.getchannel("A").point(lambda a: round(a * opacity)))
        return layer

    return paint_affine
