"""Compiled OS tutorials with deterministic random-access playback."""

from __future__ import annotations

from bisect import bisect_right
from collections import OrderedDict
from copy import deepcopy
from dataclasses import replace
from math import ceil

from ..components import Component, finite
from .layout import geometry, listing
from .model import File, Folder, MacOSPreset, VirtualFileSystem, starter_pages
from .script import OSScript


class OSClip(Component):
    """A self-contained viewport. Configure before Scene.add, as with other components.

    bounds_for uses local design coordinates and original script time. Outer scene
    transforms apply to the complete viewport, including the cursor.
    """

    def __init__(
        self,
        filesystem=None,
        script=None,
        *,
        preset=None,
        pages=None,
        mode="desktop",
        width=1920,
        height=1080,
        source_start=0,
        cursor=True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.width = finite(width, "width", 960)
        self.height = finite(height, "height", 600)
        if mode not in {"desktop", "finder", "settings"}:
            raise ValueError("mode must be desktop, finder, or settings")
        self.mode = mode
        self.preset = deepcopy(preset or MacOSPreset())
        self.pages = tuple(deepcopy(starter_pages() if pages is None else pages))
        if not self.pages or len({p.id for p in self.pages}) != len(self.pages):
            raise ValueError("Settings pages must be nonempty with unique IDs")
        self.source_start = finite(source_start, "source_start", 0)
        self.cursor = bool(cursor)
        fs = deepcopy(filesystem or VirtualFileSystem(Folder("root", "Home")))
        script = deepcopy(script or OSScript())
        self.duration = script.duration
        if self.duration and self.source_start > self.duration:
            raise ValueError("source_start exceeds script duration")
        w, h = self.width, self.height
        if mode == "desktop":
            fw, fh = min(w - 80, 1180), min(h - 150, 740)
            finder = (40, 64, fw, fh)
            settings = (w - fw - 28, min(140, h - fh - 94), fw, fh)
        else:
            finder = settings = (16, 16, w - 32, h - 32)
        for box in (finder, settings):
            if box[2] < 900 or box[3] < 540:
                raise ValueError("Viewport is too small for system controls")
        state = {
            "fs": fs,
            "folder": fs.root,
            "history": [fs.root],
            "history_index": 0,
            "view": "icons",
            "search": "",
            "scroll": 0,
            "selected": None,
            "preview": None,
            "page": self.pages[0].id,
            "settings_scroll": 0,
            "values": {f"{p.id}:{c.id}": deepcopy(c.value) for p in self.pages for c in p.controls},
            "appearance": self.preset.appearance,
            "menu": None,
            "dialog": None,
            "order": ["finder", "settings", "preview"],
            "active": "settings" if mode == "settings" else "finder",
            "windows": {
                "finder": {"box": finder, "saved": finder, "visible": mode != "settings", "minimized": False},
                "settings": {"box": settings, "saved": settings, "visible": mode == "settings", "minimized": False},
                "preview": {
                    "box": (w / 2 - 380, h / 2 - 230, 760, 460),
                    "saved": None,
                    "visible": False,
                    "minimized": False,
                },
            },
        }
        if "appearance:theme" in state["values"]:
            state["values"]["appearance:theme"] = self.preset.appearance
        self._initial = deepcopy(state)
        self._records = []
        position = (w / 2, h - 120)
        for action in script.actions:
            before = deepcopy(state)
            boxes = self._geometry(state)
            target = self._target(action, state, boxes)
            if (
                action.kind != "wait"
                and target is None
                and not (action.kind == "move_cursor" and action.args.get("position") is not None)
                and not (
                    action.kind == "window" and action.args["operation"] in {"open", "restore"} and not action.cursor
                )
            ):
                raise ValueError(f"{action.kind}: target is hidden or unavailable: {action.target}")
            destination = position
            if target is not None:
                destination = boxes[target].center
                if target.startswith("control:"):
                    control = self._control(target)
                    box = boxes[target]
                    offset = 52 if control.kind == "toggle" else 109
                    destination = (box.right - offset, box.center[1])
                    if control.kind == "slider":
                        value = state["values"][target.removeprefix("control:")]
                        ratio = (value - control.minimum) / (control.maximum - control.minimum)
                        destination = (box.right - 200 + 160 * ratio, box.top + 38)
            if action.kind == "move_cursor" and action.args.get("position") is not None:
                coords = action.args["position"]
                if len(coords) != 2:
                    raise ValueError("Cursor position needs x and y")
                destination = tuple(finite(v, "cursor position", 0) for v in coords)
                if destination[0] > w or destination[1] > h:
                    raise ValueError("Cursor position outside viewport")
            end_position = destination
            if action.kind == "set_value" and target is not None and self._control(target).kind == "slider":
                control = self._control(target)
                control.validate(action.args["value"])
                ratio = (action.args["value"] - control.minimum) / (control.maximum - control.minimum)
                end_position = (boxes[target].right - 200 + 160 * ratio, boxes[target].top + 38)
            if action.kind in {"drag", "move"}:
                dest = self._file_target(action.args["destination"], boxes)
                if dest is None:
                    raise ValueError("Drag destination must be visible; navigate or scroll first")
                if dest:
                    end_position = boxes[dest].center
            if action.kind == "window" and action.args["operation"] == "move":
                old = state["windows"][action.target]["box"]
                xy = action.args.get("position")
                if xy is not None:
                    end_position = (destination[0] + xy[0] - old[0], destination[1] + xy[1] - old[1])
            self._apply(state, action, boxes)
            self._validate_layout(state)
            if not action.cursor:
                destination = end_position = position
            self._records.append((action, before, deepcopy(state), position, destination, end_position))
            position = end_position
        self._starts = tuple(r[0].at for r in self._records)
        self._final = deepcopy(state)
        # Assets are loaded once, so missing images fail before export and playback is host-independent.
        self._surface_cache = OrderedDict()
        self._images = {}
        from PIL import Image

        for node in fs.nodes.values():
            if isinstance(node, File) and node.image:
                with Image.open(node.image) as image:
                    self._images[str(node.image)] = image.convert("RGBA").copy()

    def _geometry(self, state):
        return geometry(state, self.width, self.height, self.mode, self.pages)

    @staticmethod
    def _file_target(id, boxes):
        return next((key for key in ("file:" + id, "sidebar:" + id, "desktop:" + id) if key in boxes), None)

    def _target(self, action, state, boxes):
        kind, id = action.kind, action.target
        if kind == "wait":
            return None
        if kind in {"open_folder", "select", "rename", "copy", "move", "drag", "trash", "restore", "preview"}:
            state["fs"].node(id)
            return self._file_target(id, boxes)
        if kind == "open_settings":
            if id not in {p.id for p in self.pages}:
                raise ValueError(f"Unknown settings page: {id}")
            return (
                ("page:" + id) if ("page:" + id) in boxes else ("dock:settings" if "dock:settings" in boxes else None)
            )
        if kind == "set_value":
            key = id if id.startswith("control:") else "control:" + id
            return key if key in boxes else None
        if kind == "window":
            if id not in state["windows"]:
                raise ValueError(f"Unknown window: {id}")
            op = action.args["operation"]
            if op in {"open", "restore"}:
                win = state["windows"][id]
                key = id + ":title" if win["visible"] and not win["minimized"] else "dock:" + id
            else:
                key = id + ":" + (op if op in {"close", "minimize", "maximize"} else "title")
            return key if key in boxes else None
        if id in boxes:
            return id
        if id is not None and id in state["fs"].nodes:
            return self._file_target(id, boxes)
        if kind == "move_cursor" and action.args.get("position") is not None:
            return None
        return None

    def _focus(self, state, name):
        if self.mode != "desktop" and name != self.mode and name != "preview":
            raise ValueError(f"{name} is unavailable in {self.mode}-only mode")
        win = state["windows"][name]
        win["visible"], win["minimized"] = True, False
        state["order"].remove(name)
        state["order"].append(name)
        state["active"] = name

    def _navigate(self, state, id, *, history=True):
        if id != "@trash" and (not isinstance(state["fs"].node(id), Folder) or not state["fs"].visible(id)):
            raise ValueError("Navigation requires an available folder")
        if history:
            state["history"] = state["history"][: state["history_index"] + 1] + [id]
            state["history_index"] += 1
        state.update(folder=id, scroll=0, search="", selected=None, menu=None)
        self._focus(state, "finder")

    def _control(self, id):
        id = id.removeprefix("control:")
        for p in self.pages:
            for c in p.controls:
                if id == f"{p.id}:{c.id}":
                    return c
        raise ValueError(f"Unknown setting: {id}")

    def _value(self, state, id, value):
        id = id.removeprefix("control:")
        self._control(id).validate(value)
        if id.split(":")[0] != state["page"]:
            raise ValueError("Control is on a different settings page")
        state["values"][id] = value
        if id == "appearance:theme":
            if value not in {"light", "dark"}:
                raise ValueError("Appearance theme must be light or dark")
            state["appearance"] = value

    def _apply(self, s, a, boxes):
        kind, id, args, fs = a.kind, a.target, a.args, s["fs"]
        if s["dialog"] and kind not in {"confirm", "wait", "move_cursor", "click"}:
            raise ValueError("Resolve the confirmation dialog before another action")
        if kind in {"wait", "move_cursor"}:
            return
        if kind == "open_folder":
            self._navigate(s, id)
        elif kind in {"back", "forward"}:
            i = s["history_index"] + (-1 if kind == "back" else 1)
            if not 0 <= i < len(s["history"]):
                raise ValueError(f"Cannot navigate {kind}")
            s["history_index"] = i
            self._navigate(s, s["history"][i], history=False)
        elif kind == "up":
            parent = fs.parents.get(s["folder"])
            if parent is None:
                raise ValueError("Current folder has no parent")
            self._navigate(s, parent)
        elif kind == "open_trash":
            self._navigate(s, "@trash")
        elif kind == "select":
            s["selected"] = id
        elif kind == "set_view":
            if args["value"] not in {"icons", "list"}:
                raise ValueError("view must be icons or list")
            s.update(view=args["value"], scroll=0)
        elif kind == "search":
            if not isinstance(args["text"], str):
                raise ValueError("Search requires text")
            s.update(search=args["text"], scroll=0)
        elif kind == "scroll":
            rows = args["rows"]
            if not isinstance(rows, int) or isinstance(rows, bool):
                raise ValueError("Scroll rows must be an integer")
            key = "scroll" if args["window"] == "finder" else "settings_scroll"
            if args["window"] not in {"finder", "settings"}:
                raise ValueError("Unknown scroll window")
            if key == "scroll":
                b = boxes["finder:content"]
                cols = max(1, int(b.width // 148)) if s["view"] == "icons" else 1
                visible = int(b.height // (118 if s["view"] == "icons" else 48))
                maximum = max(0, ceil(len(listing(s)) / cols) - visible)
            else:
                p = next(p for p in self.pages if p.id == s["page"])
                maximum = max(0, len(p.controls) - int((boxes["settings:content"].height - 24) // 86))
            s[key] = min(maximum, max(0, s[key] + rows))
        elif kind == "create_folder":
            fs.create_folder(s["folder"], args["id"], args["name"])
            s["selected"] = args["id"]
        elif kind == "rename":
            fs.rename(id, args["name"])
            s["selected"] = id
        elif kind == "copy":
            fs.copy(id, args["destination"], args["new_id"], args["name"])
        elif kind in {"move", "drag"}:
            fs.move(id, args["destination"])
            s["selected"] = None
        elif kind == "trash":
            if args.get("confirm"):
                s["dialog"] = {"id": id, "name": fs.node(id).name}
            else:
                fs.trash(id)
                s["selected"] = None
            s["menu"] = None
        elif kind == "restore":
            fs.restore(id)
        elif kind == "preview":
            if not isinstance(fs.node(id), File) or not fs.visible(id):
                raise ValueError("Preview requires an available file")
            s["preview"] = id
            self._focus(s, "preview")
        elif kind == "open_settings":
            s.update(page=id, settings_scroll=0)
            self._focus(s, "settings")
        elif kind == "set_value":
            self._value(s, id, args["value"])
        elif kind == "window":
            op, win = args["operation"], s["windows"][id]
            if op in {"open", "focus", "restore"}:
                if op == "restore" and win.get("maximized"):
                    win["box"], win["maximized"] = win["saved"], False
                self._focus(s, id)
            elif op in {"close", "minimize"}:
                win["visible" if op == "close" else "minimized"] = op != "close"
                visible = [n for n in s["order"] if s["windows"][n]["visible"] and not s["windows"][n]["minimized"]]
                s["active"] = visible[-1] if visible else None
            elif op == "maximize":
                if win.get("maximized"):
                    win["box"], win["maximized"] = win["saved"], False
                else:
                    win["saved"] = win["box"]
                    win["box"] = (
                        16,
                        46 if self.mode == "desktop" else 16,
                        self.width - 32,
                        self.height - (146 if self.mode == "desktop" else 32),
                    )
                    win["maximized"] = True
                self._focus(s, id)
            elif op in {"move", "resize"}:
                x, y, w, h = win["box"]
                if op == "move":
                    x, y = args["position"]
                else:
                    w, h = args["size"]
                win["box"] = tuple(finite(v, "window geometry", 0) for v in (x, y, w, h))
                self._focus(s, id)
            else:
                raise ValueError(f"Unknown window action: {op}")
        elif kind == "confirm":
            if not s["dialog"]:
                raise ValueError("No confirmation dialog is open")
            if args["accept"]:
                fs.trash(s["dialog"]["id"])
            s["dialog"] = None
        elif kind == "menu":
            if args["name"] != "File":
                raise ValueError("The starter menu is File")
            s["menu"] = {"position": (100, 40), "target": s["selected"]}
        elif kind == "type_text":
            if not isinstance(args["text"], str):
                raise ValueError("Typing requires text")
            if id == "finder:search":
                s.update(search=args["text"], scroll=0)
            else:
                if self._control(id).kind != "text":
                    raise ValueError("type_text requires a text control or finder:search")
                self._value(s, id, args["text"])
        elif kind == "click":
            self._click(s, a, boxes)
        else:
            raise ValueError(f"Unsupported OS action: {kind}")

    def _click(self, s, a, boxes):
        key = self._target(a, s, boxes)
        if key is None:
            raise ValueError("Click target is unavailable")
        args = a.args
        if args["button"] not in {"left", "right"} or args["count"] not in {1, 2}:
            raise ValueError("Supported clicks are left/right, single/double")
        if args["button"] == "right":
            id = key.split(":", 1)[1] if key.startswith(("file:", "desktop:")) else None
            if id is None:
                raise ValueError("Context menus require a file target")
            x, y = boxes[key].center
            s["menu"] = {"position": (min(x, self.width - 240), min(y, self.height - 180)), "target": id}
            s["selected"] = id
            return
        if key.startswith(("file:", "sidebar:", "desktop:")):
            id = key.split(":", 1)[1]
            s["selected"] = id
            if args["count"] == 2 or key.startswith("sidebar:"):
                kind = "open_folder" if isinstance(s["fs"].node(id), Folder) else "preview"
                self._apply(s, replace(a, kind=kind, target=id), boxes)
        elif key.startswith("control:"):
            control = self._control(key)
            if control.kind not in {"toggle", "button"}:
                raise ValueError("Use set_value or type_text for this control")
            self._value(s, key, not s["values"][key.removeprefix("control:")])
        elif key.startswith("page:"):
            self._apply(s, replace(a, kind="open_settings", target=key[5:]), boxes)
        elif key in {"finder:back", "finder:forward", "finder:up", "finder:trash"}:
            kind = key.split(":")[1]
            self._apply(s, replace(a, kind="open_trash" if kind == "trash" else kind), boxes)
        elif key == "finder:root":
            self._navigate(s, s["fs"].root)
        elif key == "finder:view":
            s.update(view="list" if s["view"] == "icons" else "icons", scroll=0)
        elif key.startswith("dock:"):
            name = key[5:]
            if name == "trash":
                self._navigate(s, "@trash")
            else:
                self._focus(s, name)
        elif key.startswith("dialog:"):
            self._apply(s, replace(a, kind="confirm", args={"accept": key == "dialog:confirm"}), boxes)
        elif key.startswith("menu:"):
            op, id = key[5:], s["menu"]["target"]
            s["menu"] = None
            if op != "dismiss":
                if id is None:
                    raise ValueError("Select a file before using this menu item")
                kind = ("open_folder" if isinstance(s["fs"].node(id), Folder) else "preview") if op == "open" else op
                self._apply(s, replace(a, kind=kind, target=id, args={}), boxes)
        elif key == "menubar:file":
            self._apply(s, replace(a, kind="menu", args={"name": "File"}), boxes)
        elif key.endswith((":close", ":minimize", ":maximize", ":title")):
            name, op = key.split(":")
            self._apply(
                s, replace(a, kind="window", target=name, args={"operation": "focus" if op == "title" else op}), boxes
            )
        elif key not in {"finder:search", "finder:content", "settings:content"}:
            raise ValueError(f"Use the semantic action for {key}")

    def _validate_layout(self, state):
        for name, win in state["windows"].items():
            if not win["visible"]:
                continue
            x, y, w, h = win["box"]
            minw, minh = (500, 300) if name == "preview" else (900, 540)
            if w < minw or h < minh or x < 0 or y < 0 or x + w > self.width or y + h > self.height:
                raise ValueError(f"{name} window does not fit the viewport")

    def _sample(self, time):
        time = finite(time, "time", 0)
        index = bisect_right(self._starts, time) - 1
        if index < 0:
            return self._initial, None, 0
        record = self._records[index]
        action = record[0]
        progress = min(1, (time - action.at) / action.duration)
        return record[2] if progress >= 0.6 else record[1], record, progress

    def state_at(self, time):
        """Return an independent logical state snapshot at original script time."""
        return deepcopy(self._sample(time)[0])

    def bounds_for(self, target, time=0):
        """Visible target bounds in viewport-local design pixels at script time."""
        from .drawing import display_state

        if not isinstance(target, str) or not target:
            raise ValueError("Target must be a nonempty string")
        state, _, _ = display_state(self, time)
        boxes = self._geometry(state)
        key = target if target in boxes else self._file_target(target, boxes)
        if key is None:
            raise ValueError(f"Target is not visible at {time:g}s: {target}")
        return boxes[key]

    def frame_key(self, age):
        return min(self.duration, self.source_start + age)

    def frame_image(self, age, factor=1):
        from .drawing import draw_frame

        return draw_frame(self, self.frame_key(age), factor)
