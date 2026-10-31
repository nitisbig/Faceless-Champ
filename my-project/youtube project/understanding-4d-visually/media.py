"""Prepared footage as skia images (see prepare_media.py)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import skia

PREPARED = Path(__file__).resolve().parent / "media" / "prepared"
FRAME_FPS = 5  # cheetah_frames were extracted at 5 fps from the 24 fps clip
OPENER_FPS = 30
FRAME_COUNT = 126


def _load(path: Path) -> skia.Image:
    image = skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName(str(path)))
    if image is None:
        raise FileNotFoundError(f"{path} missing: run prepare_media.py")
    return image.makeRasterImage()


def _clamp(i: int, n: int) -> int:
    return max(1, min(n, i))


@lru_cache(maxsize=4)
def opener(index: int) -> skia.Image:
    count = len(list((PREPARED / "opener").glob("*.jpg")))
    return _load(PREPARED / "opener" / f"{_clamp(index, count):04d}.jpg")


@lru_cache(maxsize=10)
def frame(index: int) -> skia.Image:
    """Full-resolution 5 fps frame, 1-based."""
    return _load(PREPARED / "full" / f"{_clamp(index, FRAME_COUNT):03d}.jpg")


@lru_cache(maxsize=FRAME_COUNT)
def thumb(index: int) -> skia.Image:
    return _load(PREPARED / "thumb" / f"{_clamp(index, FRAME_COUNT):03d}.jpg")


def frame_at(clip_seconds: float) -> int:
    """The 5 fps frame showing clip time ``clip_seconds``."""
    return _clamp(int(clip_seconds * FRAME_FPS) + 1, FRAME_COUNT)
