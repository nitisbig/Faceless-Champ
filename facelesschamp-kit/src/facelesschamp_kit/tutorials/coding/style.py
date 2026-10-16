"""Editable, validated style data for the approved coding tutorial design."""

import json
import math
from dataclasses import asdict, dataclass, fields, replace
from importlib.resources import files
from pathlib import Path

from faceless_champ import Bounds, CodeTheme, CodeWorkspaceDesign, Spring
from PIL import ImageColor

from ...diagnostics import KitError


@dataclass(frozen=True)
class CodingTutorialStyle:
    background: str = "#E8E6E2"
    accent: str = "#FF5A20"
    python_blue: str = "#3776AB"
    python_yellow: str = "#FFD343"
    editor_background: str = "#14161A"
    editor_chrome: str = "#1F2329"
    foreground: str = "#F5F5F5"
    muted: str = "#A6A7AD"
    connector: str = "#BDB8B1"
    inset_x: float = 96
    inset_y: float = 108
    editor_scale: float = 0.64
    code_size: float = 54
    terminal_size: float = 32
    shrink_duration: float = 0.8
    restore_duration: float = 0.9
    terminal_entrance_duration: float = 0.6
    terminal_exit_duration: float = 0.45
    spring_stiffness: float = 180
    window_damping: float = 27
    icon_damping: float = 23

    def __post_init__(self):
        try:
            for field in fields(self):
                value = getattr(self, field.name)
                if field.type is str:
                    if not isinstance(value, str):
                        raise ValueError(f"{field.name} must be a color string")
                    ImageColor.getcolor(value, "RGBA")
                elif (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    or value <= 0
                ):
                    raise ValueError(f"{field.name} must be finite and positive")
            if self.inset_x >= 960 or self.inset_y >= 540:
                raise ValueError("Insets must leave positive workspace dimensions")
            self.workspace()
            Spring(self.spring_stiffness, self.window_damping, 1)
            Spring(self.spring_stiffness, self.icon_damping, 1)
        except (TypeError, ValueError) as exc:
            raise KitError("TUTORIAL_STYLE", str(exc)) from exc

    @classmethod
    def load(cls, path=None):
        source = Path(path) if path is not None else files(__package__).joinpath("style.json")
        try:
            data = json.loads(source.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise TypeError("Style must be a JSON object")
            return cls(**data)
        except (OSError, TypeError, ValueError) as exc:
            raise KitError("TUTORIAL_STYLE", f"Cannot load coding tutorial style: {exc}", path=str(source)) from exc

    def to_dict(self):
        return asdict(self)

    @property
    def palette(self):
        return {
            "background": self.background,
            "surface": self.editor_background,
            "foreground": self.foreground,
            "muted": self.muted,
            "accent": self.accent,
        }

    def workspace(self):
        theme = replace(
            CodeTheme.named("clean-flow"),
            background=self.editor_background,
            chrome=self.editor_chrome,
            foreground=self.foreground,
            muted=self.muted,
            accent=self.accent,
        )
        return CodeWorkspaceDesign.named(
            "clean-flow",
            bounds=Bounds(self.inset_x, self.inset_y, 1920 - self.inset_x, 1080 - self.inset_y),
            background=self.background,
            theme=theme,
            editor_scale=self.editor_scale,
            code_size=self.code_size,
            terminal_size=self.terminal_size,
            shrink_duration=self.shrink_duration,
            restore_duration=self.restore_duration,
            terminal_entrance_duration=self.terminal_entrance_duration,
            terminal_exit_duration=self.terminal_exit_duration,
        )
