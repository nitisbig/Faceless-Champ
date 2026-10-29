"""Project-local Roadster engineering film; source media stays untouched."""

import os
from pathlib import Path

# Avoid oversubscribing the software OpenGL renderer on small review machines.
os.environ.setdefault("LP_NUM_THREADS", "2")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/faceless-roadster-matplotlib")

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
ASSETS = ROOT / "assets"
OUTPUT = ROOT / "output"
FPS = 30
END = 738.3
DECODED_AUDIO_DURATION = 738.2726666666666
FONT = REPO / "assets/fonts/DMSans[opsz,wght].ttf"
DISPLAY_FONT = REPO / "assets/fonts/SpaceGrotesk[wght].ttf"
