"""Authored, host-independent filesystem and settings models."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class File:
    id: str
    name: str
    text: str = ""
    image: str | Path | None = None


@dataclass(frozen=True)
class Folder:
    id: str
    name: str
    children: tuple[File | Folder, ...] = ()


class VirtualFileSystem:
    """A virtual tree. Operations never read or write host directories."""

    def __init__(self, root: Folder):
        if not isinstance(root, Folder):
            raise TypeError("root must be a Folder")
        self.root = root.id
        self.nodes = {}
        self.parents = {}
        self.trashed = {}

        def visit(node, parent):
            if not isinstance(node, (File, Folder)):
                raise TypeError("Expected File or Folder")
            self._name(node.name)
            if not isinstance(node.id, str) or not node.id or node.id in self.nodes or ":" in node.id:
                raise ValueError("Node IDs must be unique, nonempty, and contain no colon")
            self.nodes[node.id] = deepcopy(node)
            self.parents[node.id] = parent
            if isinstance(node, Folder):
                names = [child.name for child in node.children]
                if len(names) != len(set(names)):
                    raise ValueError("Duplicate sibling names")
                for child in node.children:
                    visit(child, node.id)

        visit(root, None)

    @staticmethod
    def _name(name):
        if not isinstance(name, str) or not name.strip() or "/" in name or name in {".", ".."}:
            raise ValueError("Names must be nonempty and cannot contain '/' or be '.' or '..'")

    def node(self, id):
        if id not in self.nodes:
            raise ValueError(f"Unknown file ID: {id}")
        return self.nodes[id]

    def visible(self, id):
        self.node(id)
        while id is not None:
            if id in self.trashed:
                return False
            id = self.parents[id]
        return True

    def children(self, id):
        if not isinstance(self.node(id), Folder):
            raise TypeError(f"Not a folder: {id}")
        return [n for key, n in self.nodes.items() if self.parents[key] == id and self.visible(key)]

    def _destination(self, parent, name, exclude=None):
        self._name(name)
        if not self.visible(parent):
            raise ValueError("Destination is in Trash")
        if any(n.name == name and n.id != exclude for n in self.children(parent)):
            raise ValueError(f"Name already exists: {name}")

    def rename(self, id, name):
        from dataclasses import replace

        node = self.node(id)
        if id == self.root or not self.visible(id):
            raise ValueError("Cannot rename root or trashed nodes")
        self._destination(self.parents[id], name, id)
        self.nodes[id] = replace(node, name=name)

    def create_folder(self, parent, id, name):
        self._destination(parent, name)
        if not isinstance(id, str) or not id or ":" in id or id in self.nodes:
            raise ValueError("New folder requires a unique nonempty ID without ':'")
        self.nodes[id] = Folder(id, name)
        self.parents[id] = parent

    def move(self, id, parent):
        node = self.node(id)
        if id == self.root or not self.visible(id):
            raise ValueError("Cannot move root or trashed nodes")
        self._destination(parent, node.name, id)
        cursor = parent
        while cursor is not None:
            if cursor == id:
                raise ValueError("Cannot move a folder into itself or its descendants")
            cursor = self.parents[cursor]
        self.parents[id] = parent

    def copy(self, id, parent, new_id, name=None):
        from dataclasses import replace

        node = self.node(id)
        if not self.visible(id):
            raise ValueError("Cannot copy trashed nodes")
        self._destination(parent, name or node.name)
        originals = []

        def gather(key):
            originals.append(key)
            if isinstance(self.node(key), Folder):
                for child in self.children(key):
                    gather(child.id)

        gather(id)
        mapping = {key: new_id if key == id else f"{new_id}/{key}" for key in originals}
        if any(not isinstance(key, str) or not key or ":" in key or key in self.nodes for key in mapping.values()):
            raise ValueError("Copy IDs must be new nonempty IDs without ':'")
        for key in originals:
            original = self.node(key)
            args = {"id": mapping[key], "name": (name or original.name) if key == id else original.name}
            if isinstance(original, Folder):
                args["children"] = ()
            self.nodes[mapping[key]] = replace(original, **args)
            self.parents[mapping[key]] = parent if key == id else mapping[self.parents[key]]

    def trash(self, id):
        self.node(id)
        if id == self.root or not self.visible(id):
            raise ValueError("Cannot trash root or an already trashed node")
        self.trashed[id] = self.parents[id]

    def restore(self, id):
        if id not in self.trashed:
            raise ValueError("Node is not in Trash")
        parent = self.trashed[id]
        self._destination(parent, self.node(id).name)
        del self.trashed[id]


@dataclass(frozen=True)
class Control:
    id: str
    label: str
    kind: str = "toggle"
    value: object = False
    options: tuple[str, ...] = ()
    minimum: float = 0
    maximum: float = 100

    def __post_init__(self):
        if not self.id or ":" in self.id or not self.label:
            raise ValueError("Controls need an ID without ':' and a label")
        if self.kind not in {"toggle", "slider", "choice", "text", "button"}:
            raise ValueError("Unknown control kind")
        from math import isfinite

        object.__setattr__(self, "options", tuple(self.options))
        if self.kind == "slider" and (not isfinite(self.minimum) or not isfinite(self.maximum)):
            raise ValueError("Slider bounds must be finite")
        if self.kind == "slider" and self.minimum >= self.maximum:
            raise ValueError("Slider minimum must be less than maximum")
        self.validate(self.value)

    def validate(self, value):
        from math import isfinite

        valid = {
            "toggle": lambda: isinstance(value, bool),
            "slider": lambda: (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and isfinite(value)
                and self.minimum <= value <= self.maximum
            ),
            "choice": lambda: isinstance(value, str) and value in self.options,
            "text": lambda: isinstance(value, str),
            "button": lambda: isinstance(value, bool),
        }[self.kind]()
        if not valid:
            raise ValueError(f"Invalid value for {self.id}: {value!r}")


@dataclass(frozen=True)
class SettingsPage:
    id: str
    title: str
    controls: tuple[Control, ...] = ()

    def __post_init__(self):
        if not self.id or ":" in self.id or not self.title:
            raise ValueError("Pages need an ID without ':' and a title")
        object.__setattr__(self, "controls", tuple(self.controls))
        if len({c.id for c in self.controls}) != len(self.controls):
            raise ValueError("Duplicate control IDs")


def starter_pages():
    return (
        SettingsPage(
            "appearance", "Appearance", (Control("theme", "Appearance", "choice", "light", ("light", "dark")),)
        ),
        SettingsPage(
            "wifi",
            "Wi-Fi",
            (Control("enabled", "Wi-Fi", value=True), Control("network", "Network name", "text", "Studio Network")),
        ),
        SettingsPage(
            "displays",
            "Displays",
            (
                Control("brightness", "Brightness", "slider", 70),
                Control("scale", "Text size", "choice", "Default", ("Larger", "Default")),
            ),
        ),
        SettingsPage(
            "sound",
            "Sound",
            (
                Control("volume", "Output volume", "slider", 60),
                Control("muted", "Mute", value=False),
                Control("test", "Test sound", "button", False),
            ),
        ),
    )


@dataclass(frozen=True)
class MacOSPreset:
    appearance: str = "light"
    wallpaper: str = "#5573B5"
    accent: str = "#1677EE"
    font: str | None = None
    font_size: int = 22
    clock: str = "Mon 9:41 AM"
    cursor_color: str = "#FFFFFF"
    cursor_size: float = 1.0
    icons: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        from faceless_champ.components import finite
        from PIL import ImageColor

        if self.appearance not in {"light", "dark"}:
            raise ValueError("appearance must be light or dark")
        for color in (self.wallpaper, self.accent, self.cursor_color, *self.icons.values()):
            ImageColor.getcolor(color, "RGBA")
        if finite(self.font_size, "font_size", 10) > 32:
            raise ValueError("font_size must be between 10 and 32; scale the viewport for larger UI")
        finite(self.cursor_size, "cursor_size", 0.1)
