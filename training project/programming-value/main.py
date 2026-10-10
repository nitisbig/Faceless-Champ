"""Programming Value: thin composition entrypoint over the two main packages."""

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[1]
sys.path.insert(0, str(PROJECT))
for source in (ROOT / "facelesschamp-kit/src", ROOT / "src"):
    sys.path.insert(0, str(source))

from facelesschamp_kit import BuildContext
from scene.design import CANVAS, THEME
from scene.story import build


def programming_value_video(image_mode="auto", version="v2"):
    if version == "v1":
        ctx = BuildContext(PROJECT, canvas=CANVAS, theme=THEME, safe_margin=72, captions=False)
        return build(ctx, image_mode=image_mode).compile()
    if version != "v2":
        raise ValueError("Version must be v1 or v2")
    from scene.design_v2 import CANVAS as canvas
    from scene.design_v2 import THEME as theme
    from scene.story_v2 import build as build_v2

    ctx = BuildContext(PROJECT, canvas=canvas, theme=theme, safe_margin=96, captions=False)
    authored = build_v2(ctx, image_mode=image_mode)
    compiled = authored.compile()
    compiled.report.update(version="v2", visual_events=authored.visual_events)
    return compiled


def video():
    """Zero-argument factory accepted by the core CLI."""
    return programming_value_video().composition


__all__ = ["build", "programming_value_video", "video"]
