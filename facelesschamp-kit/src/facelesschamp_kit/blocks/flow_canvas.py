"""Themed placement of the public core FlowChamp component."""

from dataclasses import dataclass

from faceless_champ.flow import FlowChamp, FlowGraph, FlowScript, FlowTheme

from .base import BlockBuild


@dataclass(frozen=True)
class FlowCanvas:
    graph: FlowGraph
    script: FlowScript | None = None
    theme: FlowTheme | None = None
    viewport: tuple = (1600, 900)
    source_start: float = 0

    def compose(self, context, bounds):
        width, height = self.viewport
        theme = self.theme or FlowTheme(
            foreground=context.theme.foreground,
            surface=context.theme.surface,
            accent=context.theme.accent,
            background=context.theme.background,
            font=context.theme.font,
            font_size=context.theme.body_size,
            minimum_font_size=context.theme.minimum_font_size,
            stroke=context.theme.muted,
        )
        clip = FlowChamp(
            self.graph,
            self.script,
            theme=theme,
            width=width,
            height=height,
            source_start=self.source_start,
            position=bounds.center,
            scale=min(bounds.width / width, bounds.height / height),
        )
        return BlockBuild(clip, {"diagram": clip})
