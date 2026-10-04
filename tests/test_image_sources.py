from io import BytesIO

import pytest
from PIL import Image as PILImage

from faceless_champ import Canvas, Image, PillowRenderer, Scene


def frame(component, time=0, renderer=None):
    scene = Scene(Canvas(40, 40, "white"))
    scene.add(component)
    scene.wait(1)
    return (renderer or PillowRenderer(1)).frame(scene, time, (40, 40))


def test_source_paths_bytes_and_pillow_match_and_snapshot(tmp_path):
    original = PILImage.new("RGBA", (12, 8), (193, 95, 60, 128))
    path = tmp_path / "sample.png"
    original.save(path)
    sources = [path, str(path), path.read_bytes(), bytearray(path.read_bytes()), original]
    results = [frame(Image.from_source(s, width=20, height=20, position=(20, 20))).tobytes() for s in sources]
    assert all(result == results[0] for result in results)
    component = Image.from_source(original, width=20, height=20, position=(20, 20))
    original.paste("blue", (0, 0, 12, 8))
    original.close()
    assert frame(component).tobytes() == results[0]


def test_trim_tint_and_transparent_image():
    source = PILImage.new("RGBA", (20, 20))
    source.paste((0, 0, 0, 255), (8, 8, 12, 12))
    result = frame(Image.from_source(source, width=20, height=20, trim=True, tint="#C15F3C", position=(20, 20)))
    assert result.getpixel((12, 12)) == (193, 95, 60, 255)
    empty = frame(Image.from_source(PILImage.new("RGBA", (20, 20)), trim=True, position=(20, 20)))
    assert empty.getpixel((20, 20)) == (255, 255, 255, 255)


def test_memory_gif_animates_even_with_scene_frame_cache():
    a, b = PILImage.new("RGB", (8, 8), "red"), PILImage.new("RGB", (8, 8), "blue")
    buffer = BytesIO()
    a.save(buffer, format="GIF", save_all=True, append_images=[b], duration=[100, 300], loop=0)
    scene = Scene(Canvas(40, 40))
    scene.add(Image.from_source(buffer.getvalue(), width=40, height=40, position=(20, 20)))
    scene.wait(1)
    renderer = PillowRenderer(1)
    assert renderer.frame(scene, 0.05, (40, 40)).getpixel((20, 20))[:3] == (255, 0, 0)
    assert renderer.frame(scene, 0.2, (40, 40)).getpixel((20, 20))[:3] == (0, 0, 255)
    assert renderer.frame(scene, 0.45, (40, 40)).getpixel((20, 20))[:3] == (255, 0, 0)


def test_invalid_source_and_tint_fail():
    with pytest.raises(TypeError, match="source"):
        Image.from_source(object())
    with pytest.raises(OSError):
        frame(Image.from_source(b"invalid"))
    scene = Scene()
    scene.add(Image.from_source(PILImage.new("RGB", (2, 2)), tint="invalid"))
    with pytest.raises(ValueError):
        PillowRenderer().validate(scene)


def test_time_based_polyline_reveal_and_validation():
    from faceless_champ import Draw, Polyline, linear

    scene = Scene(Canvas(100, 100, "white"))
    curve = Polyline([(10, 80), (50, 10), (90, 10)], draw_by="x", stroke="red", stroke_width=2)
    scene.play(Draw(curve), run_time=1, rate_func=linear)
    image = PillowRenderer(1).frame(scene, 0.5, (100, 100))
    red_pixels = [(x, y) for y in range(100) for x in range(100) if image.getpixel((x, y))[:3] == (255, 0, 0)]
    assert 49 <= max(x for x, y in red_pixels) <= 51
    assert min(y for x, y in red_pixels) <= 11
    for points in ([(0, 0), (0, 2)], [(1, 0), (0, 2)]):
        with pytest.raises(ValueError, match="increasing"):
            Polyline(points, draw_by="x")
    with pytest.raises(ValueError, match="draw_by"):
        Polyline([(0, 0), (2, 2)], draw_by="bad")
