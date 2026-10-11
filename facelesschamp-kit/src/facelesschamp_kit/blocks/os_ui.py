"""Reusable tutorial placements over the public core OS UI API."""

from dataclasses import dataclass

from faceless_champ.os_ui import MacOSPreset, OSClip, OSScript, VirtualFileSystem

from .base import BlockBuild


@dataclass(frozen=True)
class OSWalkthrough:
    filesystem: VirtualFileSystem | None = None
    script: OSScript | None = None
    preset: MacOSPreset | None = None
    pages: tuple | None = None
    source_start: float = 0
    cursor: bool = True
    mode: str = "desktop"
    viewport: tuple[int, int] = (1920, 1080)

    def compose(self, context, bounds):
        width, height = self.viewport
        ratio = min(bounds.width / width, bounds.height / height)
        clip = OSClip(
            self.filesystem,
            self.script,
            preset=self.preset,
            pages=self.pages,
            source_start=self.source_start,
            cursor=self.cursor,
            mode=self.mode,
            width=width,
            height=height,
            scale=ratio,
            position=bounds.center,
        )
        return BlockBuild(clip, {"ui": clip})


@dataclass(frozen=True)
class FinderWindow(OSWalkthrough):
    mode: str = "finder"
    viewport: tuple[int, int] = (1280, 800)


@dataclass(frozen=True)
class SettingsWindow(OSWalkthrough):
    mode: str = "settings"
    viewport: tuple[int, int] = (1280, 800)
