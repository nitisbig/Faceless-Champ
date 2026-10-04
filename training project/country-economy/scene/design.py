"""Country Economy art direction; all drawing and animation use the main library."""

from __future__ import annotations

from pathlib import Path

from faceless_champ import (
    Arrow,
    Canvas,
    ColorScheme,
    Draw,
    FadeIn,
    ImageSlot,
    Number,
    Rectangle,
    Scene,
    SlideIn,
    Text,
)

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[1]
SERIF = ROOT / "assets/fonts/CormorantGaramond[wght].ttf"
SANS = ROOT / "assets/fonts/DMSans[opsz,wght].ttf"
SYMBOLS = ROOT / "assets/icons/MaterialSymbolsOutlined[FILL,GRAD,opsz,wght].ttf"
WHITE, RUST, TAUPE, IVORY, INK = "#FFFFFF", "#C15F3C", "#B1ADA1", "#F4F3EE", "#292724"
CANVAS = Canvas(1920, 1080, WHITE)
SCHEME = ColorScheme(
    name="country-economy",
    background=WHITE,
    surface=IVORY,
    text=INK,
    muted=TAUPE,
    axis=TAUPE,
    border=TAUPE,
    grid=IVORY,
    primary=RUST,
    secondary=TAUPE,
    tertiary=INK,
    highlight=RUST,
)
GLYPHS = {
    "government": "\ue84f",
    "wallet": "\ue850",
    "school": "\ue80c",
    "hospital": "\ue548",
    "road": "\uef3b",
    "ship": "\ue558",
    "factory": "\uebbc",
    "people": "\uf233",
    "world": "\ue80b",
    "exchange": "\ueb70",
    "down": "\ue8e3",
    "up": "\ue8e5",
    "deal": "\uebcb",
    "tax": "\uef6e",
    "work": "\ue8f9",
    "warning": "\ue002",
    "money": "\uef63",
    "military": "\uea3f",
    "food": "\ue56c",
    "energy": "\uea0b",
    "clock": "\ue192",
    "savings": "\ue2eb",
    "percent": "\ueb58",
    "bond": "\ue873",
    "basket": "\ue8cb",
    "person": "\ue7fd",
}


def text(value, x, y, size=34, *, color=INK, serif=False, weight=400, **kwargs):
    return Text(
        value,
        font=SERIF if serif else SANS,
        font_weight=weight,
        font_size=size,
        color=color,
        position=(x, y),
        align="center",
        **kwargs,
    )


def number(value, x, y, size=100, *, color=RUST, **kwargs):
    return Number(
        value, font=SERIF, font_weight=500, font_size=size, color=color, position=(x, y), align="center", **kwargs
    )


def icon(name, x, y, size=90, color=RUST):
    return Text(GLYPHS[name], font=SYMBOLS, font_size=size, color=color, position=(x, y))


def card(title, x, y, *, symbol=None, detail=None, width=600, height=210, accent=False):
    items = [
        Rectangle(
            width=width,
            height=height,
            corner_radius=16,
            fill=IVORY,
            stroke=RUST if accent else None,
            stroke_width=2,
            position=(x, y),
        )
    ]
    if symbol:
        items.append(icon(symbol, x - width / 2 + 62, y, 66))
        tx = x + 45
    else:
        tx = x
    items.append(text(title, tx, y - (22 if detail else 0), 36 if width < 520 else 42, serif=True))
    if detail:
        items.append(text(detail, tx, y + 44, 28))
    return items


def connector(a, b, *, color=RUST, width=3):
    return Arrow(a, b, stroke=color, stroke_width=width, tip_size=17)


def image(n, x, y, width, height, mode):
    return ImageSlot(
        PROJECT / "image" / f"{n}.png",
        mode=mode,
        width=width,
        height=height,
        fit="cover",
        position=(x, y),
        placeholder_font=SANS,
        placeholder_font_size=42,
    )


class Board(Scene):
    """A chapter composition on a local clock derived from original cue indices."""

    def __init__(self, track, chapter, image_mode):
        super().__init__(CANVAS)
        self.track, self.chapter, self.image_mode = track, chapter, image_mode
        self.start, self.end = chapter["start"], chapter["end"]
        self.events = []

    def time_at(self, cue):
        local = self.track.cue(cue).start - self.start
        if not 0 <= local < self.end - self.start:
            raise ValueError(f"Cue {cue} is outside chapter {self.chapter['id']}")
        return local

    def show(self, cue, *items, motion=False, duration=0.35, note=None):
        local = self.time_at(cue)
        duration = min(duration, self.end - self.start - local)
        with self.at(local):
            self.play(*(SlideIn(item, distance=22) if motion else FadeIn(item) for item in items), run_time=duration)
        self.events.append(
            {
                "cue": cue,
                "time": self.track.cue(cue).start,
                "end": self.start + local + duration,
                "label": note or "visual reveal",
            }
        )
        return items

    def draw(self, cue, *items):
        with self.at(self.time_at(cue)):
            self.play(*(Draw(item) for item in items), run_time=0.45)
        self.events.append(
            {
                "cue": cue,
                "time": self.track.cue(cue).start,
                "end": self.track.cue(cue).start + 0.45,
                "label": "diagram connection",
            }
        )

    def change(self, cue, *animations, duration=0.6, note="value transition"):
        with self.at(self.time_at(cue)):
            self.play(*animations, run_time=duration)
        self.events.append(
            {"cue": cue, "time": self.track.cue(cue).start, "end": self.track.cue(cue).start + duration, "label": note}
        )

    def retire(self, cue, *items):
        with self.at(self.time_at(cue)):
            self.remove(*items)

    def finish(self):
        self.wait_until(self.end - self.start)
        return self


def flow_nodes(board, nodes, *, loop=False):
    """Compose a cue-triggered explanatory loop from cards and arrows."""
    for cue, label, symbol, x, y in nodes:
        board.show(cue, *card(label, x, y, symbol=symbol, width=520, height=170), motion=True, note=label)
    for current, following in zip(nodes, nodes[1:] + nodes[:1] if loop else nodes[1:]):
        cue, _, _, x, y = following
        _, _, _, px, py = current
        dx, dy = x - px, y - py
        if abs(dx) >= abs(dy):
            sign = 1 if dx > 0 else -1
            a, b = (px + sign * 270, py), (x - sign * 270, y)
        else:
            sign = 1 if dy > 0 else -1
            a, b = (px, py + sign * 90), (x, y - sign * 90)
        # A closing arrow appears after all nodes, not before its source exists.
        board.draw(nodes[-1][0] if following is nodes[0] else cue, connector(a, b))
