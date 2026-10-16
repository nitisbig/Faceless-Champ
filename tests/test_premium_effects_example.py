"""The published preview's authored lifetimes and gradients work through the core renderer."""

import runpy
from pathlib import Path

from faceless_champ import Image, PillowRenderer


def test_premium_comparison_preview_builds_and_seeks():
    example = runpy.run_path(str(Path(__file__).resolve().parents[1] / "examples/premium_effects/render.py"))
    movie = example["comparison"]()
    assert movie.duration == 6
    images = [e for e in movie.entries if isinstance(e.component, Image)]
    assert len(images) == 6 and all(e.start == 0 for e in movie.entries)
    with PillowRenderer(1) as renderer:
        entrance = renderer.frame(movie, 0.4, (240, 135))
        settled = renderer.frame(movie, 2.5, (240, 135))
        transformed = renderer.frame(movie, 3.5, (240, 135))
        assert entrance.tobytes() != settled.tobytes() != transformed.tobytes()
        assert renderer.frame(movie, 2.5, (240, 135)).tobytes() == settled.tobytes()


def test_rotated_pale_gradient_edge_does_not_ring_white():
    example = runpy.run_path(str(Path(__file__).resolve().parents[1] / "examples/premium_effects/render.py"))
    with PillowRenderer(1) as renderer:
        frame = renderer.frame(example["comparison"](), 3.5, (960, 540))
    # This blue lower edge used to contain all-white pixels after resize + rotate.
    assert not any(min(frame.getpixel((x, y))[:3]) >= 250 for y in range(215, 243) for x in range(365, 595))
