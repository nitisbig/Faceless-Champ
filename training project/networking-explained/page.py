"""Tutorial-specific browser illustration; shared styling lives in FlowDesign."""

from faceless_champ import Circle, FlowDesign, Group, Polyline, Rectangle

PALETTE = FlowDesign.named("networking").palette


def _rounded(center, size, fill, radius=18, **kwargs):
    return Rectangle(
        width=size[0],
        height=size[1],
        corner_radius=min(radius, min(size) / 2),
        position=center,
        fill=fill,
        stroke=None,
        stroke_width=0,
        **kwargs,
    )


def _tag(component, name):
    component.training_id = name
    return component


def page_part(id, center):
    """Return independently animated, rounded parts of the laptop's loaded page."""
    x, y = center
    body_center = (x, y + 20)
    if id == "page-surface":
        result = _rounded(body_center, (344, 204), "#F8FAFF", radius=20)
    elif id in {"page-header", "page-bar"}:
        result = Group(
            _rounded((x - 103, y - 50), (86, 12), PALETTE["blue"], radius=6),
            _rounded((x + 75, y - 50), (108, 8), "#CBD6E9", radius=4),
            _rounded((x - 82, y - 27), (128, 7), "#BFCDE5", radius=3.5),
        )
    elif id == "page-image":
        result = Group(
            _rounded((x - 72, y + 38), (148, 90), PALETTE["pale_blue"], radius=16),
            _rounded((x - 88, y + 35), (88, 48), "#BCD1FE", radius=16),
            Circle(radius=15, fill="#FFFFFF", stroke=None, stroke_width=0, position=(x - 32, y + 12)),
            _rounded((x - 56, y + 61), (88, 17), "#82AAFA", radius=8),
        )
    elif id == "page-rows":
        result = Group(
            _rounded((x + 85, y + 1), (108, 11), PALETTE["ink"], radius=5.5),
            _rounded((x + 86, y + 26), (110, 7), "#B7C7E2", radius=3.5),
            _rounded((x + 75, y + 44), (88, 7), "#CBD6E9", radius=3.5),
            _rounded((x + 62, y + 74), (62, 22), PALETTE["blue"], radius=11),
        )
    elif id == "page-ready":
        result = Group(
            Circle(radius=14, fill=PALETTE["pale_teal"], stroke=None, stroke_width=0, position=(x + 142, y + 93)),
            Polyline(
                ((x + 135, y + 93), (x + 140, y + 98), (x + 149, y + 88)),
                stroke=PALETTE["teal"],
                stroke_width=3,
                line_cap="round",
            ),
        )
    else:
        raise ValueError(f"Unknown networking page part: {id}")
    return _tag(result, id)
