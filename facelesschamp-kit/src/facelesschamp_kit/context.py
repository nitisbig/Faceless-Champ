import csv
import json
import random
from dataclasses import dataclass, field
from pathlib import Path

from faceless_champ import Bounds, Canvas

from .assets import AssetRegistry
from .diagnostics import KitError, number
from .themes import MIDNIGHT, Theme


@dataclass
class BuildContext:
    root: Path
    canvas: Canvas = field(default_factory=lambda: Canvas(1080, 1920, MIDNIGHT.background))
    theme: Theme = MIDNIGHT
    seed: int = 0
    safe_margin: float = 64
    caption_space: float = 220
    captions: bool = False
    assets: AssetRegistry | None = None

    def __post_init__(self):
        self.root = Path(self.root).resolve()
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise KitError("SEED", "seed must be an integer")
        self.random = random.Random(self.seed)
        self.assets = self.assets or AssetRegistry(self.root)
        self.safe_margin = number(self.safe_margin, "safe_margin")
        self.caption_space = number(self.caption_space, "caption_space")
        if 2 * self.safe_margin >= min(self.canvas.width, self.canvas.height):
            raise KitError("LAYOUT", "Safe margin leaves no content area")

    @property
    def bounds(self):
        m = self.safe_margin
        bottom = self.canvas.height - m - (self.caption_space if self.captions else 0)
        if bottom <= m:
            raise KitError("LAYOUT", "Caption reservation leaves no content area")
        return Bounds(m, m, self.canvas.width - m, bottom)

    def load_json(self, path):
        return json.loads((self.root / path).read_text())

    def load_csv(self, path):
        with (self.root / path).open(newline="") as stream:
            return list(csv.DictReader(stream))
