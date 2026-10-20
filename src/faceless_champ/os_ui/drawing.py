"""Original, scalable macOS-style artwork drawn with Pillow."""

import math
from copy import deepcopy
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from ..typography import DEFAULT_FONT, load_font
from .layout import geometry, listing
from .model import Folder


@lru_cache(maxsize=64)
def font(path, size):
    return load_font(path or DEFAULT_FONT, size)


def palette(appearance, accent):
    dark = appearance == "dark"
    return {
        "bg": "#25272D" if dark else "#F8F9FC",
        "sidebar": "#30333B" if dark else "#E9EDF5",
        "chrome": "#353841" if dark else "#EEF0F5",
        "text": "#F2F4F8" if dark else "#252B38",
        "muted": "#AEB8C9" if dark else "#647188",
        "line": "#474C58" if dark else "#D4DAE5",
        "field": "#454A55" if dark else "#FFFFFF",
        "accent": accent,
    }


class Painter:
    def __init__(self, image, clip, state, factor):
        self.image, self.clip, self.state, self.f = image, clip, state, factor
        self.draw = ImageDraw.Draw(image)
        self.colors = palette(state["appearance"], clip.preset.accent)

    def box(self, box):
        if hasattr(box, "left"):
            box = (box.left, box.top, box.right, box.bottom)
        return tuple(round(v * self.f) for v in box)

    def rect(self, box, fill, radius=8, outline=None, width=1):
        self.draw.rounded_rectangle(
            self.box(box),
            radius=max(0, round(radius * self.f)),
            fill=fill,
            outline=outline,
            width=max(1, round(width * self.f)),
        )

    def line(self, points, fill, width=2):
        self.draw.line(
            [(round(x * self.f), round(y * self.f)) for x, y in points], fill=fill, width=max(1, round(width * self.f))
        )

    def text(self, xy, text, *, size=None, color=None, max_width=None, center=False):
        size = (size or 22) * self.clip.preset.font_size / 22
        face = font(self.clip.preset.font, max(1, round(size * self.f)))
        text = str(text).replace("\n", " ")
        if max_width is not None:
            limit = max_width * self.f
            if self.draw.textlength(text, font=face) > limit:
                while text and self.draw.textlength(text + "…", font=face) > limit:
                    text = text[:-1]
                text += "…"
        x, y = xy
        if center:
            x -= self.draw.textlength(text, font=face) / self.f / 2
        self.draw.text(
            (round(x * self.f), round(y * self.f)), text, font=face, fill=color or self.colors["text"], anchor="lt"
        )

    def icon(self, name, x, y, size=48):
        p = self.clip.preset
        color = p.icons.get(name, "#54ACF5" if name in {"folder", "finder"} else "#8193AF")
        if name in {"folder", "finder"}:
            self.rect((x, y + size * 0.15, x + size * 0.48, y + size * 0.4), color, 4)
            self.rect((x, y + size * 0.28, x + size, y + size * 0.9), color, 6)
            self.line([(x + 5, y + size * 0.4), (x + size - 5, y + size * 0.4)], "#A8D9FF", 2)
        elif name == "settings":
            for i in range(8):
                a = i * math.pi / 4
                cx, cy = x + size / 2, y + size / 2
                self.line(
                    [
                        (cx + math.cos(a) * size * 0.27, cy + math.sin(a) * size * 0.27),
                        (cx + math.cos(a) * size * 0.46, cy + math.sin(a) * size * 0.46),
                    ],
                    color,
                    size * 0.14,
                )
            self.draw.ellipse(
                self.box((x + size * 0.18, y + size * 0.18, x + size * 0.82, y + size * 0.82)), fill=color
            )
            self.draw.ellipse(
                self.box((x + size * 0.35, y + size * 0.35, x + size * 0.65, y + size * 0.65)),
                fill=self.colors["chrome"],
            )
        elif name == "trash":
            self.rect((x + size * 0.2, y + size * 0.25, x + size * 0.8, y + size * 0.9), color, 5)
            self.line([(x + size * 0.1, y + size * 0.2), (x + size * 0.9, y + size * 0.2)], color, 5)
            self.line([(x + size * 0.4, y + size * 0.1), (x + size * 0.6, y + size * 0.1)], color, 4)
            for dx in (0.38, 0.62):
                self.line([(x + size * dx, y + size * 0.38), (x + size * dx, y + size * 0.76)], "#D9E1EE", 2)
        else:
            self.rect(
                (x + size * 0.16, y + size * 0.05, x + size * 0.82, y + size * 0.95), "#FDFEFF", 4, outline="#9CAEC6"
            )
            for dy in (0.4, 0.55, 0.7):
                self.line([(x + size * 0.28, y + size * dy), (x + size * 0.68, y + size * dy)], color, 2)


