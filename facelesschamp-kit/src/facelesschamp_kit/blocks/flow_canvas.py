"""Themed placement of the public core FlowChamp component."""

from dataclasses import dataclass

from facelesschamp_kit.diagrams import FlowChamp, FlowDesign, FlowGraph, FlowScript, FlowTheme

from .base import BlockBuild
from .flow_design import _design


@dataclass(frozen=True)
class FlowCanvas:
    """Place a diagram or a designed connection layer in a kit layout.

    With ``design``, graph nodes are transparent binding proxies for separate
    ``FlowCard`` layouts. The design styles connections and packets; it does not
    turn graph metadata into cards. ``theme`` configures the legacy diagram and
    cannot be combined with ``design``, which owns its connection styling.
    """

    graph: FlowGraph
    script: FlowScript | None = None
    theme: FlowTheme | None = None
    viewport: tuple = (1600, 900)
    source_start: float = 0
    design: FlowDesign | str | None = None

    def compose(self, context, bounds):
        width, height = self.viewport
        if self.design is not None:
            if self.theme is not None:
                raise ValueError("FlowCanvas accepts either theme or design; design owns its connection styling")
            root = _design(self.design).connections(
                self.graph,
                self.script,
                width=width,
                height=height,
                source_start=self.source_start,
                position=bounds.center,
                scale=min(bounds.width / width, bounds.height / height),
            )
            return BlockBuild(root, root.parts)
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
