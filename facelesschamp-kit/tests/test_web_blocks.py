import json

from faceless_champ import Canvas, PillowRenderer, Scene
from faceless_champ.web import WebCapture
from PIL import Image

from facelesschamp_kit.blocks import WebElement, WebWalkthrough
from facelesschamp_kit.context import BuildContext


def test_web_blocks_fresh_and_fitted(tmp_path):
    Image.new("RGB", (144, 90), "#aaccdd").save(tmp_path / "00000000.png")
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "fps": 1,
                "duration": 1,
                "viewport": [144, 90],
                "frames": {"0": {"geometry": {"#box": [0, 0, 72, 45]}, "cursor": [10, 10], "clicks": []}},
            }
        )
    )
    capture = WebCapture(tmp_path)
    for canvas in (Canvas(1920, 1080), Canvas(1080, 1920)):
        ctx = BuildContext(tmp_path, canvas=canvas)
        for block in (
            WebWalkthrough(capture, browser_chrome=False),
            WebWalkthrough(capture),
            WebElement(capture, "#box"),
        ):
            first, second = block.compose(ctx, ctx.bounds), block.compose(ctx, ctx.bounds)
            assert first.root is not second.root
            assert first.bounds.left >= ctx.bounds.left - 1
            assert first.bounds.right <= ctx.bounds.right + 1
            assert first.bounds.top >= ctx.bounds.top - 1
            assert first.bounds.bottom <= ctx.bounds.bottom + 1
            scene = Scene(canvas)
            scene.add(first.root)
            scene.wait(1)
            assert PillowRenderer(1).frame(scene, 0, (192, 108)).size == (192, 108)
