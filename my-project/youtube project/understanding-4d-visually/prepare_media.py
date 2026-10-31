"""One-off media preparation (re-run only when the footage changes).

* Crops away the burned-in "0.87 SECONDS" timer: box (205, 115, 1920, 1080) is
  1715 x 965, i.e. 16:9, and is scaled back to 1920 x 1080.
* media/prepared/full/NNN.jpg   126 cropped 5 fps frames, 1920 x 1080
* media/prepared/thumb/NNN.jpg  the same frames at 480 x 270 for the volume block
* media/prepared/opener/NNNN.jpg  smooth 30 fps footage, clip seconds 0-5, same crop

    python prepare_media.py
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
MEDIA = ROOT / "media"
OUT = MEDIA / "prepared"
CROP = (205, 115, 1920, 1080)
OPENER_SECONDS = 5.0


def main():
    frames = sorted((MEDIA / "cheetah_frames").glob("frame_*.png"))
    for sub in ("full", "thumb", "opener"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    for i, path in enumerate(frames, 1):
        img = Image.open(path).convert("RGB").crop(CROP)
        img.resize((1920, 1080), Image.Resampling.LANCZOS).save(OUT / "full" / f"{i:03d}.jpg", quality=93)
        img.resize((480, 270), Image.Resampling.LANCZOS).save(OUT / "thumb" / f"{i:03d}.jpg", quality=90)
    x, y, x1, y1 = CROP
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-y", "-t", str(OPENER_SECONDS), "-i", str(MEDIA / "cheetah.mp4"),
            "-vf", f"crop={x1 - x}:{y1 - y}:{x}:{y},scale=1920:1080:flags=lanczos,fps=30",
            "-q:v", "2", str(OUT / "opener" / "%04d.jpg"),
        ],
        check=True,
    )
    counts = {sub: len(list((OUT / sub).glob("*.jpg"))) for sub in ("full", "thumb", "opener")}
    print(counts)


if __name__ == "__main__":
    main()
