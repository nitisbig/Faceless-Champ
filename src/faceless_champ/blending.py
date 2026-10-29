"""Layer blend modes, After Effects style; composited by Skia.

A component's ``blend`` decides how its pixels combine with what is already
drawn beneath it *inside the same layer*. A Group becomes its own layer when it
or one of its direct children blends, so blending stays local to the group
(like an After Effects pre-comp). ``stencil`` and ``silhouette`` cut the content
beneath them, which makes a shape act as a track matte for the rest of its group.
"""

BLEND_MODES = {
    "normal": "kSrcOver",
    "multiply": "kMultiply",
    "screen": "kScreen",
    "overlay": "kOverlay",
    "darken": "kDarken",
    "lighten": "kLighten",
    "color_dodge": "kColorDodge",
    "color_burn": "kColorBurn",
    "hard_light": "kHardLight",
    "soft_light": "kSoftLight",
    "difference": "kDifference",
    "exclusion": "kExclusion",
    "hue": "kHue",
    "saturation": "kSaturation",
    "color": "kColor",
    "luminosity": "kLuminosity",
    "add": "kPlus",
    # Keep the content beneath only where this layer is opaque / transparent.
    "stencil": "kDstIn",
    "silhouette": "kDstOut",
}

# Modes that also affect pixels outside this layer's own bounds.
UNBOUNDED_BLENDS = frozenset({"stencil", "silhouette"})


def blend_mode(value):
    if value not in BLEND_MODES:
        raise ValueError(f"blend must be one of: {', '.join(BLEND_MODES)}")
    return value


def skia_blend(skia, name):
    return getattr(skia.BlendMode, BLEND_MODES[name])


def blends(component):
    """True when the component, or a direct child of a group, uses a blend mode."""
    from .layout import Group

    if getattr(component, "blend", "normal") != "normal":
        return True
    return isinstance(component, Group) and any(getattr(c, "blend", "normal") != "normal" for c in component.children)


__all__ = ["BLEND_MODES", "blend_mode"]
