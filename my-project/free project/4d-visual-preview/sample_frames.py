"""Video frames shown inside the tesseract.

Drop real frames into ``frames/`` (``*.png`` or ``*.jpg``, sorted by name) and they are
used automatically. Otherwise a procedural galloping-cat clip stands in.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
FRAME_DIR = ROOT / "frames"
FRAME_SIZE = (480, 300)
SAMPLE_COUNT = 16
SKY_TOP, SKY_LOW, GROUND = (255, 196, 120), (255, 137, 74), (92, 52, 34)
SUN, SHADOW, BODY = (255, 236, 190), (40, 22, 16), (24, 14, 12)


def _leg(draw, hip, angle, knee_bend, upper, lower, width):
    kx = hip[0] + upper * math.sin(angle)
    ky = hip[1] + upper * math.cos(angle)
    fa = angle - knee_bend
    fx, fy = kx + lower * math.sin(fa), ky + lower * math.cos(fa)
    draw.line([hip, (kx, ky), (fx, fy)], fill=BODY, width=width, joint="curve")
    draw.ellipse((fx - width / 2, fy - width / 2, fx + width / 2, fy + width / 2), fill=BODY)


def _sample(index: int) -> Image.Image:
    """One frame of a stylised rotary gallop, drawn at 4x and downsampled."""
    s = 4
    w, h = FRAME_SIZE[0] * s, FRAME_SIZE[1] * s
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    horizon = int(h * 0.7)
    for y in range(horizon):
        k = y / horizon
        draw.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * k) for a, b in zip(SKY_TOP, SKY_LOW)))
    draw.ellipse((w * 0.68, h * 0.18, w * 0.84, h * 0.18 + w * 0.16), fill=SUN)
    draw.rectangle((0, horizon, w, h), fill=GROUND)
    p = index / SAMPLE_COUNT
    # Grass tufts scroll left so the frames read as motion even without the cat.
    for i in range(14):
        gx = ((i * 173 - p * 2 * w * 0.5) % (w + 200)) - 100
        gy = horizon + 30 + (i * 53) % (h - horizon - 60)
        for dx in (-14, 0, 14):
            draw.line([(gx + dx, gy), (gx + dx * 2, gy - 46)], fill=(140, 86, 48), width=7)
    ph = math.tau * p
    cx, cy = w * 0.46, horizon - 250 + 26 * math.sin(2 * ph)
    stretch = 1 + 0.16 * math.sin(ph)  # spine extends and gathers each stride
    tilt = 0.08 * math.sin(ph + 0.6)
    draw.ellipse((cx - 330, horizon - 18, cx + 330, horizon + 30), fill=SHADOW)
    shoulder = (cx + 230 * stretch * math.cos(tilt), cy - 230 * math.sin(tilt) - 20)
    hip = (cx - 230 * stretch * math.cos(tilt), cy + 230 * math.sin(tilt) - 20)
    draw.line([hip, (cx, cy - 40), shoulder], fill=BODY, width=120, joint="curve")
    draw.ellipse((cx - 70, cy - 70, cx + 90, cy + 50), fill=BODY)
    head = (shoulder[0] + 130, shoulder[1] - 40 + 10 * math.sin(2 * ph))
    draw.line([shoulder, head], fill=BODY, width=78)
    draw.ellipse((head[0] - 58, head[1] - 46, head[0] + 70, head[1] + 40), fill=BODY)
    draw.polygon([(head[0] - 30, head[1] - 40), (head[0] - 10, head[1] - 82), (head[0] + 8, head[1] - 38)], fill=BODY)
    tail = [hip]
    for k in range(1, 7):
        tail.append((hip[0] - 62 * k, hip[1] - 30 * k + 40 * math.sin(ph * 1.0 + k * 0.7) * k / 6))
    draw.line(tail, fill=BODY, width=30, joint="curve")
    for offset, root, sign in ((0.0, shoulder, 1), (0.35, shoulder, 1), (0.55, hip, -1), (0.85, hip, -1)):
        a = ph + offset * math.tau
        swing = 0.95 * math.sin(a)
        bend = sign * (0.4 + 0.7 * max(0.0, math.cos(a)))
        _leg(draw, (root[0], root[1] + 30), swing, bend, 190, 180, 40)
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    return img.resize(FRAME_SIZE, Image.Resampling.LANCZOS).convert("RGBA")


@lru_cache(maxsize=1)
def load_frames() -> tuple[Image.Image, ...]:
    """Frames from ``frames/`` when present, else the procedural sample clip."""
    files = sorted(p for p in FRAME_DIR.glob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"})
    if files:
        return tuple(Image.open(p).convert("RGBA").resize(FRAME_SIZE, Image.Resampling.LANCZOS) for p in files)
    return tuple(_sample(i) for i in range(SAMPLE_COUNT))


if __name__ == "__main__":
    out = ROOT / "output" / "sample-frames.png"
    out.parent.mkdir(exist_ok=True)
    frames = load_frames()
    sheet = Image.new("RGBA", (FRAME_SIZE[0] * 4, FRAME_SIZE[1] * ((len(frames) + 3) // 4)))
    for i, f in enumerate(frames):
        sheet.paste(f, ((i % 4) * FRAME_SIZE[0], (i // 4) * FRAME_SIZE[1]))
    sheet.save(out)
    print(out)
