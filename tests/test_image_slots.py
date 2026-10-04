import pytest
from PIL import Image as PILImage
from PIL import ImageChops

from faceless_champ import Canvas, FadeIn, ImageSlot, PillowRenderer, Scene


def slot_scene(path, mode="auto", **kwargs):
    scene = Scene(Canvas(160, 90, "white"))
    scene.play(FadeIn(ImageSlot(path, mode=mode, width=100, height=60, position=(80, 45), **kwargs)), run_time=1)
    return scene


def test_slot_modes_and_replacement_preserve_box(tmp_path):
    path = tmp_path / "1.png"
    scene = slot_scene(path)
    renderer = PillowRenderer(1)
    renderer.validate(scene)
    placeholder = renderer.frame(scene, 1, (160, 90))
    assert placeholder.getpixel((34, 20))[:3] == (244, 243, 238)
    assert renderer.frame(scene, 0, (160, 90)).getpixel((80, 45))[:3] == (255, 255, 255)
    PILImage.new("RGB", (40, 40), "red").save(path)
    loaded = PillowRenderer(1).frame(scene, 1, (160, 90))
    assert loaded.getpixel((80, 45))[:3] == (255, 0, 0)
    forced = PillowRenderer(1).frame(slot_scene(path, "placeholder"), 1, (160, 90))
    assert forced.tobytes() == placeholder.tobytes()
    cover = PillowRenderer(1).frame(slot_scene(path, "required", fit="cover"), 1, (160, 90))
    assert cover.getpixel((31, 16))[:3] == (255, 0, 0)


def test_slot_transform_and_useful_asset_errors(tmp_path):
    path = tmp_path / "2.png"
    with pytest.raises(FileNotFoundError, match="2.png"):
        PillowRenderer(1).validate(slot_scene(path, "required"))
    path.write_bytes(b"not an image")
    with pytest.raises(ValueError, match="Cannot decode image.*2.png"):
        PillowRenderer(1).validate(slot_scene(path))
    PillowRenderer(1).validate(slot_scene(path, "placeholder", rotation=30, scale=0.8))
    transformed = (
        PillowRenderer(1)
        .frame(slot_scene(path, "placeholder", rotation=90, scale=0.5, label=""), 1, (160, 90))
        .convert("RGB")
    )
    assert ImageChops.difference(transformed, PILImage.new("RGB", (160, 90), "white")).getbbox() == (65, 20, 95, 70)
    with pytest.raises(ValueError, match="mode"):
        ImageSlot(path, mode="unknown")
