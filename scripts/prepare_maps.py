"""Prepare offline assets from two local downloads; see docs/maps.md."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

COUNTRIES = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_110m_admin_0_countries.geojson"
)
TEXTURE = (
    "https://assets.science.nasa.gov/content/dam/science/esd/eo/images/bmng/"
    "bmng-base/january/world.200401.3x5400x2700.jpg"
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("countries", type=Path)
    parser.add_argument("texture", type=Path)
    args = parser.parse_args()
    for path in (args.countries, args.texture):
        if path.stat().st_size > 10_000_000:
            raise ValueError("Source exceeds 10 MB")
    root = Path(__file__).resolve().parents[1] / "src/faceless_champ/assets/maps"
    root.mkdir(parents=True, exist_ok=True)
    countries = []
    for feature in json.loads(args.countries.read_text())["features"]:
        p, g = feature["properties"], feature["geometry"]
        aliases = sorted(
            {
                str(p[k])
                for k in ("ADMIN", "NAME", "NAME_LONG", "ISO_A2", "ISO_A3", "ISO_A2_EH", "ISO_A3_EH", "ADM0_A3")
                if p.get(k) and str(p[k]) != "-99"
            }
        )
        polygons = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        polygons = [[[[round(x, 5), round(y, 5)] for x, y in ring] for ring in poly] for poly in polygons]
        countries.append({"name": p["ADMIN"], "aliases": aliases, "polygons": polygons})
    (root / "countries.json").write_text(json.dumps(countries, separators=(",", ":")) + "\n")
    with Image.open(args.texture) as image:
        image.convert("RGB").resize((4096, 2048), Image.Resampling.LANCZOS).save(
            root / "earth.jpg", quality=88, optimize=True
        )
    metadata = {
        "sources": {
            COUNTRIES: hashlib.sha256(args.countries.read_bytes()).hexdigest(),
            TEXTURE: hashlib.sha256(args.texture.read_bytes()).hexdigest(),
        },
        "outputs": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (root / "countries.json", root / "earth.jpg")
        },
    }
    (root / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    assert sum(p.stat().st_size for p in root.iterdir()) <= 5_000_000
    print(f"Prepared {len(countries)} countries and 4096x2048 Earth texture")


if __name__ == "__main__":
    main()
