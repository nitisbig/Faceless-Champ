"""Lazy native loading and explicit pixel-format conversions."""

from functools import lru_cache
from importlib.metadata import version


@lru_cache(maxsize=1)
def load_skia():
    try:
        import skia
    except (ImportError, OSError) as exc:
        raise RuntimeError(
            "Skia backend unavailable. Install faceless-champ[skia]; on Linux install "
            "libfontconfig1, libgl1 and libegl1. No automatic Pillow substitution is performed."
        ) from exc
    if not version("skia-python").startswith("144."):
        raise RuntimeError("This backend requires skia-python>=144.0.post2,<145; install faceless-champ[skia]")
    return skia


def image_from_pillow(image, skia):
    import numpy as np

    return skia.Image.fromarray(
        np.asarray(image.convert("RGBA")),
        colorType=skia.ColorType.kRGBA_8888_ColorType,
        alphaType=skia.AlphaType.kUnpremul_AlphaType,
        copy=True,
    )


def image_to_pillow(image, skia):
    from PIL import Image

    array = image.toarray(
        colorType=skia.ColorType.kRGBA_8888_ColorType,
        alphaType=skia.AlphaType.kUnpremul_AlphaType,
        colorSpace=skia.ColorSpace.MakeSRGB(),
    )
    array[array[:, :, 3] == 0] = 0
    return Image.frombytes("RGBA", (image.width(), image.height()), array.tobytes())
