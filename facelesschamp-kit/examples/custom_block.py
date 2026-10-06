"""A project-specific block and independent reused instances."""

from dataclasses import dataclass

from faceless_champ import Circle, Group, Text

from facelesschamp_kit import BlockBuild, Video


@dataclass(frozen=True)
class Badge:
    label: str

    def compose(self, ctx, bounds):
        circle = Circle(radius=90, fill=ctx.theme.accent, stroke=None, position=bounds.center)
        text = Text(self.label, font_size=32, color=ctx.theme.background, position=bounds.center)
        return BlockBuild(Group(circle, text), {"circle": circle, "label": text})


def build(ctx):
    video = Video(ctx)
    badge = Badge("REUSE")
    for name in ("first", "second"):
        with video.segment(name, duration=3) as segment:
            handle = segment.add(badge, enter="pop")
            segment.play(handle["circle"], lambda circle: circle.animate.rotate_to(20), at=1, duration=1)
    return video