def _surface(clip, state, factor):
    w, h = clip.width, clip.height
    image = Image.new("RGBA", (max(1, round(w * factor)), max(1, round(h * factor))))
    p = Painter(image, clip, state, factor)
    c = p.colors
    if clip.mode == "desktop":
        p.rect((0, 0, w, h), clip.preset.wallpaper, 0)
        # Broad translucent hills give the authored wallpaper depth, without external assets.
        wash = Image.new("RGBA", image.size)
        d = ImageDraw.Draw(wash)
        d.ellipse(p.box((-w * 0.2, h * 0.35, w * 1.2, h * 1.9)), fill=(89, 143, 203, 100))
        d.ellipse(p.box((w * 0.3, h * 0.45, w * 1.5, h * 1.5)), fill=(41, 66, 121, 100))
        image.alpha_composite(wash)
        p.rect((0, 0, w, 38), c["chrome"], 0)
        p.text((22, 8), "●", size=20)
        p.text((55, 8), "Finder" if state["active"] != "settings" else "Settings", size=18)
        p.text((137, 8), "File   Edit   View   Go   Window   Help", size=18)
        p.text((w - 245, 8), clip.preset.clock, size=18, max_width=225)
        p.rect((w / 2 - 120, h - 98, w / 2 + 120, h - 10), c["chrome"], 22)
        for name, x in [("finder", w / 2 - 98), ("settings", w / 2 - 25), ("trash", w / 2 + 48)]:
            p.icon(name, x, h - 77, 50)
            if name in state["windows"] and state["windows"][name]["visible"]:
                p.rect((x + 22, h - 20, x + 28, h - 15), c["muted"], 3)
        for i, node in enumerate(state["fs"].children(state["fs"].root)[:6]):
            x, y = w - 120, 70 + i * 116
            p.icon("folder" if isinstance(node, Folder) else "file", x + 26, y, 54)
            p.text((x + 50, y + 66), node.name, size=18, color="white", max_width=112, center=True)
    for name in state["order"]:
        win = state["windows"][name]
        if not win["visible"] or win["minimized"]:
            continue
        x, y, ww, hh = win["box"]
        shadow = Image.new("RGBA", image.size)
        ImageDraw.Draw(shadow).rounded_rectangle(
            p.box((x, y + 7, x + ww, y + hh + 7)), radius=round(16 * factor), fill=(0, 0, 0, 65)
        )
        image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(max(1, 7 * factor))))
        p.rect((x, y, x + ww, y + hh), c["bg"], 14, c["line"])
        p.rect((x + 1, y + 1, x + ww - 1, y + 48), c["chrome"], 13)
        p.rect((x + 1, y + 28, x + ww - 1, y + 48), c["chrome"], 0)
        for i, color in enumerate(("#FF6058", "#FFBD2E", "#28C840")):
            p.draw.ellipse(
                p.box((x + 16 + i * 27, y + 15, x + 34 + i * 27, y + 33)),
                fill=color if state["active"] == name else c["muted"],
            )
        title = {"finder": "Finder", "settings": "System Settings", "preview": "Quick Look"}[name]
        if name == "finder":
            title = "Trash" if state["folder"] == "@trash" else state["fs"].node(state["folder"]).name
        p.text((x + ww / 2, y + 13), title, size=20, center=True, max_width=ww - 280)
        # Draw full window contents even where other windows later cover them.
        local = dict(state, order=[name], menu=None, dialog=None)
        boxes = geometry(local, w, h, clip.mode, clip.pages)
        if name == "finder":
            _finder(p, state, boxes, x, y, ww, hh)
        elif name == "settings":
            _settings(p, state, boxes, x, y, ww, hh)
        elif state["preview"]:
            node = state["fs"].node(state["preview"])
            p.text((x + 30, y + 72), node.name, size=26, max_width=ww - 60)
            if node.image:
                asset = clip._images[str(node.image)]
                fitted = ImageOps.contain(asset, (round((ww - 64) * factor), round((hh - 142) * factor)))
                image.alpha_composite(
                    fitted, (round((x + ww / 2) * factor - fitted.width / 2), round((y + 120) * factor))
                )
            else:
                for i, line in enumerate(node.text.splitlines()[: int((hh - 150) // 30)]):
                    p.text((x + 30, y + 118 + i * 30), line, size=20, max_width=ww - 60)
    if state["menu"]:
        x, y = state["menu"]["position"]
        p.rect((x, y, x + 220, y + 160), c["field"], 9, c["line"])
        for i, label in enumerate(("Open", "Quick Look", "Move to Trash", "Dismiss")):
            p.text((x + 18, y + i * 40 + 10), label, size=19)
    if state["dialog"]:
        dim = Image.new("RGBA", image.size, (0, 0, 0, 65))
        image.alpha_composite(dim)
        x, y = w / 2 - 220, h / 2 - 90
        p.rect((x, y, x + 440, y + 180), c["bg"], 16)
        p.text((x + 24, y + 28), "Move to Trash?", size=25)
        p.text((x + 24, y + 68), state["dialog"]["name"], size=19, max_width=390)
        for dx, label in ((30, "Cancel"), (240, "Move to Trash")):
            p.rect((x + dx, y + 110, x + dx + 160, y + 150), c["accent"] if dx == 240 else c["chrome"])
            p.text((x + dx + 80, y + 121), label, size=17, center=True, color="white" if dx == 240 else c["text"])
    return image


def _finder(p, s, boxes, x, y, w, h):
    c = p.colors
    p.rect((x + 1, y + 48, x + 194, y + h - 14), c["sidebar"], 0)
    labels = {
        "finder:back": "‹",
        "finder:forward": "›",
        "finder:up": "↑",
        "finder:view": "List" if s["view"] == "icons" else "Icons",
        "finder:new": "+ Folder",
        "finder:root": "Home",
        "finder:trash": "Trash",
    }
    for key, b in boxes.items():
        if key in labels or key.startswith("sidebar:"):
            sidebar = key.startswith("sidebar:") or key in {"finder:root", "finder:trash"}
            label = s["fs"].node(key[8:]).name if key.startswith("sidebar:") else labels[key]
            if not sidebar:
                p.rect(b, c["field"], 7, c["line"])
            p.text((b.left + 12, b.top + 9), label, size=18, max_width=b.width - 20)
    b = boxes["finder:search"]
    p.rect(b, c["field"], 7, c["line"])
    p.text(
        (b.left + 12, b.top + 9),
        s["search"] or "Search this folder",
        size=18,
        color=c["text"] if s["search"] else c["muted"],
        max_width=b.width - 24,
    )
    content = boxes["finder:content"]
    if not listing(s):
        p.text((content.center[0], content.top + 90), "No items", color=c["muted"], center=True)
    for key, b in boxes.items():
        if not key.startswith("file:"):
            continue
        node = s["fs"].node(key[5:])
        selected = s["selected"] == node.id
        if selected:
            p.rect((b.left + 3, b.top + 2, b.right - 3, b.bottom - 4), c["accent"], 9)
        if s["view"] == "icons":
            p.icon("folder" if isinstance(node, Folder) else "file", b.center[0] - 27, b.top + 9, 54)
            p.text(
                (b.center[0], b.top + 79),
                node.name,
                size=18,
                center=True,
                max_width=b.width - 14,
                color="white" if selected else c["text"],
            )
        else:
            p.icon("folder" if isinstance(node, Folder) else "file", b.left + 10, b.top + 6, 30)
            p.text(
                (b.left + 55, b.top + 14),
                node.name,
                size=19,
                max_width=b.width - 180,
                color="white" if selected else c["text"],
            )
            p.text(
                (b.right - 110, b.top + 14),
                "Folder" if isinstance(node, Folder) else "Document",
                size=16,
                color="white" if selected else c["muted"],
            )
    trail = []
    id = s["folder"]
    if id == "@trash":
        trail = ["Trash"]
    else:
        while id is not None:
            trail.insert(0, s["fs"].node(id).name)
            id = s["fs"].parents[id]
    p.line([(x + 194, y + h - 40), (x + w - 1, y + h - 40)], c["line"], 1)
    p.text((x + 212, y + h - 28), "  ›  ".join(trail), size=16, color=c["muted"], max_width=w - 345)
    p.text((x + w - 110, y + h - 28), f"{len(listing(s))} items", size=16, color=c["muted"])
    # A proportional scrollbar communicates clipped content.
    columns = max(1, int(content.width // 148)) if s["view"] == "icons" else 1
    visible = max(1, int(content.height // (118 if s["view"] == "icons" else 48)))
    rows = math.ceil(len(listing(s)) / columns)
    if rows > visible:
        thumb = min(content.height, max(20, content.height * visible / rows))
        progress = min(1, max(0, s["scroll"] / (rows - visible)))
        top = content.top + (content.height - thumb) * progress
        p.rect(
            (
                x + w - 12,
                top,
                x + w - 7,
                min(content.bottom, top + thumb),
            ),
            c["muted"],
            3,
        )


def _settings(p, s, boxes, x, y, w, h):
    c = p.colors
    p.rect((x + 1, y + 48, x + 220, y + h - 14), c["sidebar"], 0)
    p.text((x + 22, y + 69), "Settings", size=24)
    for page in p.clip.pages:
        key = "page:" + page.id
        if key not in boxes:
            continue
        b = boxes[key]
        if page.id == s["page"]:
            p.rect(b, c["accent"], 8)
        p.text(
            (b.left + 12, b.top + 11),
            page.title,
            size=18,
            max_width=b.width - 24,
            color="white" if page.id == s["page"] else c["text"],
        )
    page = next(page for page in p.clip.pages if page.id == s["page"])
    p.text((x + 245, y + 73), page.title, size=27, max_width=w - 280)
    for control in page.controls:
        key = f"control:{page.id}:{control.id}"
        if key not in boxes:
            continue
        b = boxes[key]
        value = s["values"][key.removeprefix("control:")]
        p.rect(b, c["field"], 10, c["line"])
        p.text((b.left + 16, b.top + 24), control.label, size=20, max_width=b.width * 0.46)
        xx, yy = b.right - 200, b.top + 24
        if control.kind == "toggle":
            p.rect((b.right - 80, yy, b.right - 24, yy + 29), c["accent"] if value else c["muted"], 15)
            dx = b.right - 51 if value else b.right - 77
            p.draw.ellipse(p.box((dx, yy + 3, dx + 23, yy + 26)), fill="white")
        elif control.kind == "slider":
            ratio = (value - control.minimum) / (control.maximum - control.minimum)
            p.line([(xx, yy + 14), (b.right - 40, yy + 14)], c["line"], 5)
            p.line([(xx, yy + 14), (xx + 160 * ratio, yy + 14)], c["accent"], 5)
            p.draw.ellipse(p.box((xx + 160 * ratio - 9, yy + 5, xx + 160 * ratio + 9, yy + 23)), fill=c["accent"])
            p.text((xx, b.top + 5), f"{value:g}", size=14, color=c["muted"])
        else:
            p.rect((xx, b.top + 15, b.right - 18, b.bottom - 15), c["chrome"], 6)
            label = ("Activated" if value else "Run") if control.kind == "button" else str(value)
            if control.kind == "choice":
                label += "  ⌄"
            p.text((xx + 10, b.top + 26), label, size=18, max_width=164)


def _smooth(x):
    x = min(1, max(0, x))
    return x * x * (3 - 2 * x)


def _lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def display_state(clip, time):
    state, record, progress = clip._sample(time)
    if (
        record
        and record[0].kind == "window"
        and record[0].args["operation"] in {"move", "resize", "maximize", "restore"}
    ):
        name = record[0].target
        before, after = record[1], record[2]
        state = deepcopy(state)
        state["windows"][name]["box"] = _lerp(
            before["windows"][name]["box"], after["windows"][name]["box"], _smooth((progress - 0.35) / 0.55)
        )
    if record and record[0].kind == "scroll":
        state = deepcopy(state)
        key = "scroll" if record[0].args["window"] == "finder" else "settings_scroll"
        state[key] = record[1][key] + (record[2][key] - record[1][key]) * _smooth((progress - 0.35) / 0.55)
    if record and record[0].kind == "set_value":
        id = record[0].target.removeprefix("control:")
        if clip._control(id).kind == "slider":
            state = deepcopy(state)
            state["values"][id] = record[1]["values"][id] + (
                record[2]["values"][id] - record[1]["values"][id]
            ) * _smooth((progress - 0.35) / 0.55)
    return state, record, progress


def _cached_surface(clip, state, factor):
    stable = state is clip._initial or any(state is r[1] or state is r[2] for r in clip._records)
    if not stable:
        return _surface(clip, state, factor)
    key = (id(state), factor)
    cache = clip._surface_cache
    if key not in cache:
        cache[key] = _surface(clip, state, factor)
        while len(cache) > 4:
            cache.popitem(last=False)
    cache.move_to_end(key)
    return cache[key].copy()


def draw_frame(clip, time, factor):
    state, record, progress = display_state(clip, time)
    image = _cached_surface(clip, state, factor)
    if record:
        a, before, _after, start, target, end = record
        if (
            a.kind != "window"
            and 0.6 <= progress < 0.82
            and a.kind not in {"wait", "move_cursor", "scroll", "type_text"}
        ):
            image = Image.blend(_cached_surface(clip, before, factor), image, _smooth((progress - 0.6) / 0.22))
        if a.kind in {"type_text", "search", "rename", "create_folder"} and 0.35 <= progress < 0.6:
            text = a.args.get("text", a.args.get("name", ""))
            typed = text[: max(1, round(len(text) * (progress - 0.35) / 0.25))]
            if a.kind in {"type_text", "search"}:
                view = deepcopy(before)
                if a.target == "finder:search":
                    view["search"] = typed
                else:
                    view["values"][a.target.removeprefix("control:")] = typed
                image = _surface(clip, view, factor)
            else:
                p = Painter(image, clip, state, factor)
                x, y = clip.width / 2 - 210, clip.height / 2 - 50
                p.rect((x, y, x + 420, y + 100), p.colors["field"], 12, clip.preset.accent, 2)
                p.text((x + 18, y + 16), "Rename" if a.kind == "rename" else "New folder", size=16)
                p.text((x + 18, y + 49), typed + "|", size=24, max_width=380)
        pos = _lerp(start, target, _smooth(progress / 0.35))
        if a.kind in {"drag", "move"} or (a.kind == "window" and a.args["operation"] == "move"):
            pos = _lerp(target, end, _smooth((progress - 0.35) / 0.25)) if progress >= 0.35 else pos
            if a.kind in {"drag", "move"} and 0.35 <= progress < 0.6:
                p = Painter(image, clip, state, factor)
                p.icon("folder" if isinstance(before["fs"].node(a.target), Folder) else "file", pos[0] + 12, pos[1], 38)
        if a.kind == "set_value" and clip._control(a.target).kind == "slider" and progress >= 0.35:
            pos = _lerp(target, end, _smooth((progress - 0.35) / 0.55))
        if not a.cursor:
            pos = start
    else:
        pos = (clip.width / 2, clip.height - 120)
    if clip.cursor:
        p = Painter(image, clip, state, factor)
        if record and record[0].cursor and 0.35 <= progress < 0.6 and record[0].kind not in {"move_cursor", "wait"}:
            pulse = (progress - 0.35) / 0.25
            radius = 12 + 22 * pulse
            p.draw.ellipse(
                p.box((pos[0] - radius, pos[1] - radius, pos[0] + radius, pos[1] + radius)),
                outline=clip.preset.accent,
                width=max(1, round(3 * factor)),
            )
            if record[0].kind == "click" and record[0].args.get("count") == 2:
                p.draw.ellipse(
                    p.box((pos[0] - radius - 8, pos[1] - radius - 8, pos[0] + radius + 8, pos[1] + radius + 8)),
                    outline=clip.preset.accent,
                    width=max(1, round(factor)),
                )
        # Outline hovered controls, leaving content containers and desktop decoration alone.
        boxes = clip._geometry(state)
        for key, b in reversed(list(boxes.items())):
            if b.left <= pos[0] <= b.right and b.top <= pos[1] <= b.bottom and not key.endswith((":content", ":title")):
                p.rect(b, None, 6, clip.preset.accent, 1)
                break
        x, y = pos
        size = clip.preset.cursor_size
        points = [
            (x + dx * size, y + dy * size)
            for dx, dy in ((0, 0), (1, 29), (8, 22), (15, 36), (21, 33), (14, 20), (25, 19))
        ]
        p.draw.polygon(
            [(round(xx * factor), round(yy * factor)) for xx, yy in points],
            fill=clip.preset.cursor_color,
            outline="#111827",
            width=max(1, round(2 * factor)),
        )
    return image
