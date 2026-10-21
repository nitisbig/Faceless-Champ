"""Shared layout for drawing and hit targets, in viewport design pixels."""

from faceless_champ.layout import Bounds

from facelesschamp_kit.desktop.model import Folder


def rect(x, y, w, h):
    return Bounds(x, y, x + w, y + h)


def window_box(state, name):
    return rect(*state["windows"][name]["box"])


def listing(state):
    fs = state["fs"]
    nodes = [fs.node(id) for id in fs.trashed] if state["folder"] == "@trash" else fs.children(state["folder"])
    query = state["search"].casefold()
    return [node for node in nodes if query in node.name.casefold()]


def geometry(state, width, height, mode, pages):
    """Only fully visible targets are returned; later windows occlude earlier ones."""
    result = {}
    owners = {}

    def add(key, box, owner=None):
        if box.left < 0 or box.top < 0 or box.right > width or box.bottom > height:
            return
        result[key] = box
        owners[key] = owner

    if mode == "desktop":
        add("menubar:file", rect(100, 0, 75, 38))
        add("dock:finder", rect(width / 2 - 105, height - 84, 64, 64))
        add("dock:settings", rect(width / 2 - 32, height - 84, 64, 64))
        add("dock:trash", rect(width / 2 + 41, height - 84, 64, 64))
        for i, node in enumerate(state["fs"].children(state["fs"].root)[:6]):
            add("desktop:" + node.id, rect(width - 134, 70 + i * 116, 112, 102))
    for name in state["order"]:
        win = state["windows"][name]
        if not win["visible"] or win["minimized"]:
            continue
        b = window_box(state, name)
        # Remove targets covered even partly by the top window.
        for key, box in list(result.items()):
            if box.left < b.right and box.right > b.left and box.top < b.bottom and box.bottom > b.top:
                del result[key]
        x, y, w, h = win["box"]
        add(name + ":title", rect(x + 120, y, w - 140, 46), name)
        for i, control in enumerate(("close", "minimize", "maximize")):
            add(name + ":" + control, rect(x + 16 + i * 27, y + 15, 18, 18), name)
        if name == "preview":
            continue
        if name == "finder":
            for key, dx, tw in [
                ("back", 208, 40),
                ("forward", 254, 40),
                ("up", 300, 40),
                ("view", 354, 95),
                ("new", 458, 100),
            ]:
                add("finder:" + key, rect(x + dx, y + 55, tw, 36), name)
            add("finder:search", rect(x + w - 270, y + 55, 246, 36), name)
            add("finder:root", rect(x + 14, y + 106, 170, 38), name)
            folders = [n for n in state["fs"].children(state["fs"].root) if isinstance(n, Folder)][:5]
            for i, node in enumerate(folders):
                add("sidebar:" + node.id, rect(x + 14, y + 154 + i * 44, 170, 38), name)
            add("finder:trash", rect(x + 14, y + h - 62, 170, 38), name)
            content = rect(x + 206, y + 110, w - 226, h - 156)
            add("finder:content", content, name)
            cols = max(1, int(content.width // 148)) if state["view"] == "icons" else 1
            step = 118 if state["view"] == "icons" else 48
            nodes = listing(state)
            for index, node in enumerate(nodes):
                row, col = divmod(index, cols)
                top = content.top + (row - state["scroll"]) * step
                if top >= content.top and top + step <= content.bottom:
                    box = rect(content.left + col * content.width / cols, top, content.width / cols, step)
                    add("file:" + node.id, box, name)
        if name == "settings":
            for i, page in enumerate(pages):
                if y + 110 + i * 48 + 40 < y + h - 20:
                    add("page:" + page.id, rect(x + 16, y + 110 + i * 48, 188, 40), name)
            add("settings:content", rect(x + 228, y + 100, w - 252, h - 126), name)
            page = next(p for p in pages if p.id == state["page"])
            for i, control in enumerate(page.controls):
                top = y + 124 + (i - state["settings_scroll"]) * 86
                if top >= y + 100 and top + 72 <= y + h - 26:
                    add(f"control:{page.id}:{control.id}", rect(x + 242, top, w - 280, 72), name)
    if state["menu"]:
        x, y = state["menu"]["position"]
        for key, box in list(result.items()):
            if box.left < x + 220 and box.right > x and box.top < y + 160 and box.bottom > y:
                del result[key]
        for i, name in enumerate(("open", "preview", "trash", "dismiss")):
            add("menu:" + name, rect(x, y + i * 40, 220, 40))
    if state["dialog"]:
        result = {}
        x, y = width / 2 - 220, height / 2 - 90
        add("dialog:cancel", rect(x + 30, y + 110, 160, 40))
        add("dialog:confirm", rect(x + 240, y + 110, 160, 40))
    return result
