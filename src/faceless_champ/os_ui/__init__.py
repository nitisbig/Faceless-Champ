"""Offline, authored OS tutorial visuals with a macOS-style preset."""

from .clip import OSClip
from .model import Control, File, Folder, MacOSPreset, SettingsPage, VirtualFileSystem, starter_pages
from .script import OSScript

__all__ = [
    "Control",
    "File",
    "Folder",
    "MacOSPreset",
    "OSClip",
    "OSScript",
    "SettingsPage",
    "VirtualFileSystem",
    "starter_pages",
]
