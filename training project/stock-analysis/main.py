"""Import the main checkout's library and compose the stock-analysis example."""

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scene import stock_analysis_video, timeline

__all__ = ["stock_analysis_video", "timeline"]
