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
    preparing: bool = False
    refresh_prepared: bool = False
    prepared_assets: list = field(default_factory=list)

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

    def manim(self, spec, *, options=None, python=None, timeout=600, output_limit=2 * 1024**3, cancel=None):
        """Declare prepared mathematical media; only Project.prepare executes it."""
        from faceless_champ.integrations.manim import (
            ManimError,
            ManimRenderOptions,
            load_manim,
            prepare_manim,
        )

        options = options or ManimRenderOptions(seed=self.seed)
        try:
            arguments = {"cache_dir": self.root / ".fc-kit/manim", "options": options, "python": python}
            if self.preparing:
                prepared = prepare_manim(
                    spec,
                    **arguments,
                    timeout=timeout,
                    output_limit=output_limit,
                    refresh=self.refresh_prepared,
                    cancel=cancel,
                )
            else:
                prepared = load_manim(spec, **arguments)
            self.prepared_assets.append(
                {
                    "kind": "manim",
                    "status": "prepared",
                    "fingerprint": prepared.fingerprint,
                    "path": str(prepared.directory),
                    "size": list(prepared.intrinsic_size),
                    "fps": str(prepared.fps),
                    "duration": prepared.duration,
                    "provenance": prepared.provenance,
                }
            )
            return prepared
        except ManimError as exc:
            raise KitError(exc.code, str(exc), **exc.details) from exc
        except (OSError, ValueError, TypeError) as exc:
            raise KitError("MANIM_ASSET", str(exc)) from exc

    def playground(self, script, *, timeout=10, output_limit=1_000_000, fps=15):
        """Declare a prepared dependency. Only Project.prepare executes checkpoints."""
        import hashlib
        import os
        import tempfile

        from facelesschamp_kit.playground import PlaygroundError, PreparedPlayground, prepare_playground

        settings = {"timeout": timeout, "output_limit": output_limit, "fps": fps}
        key = hashlib.sha256(json.dumps({"script": script.record(), **settings}, sort_keys=True).encode()).hexdigest()
        directory = self.root / ".fc-kit/playgrounds"
        reference = directory / (key + ".json")
        try:
            if self.preparing:
                prepared = prepare_playground(script, cache_dir=directory, refresh=self.refresh_prepared, **settings)
                fd, temporary = tempfile.mkstemp(prefix=".reference-", dir=directory)
                try:
                    with os.fdopen(fd, "w") as stream:
                        json.dump({"asset": prepared.directory.name}, stream)
                    os.replace(temporary, reference)
                finally:
                    Path(temporary).unlink(missing_ok=True)
            else:
                if not reference.is_file():
                    raise KitError("PLAYGROUND_UNPREPARED", "Run fc-kit prepare before validate/frame/preview/render")
                asset = (directory / json.loads(reference.read_text())["asset"]).resolve()
                if not asset.is_relative_to(directory.resolve()):
                    raise KitError("PLAYGROUND_ASSET", "Prepared reference escapes its cache")
                prepared = PreparedPlayground(asset)
                if prepared.script.record() != script.record():
                    raise KitError("PLAYGROUND_STALE", "Source changed; run fc-kit prepare")
            self.prepared_assets.append(
                {
                    "kind": "coding-playground",
                    "status": "prepared",
                    "fingerprint": prepared.fingerprint,
                    "path": str(prepared.directory),
                }
            )
            return prepared
        except KitError:
            raise
        except PlaygroundError as exc:
            raise KitError(exc.code, str(exc), **exc.scope) from exc
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise KitError("PLAYGROUND_ASSET", str(exc)) from exc
