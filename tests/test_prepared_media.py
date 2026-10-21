"""Pillow-only prepared playback, identity, timelines and corrupt input checks."""

import json
from copy import deepcopy

import pytest
from PIL import Image

from faceless_champ import Canvas, Group, PreparedFrameSource, Scene, Viewport, create_renderer
from faceless_champ.prepared import _digest, _write_manifest


def frames(directory, colors=((255, 0, 0, 128), (0, 0, 255, 255))):
    (directory / "frames").mkdir(parents=True)
    for index, color in enumerate(colors):
        Image.new("RGBA", (20, 10), color).save(directory / "frames" / f"{index:08d}.png")
    return _write_manifest(directory, size=(20, 10), fps="2", provenance={"fixture": True})


def test_arbitrary_sampling_terminal_holds_alpha_fitting_and_snapshot(tmp_path):
    source = frames(tmp_path)
    assert isinstance(source, PreparedFrameSource)
    assert source.duration == 1 and source.fps == 2
    assert deepcopy(source) is source
    session = source.open((20, 20))
    for time, color in ((0.75, (0, 0, 255, 255)), (0.1, (255, 0, 0, 128)), (1, (0, 0, 255, 255))):
        image = session.frame(time)
        assert image.getpixel((10, 10)) == color
        assert image.getpixel((10, 0)) == (0, 0, 0, 0)
        image.paste("green", (0, 0, 20, 20))
        assert session.frame(time).getpixel((10, 10)) == color
    assert source.frame_key(100) == source.frame_key(0.99)
    session.close()
    session.close()
    with pytest.raises(RuntimeError, match="closed"):
        session.frame(0)


@pytest.mark.parametrize("backend", ["pillow", "skia", "moderngl"])
def test_existing_backends_delay_source_offset_group_opacity_and_seek(tmp_path, backend):
    from importlib.util import find_spec

    if backend != "pillow" and find_spec(backend) is None:
        pytest.skip(f"{backend} is not installed")
    source = frames(tmp_path)
    view = Viewport(source, position=(20, 15), source_start=0.25)
    scene = Scene(Canvas(40, 30, "white")).wait(1).add(Group(view, opacity=0.5)).wait(2)
    with create_renderer(backend, antialias=1) as renderer:
        renderer.validate(scene)
        assert renderer.frame(scene, 0, (40, 30)).getpixel((20, 15))[:3] == (255, 255, 255)
        first = renderer.frame(scene, 1.1, (40, 30))
        blue = renderer.frame(scene, 1.8, (40, 30)).getpixel((20, 15))
        assert blue[2] == 255 and 125 <= blue[0] <= 129
        assert renderer.frame(scene, 1.1, (40, 30)).tobytes() == first.tobytes()
        assert renderer.frame(scene, 2.9, (40, 30)).getpixel((20, 15)) == blue


@pytest.mark.parametrize("damage", ["hash", "dimensions", "path", "missing", "manifest"])
def test_corruption_is_rejected_before_playback(tmp_path, damage):
    frames(tmp_path)
    path = tmp_path / "manifest.json"
    record = json.loads(path.read_text())
    if damage == "hash":
        (tmp_path / "frames/00000000.png").write_bytes(b"broken")
    elif damage == "missing":
        (tmp_path / "frames/00000001.png").unlink()
    elif damage == "dimensions":
        record["size"] = [10, 10]
    elif damage == "path":
        record["frames"][0]["path"] = "../outside.png"
    else:
        record["fingerprint"] = "bad"
    if damage != "manifest":
        record.pop("fingerprint")
        record["fingerprint"] = _digest(record)
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="Invalid prepared"):
        PreparedFrameSource(tmp_path)


def test_new_generation_changes_pixel_identity_and_provenance_is_detached(tmp_path):
    first = frames(tmp_path / "one")
    second = frames(tmp_path / "two", ((0, 255, 0, 255),))
    assert first.fingerprint != second.fingerprint
    first.provenance["fixture"] = False
    assert first.provenance["fixture"] is True
