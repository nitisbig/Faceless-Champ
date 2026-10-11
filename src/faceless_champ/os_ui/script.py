"""Semantic action authoring. Times are local to the OS viewport."""

from copy import deepcopy
from dataclasses import dataclass

from ..components import finite


@dataclass(frozen=True)
class Action:
    kind: str
    target: str | None
    at: float
    duration: float
    cursor: bool
    args: dict


class OSScript:
    def __init__(self):
        self._actions = []

    @property
    def actions(self):
        return tuple(deepcopy(self._actions))

    @property
    def duration(self):
        return max((a.at + a.duration for a in self._actions), default=0)

    def _add(self, kind, target=None, *, at=None, duration=1, cursor=True, **args):
        if target is not None and (not isinstance(target, str) or not target):
            raise ValueError("Action targets must be nonempty strings")
        allowed = {
            "set_view": {"value"},
            "search": {"text"},
            "scroll": {"rows", "window"},
            "create_folder": {"id", "name"},
            "rename": {"name"},
            "copy": {"destination", "new_id", "name"},
            "move": {"destination"},
            "drag": {"destination"},
            "trash": {"confirm"},
            "set_value": {"value"},
            "window": {"operation", "position", "size"},
            "move_cursor": {"position"},
            "click": {"button", "count"},
            "type_text": {"text"},
            "confirm": {"accept"},
            "menu": {"name"},
        }.get(kind, set())
        if set(args) - allowed:
            raise TypeError(f"Unexpected {kind} options: {', '.join(sorted(set(args) - allowed))}")
        at = self.duration if at is None else finite(at, "at", 0)
        duration = finite(duration, "duration", 0.001)
        if self._actions and at < self.duration - 1e-9:
            raise ValueError("OS actions must be chronological and cannot overlap")
        self._actions.append(Action(kind, target, at, duration, bool(cursor), deepcopy(args)))
        return self

    def wait(self, duration=1):
        return self._add("wait", duration=duration, cursor=False)

    def open_folder(self, id, **timing):
        return self._add("open_folder", id, **timing)

    def back(self, **timing):
        return self._add("back", "finder:back", **timing)

    def forward(self, **timing):
        return self._add("forward", "finder:forward", **timing)

    def up(self, **timing):
        return self._add("up", "finder:up", **timing)

    def select(self, id, **timing):
        return self._add("select", id, **timing)

    def set_view(self, view, **timing):
        return self._add("set_view", "finder:view", value=view, **timing)

    def search(self, text, **timing):
        return self._add("search", "finder:search", text=text, **timing)

    def scroll(self, rows=1, *, window="finder", **timing):
        return self._add("scroll", f"{window}:content", rows=rows, window=window, **timing)

    def create_folder(self, id, name, **timing):
        return self._add("create_folder", "finder:new", id=id, name=name, **timing)

    def rename(self, id, name, **timing):
        return self._add("rename", id, name=name, **timing)

    def copy(self, id, destination, new_id, *, name=None, **timing):
        return self._add("copy", id, destination=destination, new_id=new_id, name=name, **timing)

    def move(self, id, destination, **timing):
        return self._add("move", id, destination=destination, **timing)

    def drag(self, id, destination, **timing):
        return self._add("drag", id, destination=destination, **timing)

    def trash(self, id, *, confirm=False, **timing):
        return self._add("trash", id, confirm=confirm, **timing)

    def restore(self, id, **timing):
        return self._add("restore", id, **timing)

    def open_trash(self, **timing):
        return self._add("open_trash", "finder:trash", **timing)

    def preview(self, id, **timing):
        return self._add("preview", id, **timing)

    def open_settings(self, page="appearance", **timing):
        return self._add("open_settings", page, **timing)

    def set_value(self, control, value, **timing):
        return self._add("set_value", control, value=value, **timing)

    def window(self, id, action, **kwargs):
        timing = {key: kwargs.pop(key) for key in ("at", "duration", "cursor") if key in kwargs}
        return self._add("window", id, operation=action, **kwargs, **timing)

    def move_cursor(self, target=None, *, position=None, **timing):
        return self._add("move_cursor", target, position=position, **timing)

    def click(self, target, *, button="left", count=1, **timing):
        return self._add("click", target, button=button, count=count, **timing)

    def double_click(self, target, **timing):
        return self.click(target, count=2, **timing)

    def right_click(self, target, **timing):
        return self.click(target, button="right", **timing)

    def type_text(self, target, text, **timing):
        return self._add("type_text", target, text=text, **timing)

    def confirm(self, accept=True, **timing):
        return self._add("confirm", "dialog:confirm" if accept else "dialog:cancel", accept=accept, **timing)

    def menu(self, name="File", **timing):
        return self._add("menu", "menubar:file", name=name, **timing)
