"""Regenerate src/faceless_champ/assets/font-coverage.json (dev-only; needs fontTools).

Runtime code reads the JSON so glyph fallback works without fontTools installed.
Run after adding or replacing a bundled font: python scripts/build_font_coverage.py
"""

import json
from pathlib import Path

from fontTools.ttLib import TTFont

ASSETS = Path(__file__).resolve().parents[1] / "src" / "faceless_champ" / "assets"


def ranges(codepoints):
    result, start, previous = [], None, None
    for cp in sorted(codepoints):
        if start is None:
            start = previous = cp
        elif cp == previous + 1:
            previous = cp
        else:
            result.append([start, previous])
            start = previous = cp
    if start is not None:
        result.append([start, previous])
    return result


def main():
    coverage = {}
    for path in sorted(ASSETS.glob("*.ttf")):
        cmap = TTFont(path).getBestCmap()
        coverage[path.name] = ranges(cmap)
    out = ASSETS / "font-coverage.json"
    out.write_text(json.dumps(coverage, separators=(",", ":")) + "\n")
    print(f"wrote {out} for {len(coverage)} fonts")


if __name__ == "__main__":
    main()
