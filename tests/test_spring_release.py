"""Release checks across FPS seek orders, damping regimes, and frame-cache modes."""

import runpy
from pathlib import Path

import pytest

from faceless_champ import Spring


@pytest.fixture(scope="module")
def verify_frame_rates():
    path = Path(__file__).resolve().parents[1] / "examples/spring_motion/verify.py"
    return runpy.run_path(str(path))["verify_frame_rates"]


@pytest.mark.parametrize("damping", [10, 20, 25])
@pytest.mark.parametrize("frame_cache_mb", [0, 64])
def test_matching_absolute_states_and_pixels_after_different_fps_seek_orders(
    verify_frame_rates, damping, frame_cache_mb
):
    result = verify_frame_rates(Spring(100, damping, 1), frame_cache_mb=frame_cache_mb)
    assert result["states_and_pixels_equal"] and result["sources_unchanged"]
