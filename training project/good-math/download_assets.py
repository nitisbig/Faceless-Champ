"""Fetch the free Google assets once; renders use only local files afterward."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parents[2] / "assets"
FONTS = ASSETS / "fonts"
ICONS = ASSETS / "icons"
RAW = "https://raw.githubusercontent.com"
SYMBOL_FONT = "MaterialSymbolsOutlined[FILL,GRAD,opsz,wght]"
ICON_NAMES = (
    "school",
    "person",
    "calculate",
    "timer",
    "menu_book",
    "lightbulb",
    "event_repeat",
    "psychology",
    "route",
    "close",
    "check",
    "help",
    "schedule",
    "trending_up",
    "edit",
    "visibility",
    "hourglass_empty",
)


def download(url: str, path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with urlopen(url, timeout=60) as response:
            content = response.read()
        path.write_bytes(content)
    print(f"Asset ready: {path.relative_to(ASSETS)}", flush=True)
    return {
        "file": str(path.relative_to(ASSETS)),
        "source": url,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def main() -> None:
    sources = []
    for name in ("CormorantGaramond[wght].ttf", "CormorantGaramond-Italic[wght].ttf", "OFL.txt"):
        sources.append(download(f"{RAW}/google/fonts/main/ofl/cormorantgaramond/{quote(name)}", FONTS / name))
    for suffix in ("ttf", "codepoints"):
        name = f"{SYMBOL_FONT}.{suffix}"
        sources.append(download(f"{RAW}/google/material-design-icons/master/variablefont/{quote(name)}", ICONS / name))
    sources.append(download(f"{RAW}/google/material-design-icons/master/LICENSE", ICONS / "LICENSE.txt"))
    codepoints = dict(line.split() for line in (ICONS / f"{SYMBOL_FONT}.codepoints").read_text().splitlines())
    font = ImageFont.truetype(str(ICONS / f"{SYMBOL_FONT}.ttf"), 256)
    # FILL=0, GRAD=0, opsz=48, wght=200: thin outline glyphs matching layout.png.
    font.set_variation_by_axes([0, 0, 48, 200])
    for name in ICON_NAMES:
        glyph = chr(int(codepoints[name], 16))
        bitmap = Image.new("RGBA", (288, 288))
        draw = ImageDraw.Draw(bitmap)
        left, top, right, bottom = draw.textbbox((0, 0), glyph, font=font)
        draw.text(((288 - right + left) / 2 - left, (288 - bottom + top) / 2 - top), glyph, font=font, fill="white")
        bitmap.save(ICONS / f"{name}.png")
    (ASSETS / "good-math-sources.json").write_text(
        json.dumps(
            {"downloads": sources, "icons": ICON_NAMES, "icon_style": {"FILL": 0, "GRAD": 0, "opsz": 48, "wght": 200}},
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
