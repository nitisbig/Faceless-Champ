"""Measured guide visuals assembled from public core and kit components."""

from copy import deepcopy

from facelesschamp_kit.blocks import FlowDiagram

from faceless_champ import (
    Bounds,
    CodeTheme,
    CodingChamp,
    Polyline,
    Rectangle,
    Text,
)
from faceless_champ.coding import MONO_FONT

from .spec import ACCENT, INK, LINE, MUTED, SURFACE

SAFE = Bounds(72, 72, 1848, 1008)
CODE_THEME = CodeTheme(
    background="#111318", chrome="#202329", muted=MUTED, foreground=INK, accent=ACCENT, highlight="#233D43"
)


def line(start, end, **kwargs):
    return Polyline([start, end], **kwargs)


def label(text, x, y, size=34, color=INK, mono=False):
    return Text(text, font_size=size, color=color, position=(x, y), font=str(MONO_FONT) if mono else None)


def box(x, y, w, h, fill=SURFACE, stroke=LINE, radius=16):
    return Rectangle(width=w, height=h, fill=fill, stroke=stroke, stroke_width=2, corner_radius=radius, position=(x, y))


def editor(source, *, x=560, y=520, w=960, h=840, size=30, file="hello.py", language="python", first=1, highlights=()):
    return CodingChamp(
        source,
        width=w,
        height=h,
        font_size=size,
        filename=file,
        theme=CODE_THEME,
        language=language,
        first_line=first,
        highlighted_lines=highlights,
        position=(x, y),
    )


class Artist:
    def __init__(self, segment, cues, events):
        self.segment, self.cues, self.events = segment, cues, events
        self.counter = 0

    def time(self, cue):
        return self.segment.start if cue is None else self.cues.cue(cue).start

    def local(self, cue):
        return 0 if cue is None else self.segment.cue_time(cue)

    def put(self, component, cue=None, *, until=None, enter=True, seconds=0.35, name=None):
        self.counter += 1
        at = self.local(cue)
        end = self.local(until) if until is not None else self.segment.duration
        handle = self.segment.add_core(
            lambda ctx, b, source=component: deepcopy(source),
            id=name or f"visual-{self.counter}",
            bounds=SAFE,
            at=at,
            duration=end - at,
            enter="fade" if enter else None,
            enter_duration=seconds if enter else None,
        )
        self.events.append(
            {
                "segment": self.segment.name,
                "cue": cue,
                "start": self.segment.start + at,
                "end": self.segment.start + end,
                "kind": type(component).__name__,
            }
        )
        return handle

    def motion(self, handle, animation, cue=None, duration=0.5, offset=0):
        at = self.local(cue) + offset
        self.segment.play(handle, animation, at=at, duration=duration)

    def text(self, text, x, y, cue=None, *, size=34, color=INK, until=None):
        return self.put(label(text, x, y, size, color), cue, until=until)

    def code(self, source, cue=None, *, until=None, **kwargs):
        # File path label, traffic lights, and source syntax belong to CodingChamp.
        component = editor(source, **kwargs)
        component.position = (kwargs.get("x", 560), kwargs.get("y", 520))
        return self.put(component, cue, until=until)

    def flow(self, ctx, steps, cue, *, bounds=None, until=None):
        bounds = bounds or Bounds(230, 350, 1690, 540)
        self.counter += 1
        at = self.local(cue)
        end = self.local(until) if until else self.segment.duration
        handle = self.segment.add(
            FlowDiagram(tuple(steps)),
            id=f"flow-{self.counter}",
            bounds=bounds,
            at=at,
            duration=end - at,
            enter="stagger",
            enter_duration=0.8,
        )
        self.events.append(
            {
                "segment": self.segment.name,
                "cue": cue,
                "start": self.segment.start + at,
                "end": self.segment.start + end,
                "kind": "FlowDiagram",
            }
        )
        return handle
