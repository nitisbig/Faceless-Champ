"""Reusable placement of the core chess renderer."""

from dataclasses import dataclass

from faceless_champ import ChessAssets, ChessChamp, ChessScript, ChessTheme

from .base import BlockBuild


@dataclass(frozen=True)
class ChessBoard:
    script: ChessScript
    theme: ChessTheme | None = None
    source_start: float = 0
    assets: ChessAssets | None = None

    def compose(self, context, bounds):
        theme = self.theme
        if theme is None and context.theme.name == "clean-flow":
            theme = ChessTheme(
                light="#FFFFFF",
                dark="#D6D2CA",
                background=context.theme.background,
                panel=context.theme.surface,
                foreground=context.theme.foreground,
                muted=context.theme.muted,
                accent=context.theme.accent,
            )
        board = ChessChamp(
            self.script,
            theme=theme,
            source_start=self.source_start,
            assets=self.assets,
            width=bounds.width,
            height=bounds.height,
            position=bounds.center,
        )
        return BlockBuild(board, {"board": board})
