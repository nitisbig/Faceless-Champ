"""Country Economy composition factory, importable from any working directory."""

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scene import country_economy_video, timeline

__all__ = ["country_economy_video", "timeline"]
