"""Fetch free fonts/icons once and create original, deterministic sound effects."""

from __future__ import annotations

import hashlib
import json
import math
import random
import struct
import wave
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"
RAW = "https://raw.githubusercontent.com"
SYMBOLS = "MaterialSymbolsOutlined[FILL,GRAD,opsz,wght]"
ICON_NAMES = (
    "square_foot",
    "calculate",
    "trending_up",
    "payments",
    "show_chart",
    "area_chart",
    "bolt",
    "device_hub",
    "analytics",
    "graphic_eq",
)
FONT = ASSETS / "fonts" / "SpaceGrotesk[wght].ttf"
BODY = ASSETS / "fonts" / "DMSans[opsz,wght].ttf"
SFX = ASSETS / "sfx" / "equation-render"
MANIFEST = ASSETS / "equation-render-sources.json"


def required_assets() -> tuple[Path, ...]:
    return (
        FONT,
        BODY,
        *(ASSETS / "icons" / f"{name}.png" for name in ICON_NAMES),
        *(SFX / f"{name}.wav" for name in ("tick", "resolve", "transition")),
        MANIFEST,
    )


def download(url: str, path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.is_file():
        with urlopen(url, timeout=60) as response:
            data = response.read()
        temporary = path.with_suffix(path.suffix + ".download")
        temporary.write_bytes(data)
        temporary.replace(path)
    print(f"Asset ready: {path.relative_to(ASSETS)}", flush=True)
    return {
        "file": str(path.relative_to(ASSETS)),
        "source": url,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def sound(name: str, duration: float) -> dict:
    """Quiet clicks, a soft major-third chime, and a filtered airy sweep."""
    SFX.mkdir(parents=True, exist_ok=True)
    path = SFX / f"{name}.wav"
    if not path.is_file():
        rate, rng, filtered, phase = 48000, random.Random(19), 0.0, 0.0
        samples = bytearray()
        for i in range(round(duration * rate)):
            t, u = i / rate, i / (duration * rate)
            if name == "tick":
                value = 0.16 * math.sin(math.tau * 1400 * t) * math.exp(-t * 52) * min(1, t / 0.003)
            elif name == "resolve":
                value = math.sin(math.tau * 660 * t) + 0.4 * math.sin(math.tau * 825 * t)
                value *= 0.10 * math.exp(-t * 7) * min(1, t / 0.012)
            else:
                noise = rng.uniform(-1, 1)
                filtered += 0.12 * (noise - filtered)
                phase += math.tau * (170 + 230 * u) / rate
                value = (filtered * 0.35 + math.sin(phase) * 0.018) * math.sin(math.pi * u) ** 2
            samples.extend(struct.pack("<h", round(max(-1, min(1, value)) * 32767)))
        with wave.open(str(path), "wb") as output:
            output.setparams((1, 2, rate, 0, "NONE", "not compressed"))
            output.writeframes(samples)
    return {
        "file": str(path.relative_to(ASSETS)),
        "source": "Original procedural audio; CC0-1.0",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def main() -> None:
    sources = []
    for family, filename in (("spacegrotesk", FONT.name), ("dmsans", BODY.name)):
        folder = ASSETS / "fonts"
        sources.append(download(f"{RAW}/google/fonts/main/ofl/{family}/{quote(filename)}", folder / filename))
        sources.append(download(f"{RAW}/google/fonts/main/ofl/{family}/OFL.txt", folder / f"{family}-OFL.txt"))
    for suffix in ("ttf", "codepoints"):
        filename = f"{SYMBOLS}.{suffix}"
        sources.append(
            download(
                f"{RAW}/google/material-design-icons/master/variablefont/{quote(filename)}", ASSETS / "icons" / filename
            )
        )
    sources.append(download(f"{RAW}/google/material-design-icons/master/LICENSE", ASSETS / "icons" / "LICENSE.txt"))
    codepoints = dict(line.split() for line in (ASSETS / "icons" / f"{SYMBOLS}.codepoints").read_text().splitlines())
    font = ImageFont.truetype(str(ASSETS / "icons" / f"{SYMBOLS}.ttf"), 256)
    font.set_variation_by_axes([0, 0, 48, 300])
    for name in ICON_NAMES:
        path = ASSETS / "icons" / f"{name}.png"
        if path.is_file():
            continue
        glyph = chr(int(codepoints[name], 16))
        bitmap = Image.new("RGBA", (288, 288))
        draw = ImageDraw.Draw(bitmap)
        left, top, right, bottom = draw.textbbox((0, 0), glyph, font=font)
        draw.text(((288 - right + left) / 2 - left, (288 - bottom + top) / 2 - top), glyph, font=font, fill="white")
        bitmap.save(path)
    sources.extend(sound(name, duration) for name, duration in (("tick", 0.14), ("resolve", 0.6), ("transition", 0.7)))
    (SFX / "LICENSE.txt").write_text(
        "Original equation-render procedural sound effects.\nDedicated to the public domain under CC0 1.0.\n"
        "https://creativecommons.org/publicdomain/zero/1.0/\n",
        encoding="utf-8",
    )
    MANIFEST.write_text(
        json.dumps(
            {"downloads": sources, "icons": ICON_NAMES, "icon_style": {"FILL": 0, "GRAD": 0, "opsz": 48, "wght": 300}},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
