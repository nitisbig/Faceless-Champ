"""Composition-only CodingChamp blocks; execution and pixels belong to core."""

from dataclasses import dataclass

from faceless_champ import Bounds, Group, PlaygroundCanvas, PlaygroundOutput, PlaygroundScript, PreparedPlayground
from faceless_champ import CodeEditor as CoreEditor

from ..diagnostics import KitError
from .base import BlockBuild


@dataclass(frozen=True)
class CodeEditor:
    script: PlaygroundScript
    font_size: float = 24
    theme: str = "midnight"
    source_start: float = 0

    def compose(self, context, bounds):
        if self.font_size < context.theme.minimum_font_size:
            raise KitError("PLAYGROUND_LAYOUT", "Editor font is below the theme minimum")
        editor = CoreEditor(
            self.script,
            width=bounds.width,
            height=bounds.height,
            font_size=self.font_size,
            theme=self.theme,
            source_start=self.source_start,
            position=bounds.center,
        )
        return BlockBuild(editor, {"editor": editor})


@dataclass(frozen=True)
class CodingPlayground:
    prepared: PreparedPlayground
    layout: str = "side"
    code_ratio: float = 0.5
    font_size: float = 24
    theme: str = "midnight"
    output: bool = True
    source_start: float = 0

    def compose(self, context, bounds: Bounds):
        from faceless_champ.components import finite

        ratio = finite(self.code_ratio, "code_ratio", 0.2)
        if ratio > 0.8 or self.layout not in {"side", "stacked"}:
            raise KitError("PLAYGROUND_LAYOUT", "Use side/stacked and code_ratio between .2 and .8")
        minimum = context.theme.minimum_font_size
        if self.font_size < minimum:
            raise KitError("PLAYGROUND_LAYOUT", "Editor font is below the theme minimum")
        gap = context.theme.spacing
        if self.layout == "side":
            edge = bounds.left + (bounds.width - gap) * ratio
            editor_box = Bounds(bounds.left, bounds.top, edge, bounds.bottom)
            canvas_box = Bounds(edge + gap, bounds.top, bounds.right, bounds.bottom)
        else:
            edge = bounds.top + (bounds.height - gap) * ratio
            editor_box = Bounds(bounds.left, bounds.top, bounds.right, edge)
            canvas_box = Bounds(bounds.left, edge + gap, bounds.right, bounds.bottom)
        children = {}
        if self.output:
            output_height = max(100, canvas_box.height * 0.22)
            children["output"] = PlaygroundOutput(
                self.prepared,
                width=canvas_box.width,
                height=output_height,
                font_size=minimum,
                source_start=self.source_start,
                position=(canvas_box.left, canvas_box.bottom - output_height),
                anchor="top_left",
            )
            canvas_box = Bounds(
                canvas_box.left, canvas_box.top, canvas_box.right, canvas_box.bottom - output_height - gap
            )
        editor = CodeEditor(self.prepared.script, self.font_size, self.theme, self.source_start).compose(
            context, editor_box
        )
        children["editor"] = editor.root
        children["canvas"] = PlaygroundCanvas(
            self.prepared,
            width=canvas_box.width,
            height=canvas_box.height,
            font_size=self.font_size,
            minimum_font_size=minimum,
            source_start=self.source_start,
            position=canvas_box.center,
        )
        return BlockBuild(Group(*children.values()), children)
