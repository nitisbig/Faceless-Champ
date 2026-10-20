"""PNG publication preserves another writer's output and cleans failed encodes."""

from pathlib import Path

import pytest
from PIL import Image

from faceless_champ import Canvas, Scene, render_storyboard, save_frame


@pytest.mark.parametrize("mode", ["frame", "storyboard-frame", "storyboard-sheet"])
@pytest.mark.parametrize("overwrite", [False, True])
def test_concurrent_png_publication_respects_overwrite(tmp_path, mode, overwrite):
    target = (
        tmp_path
        / {"frame": "frame.png", "storyboard-frame": "01-0000.500s.png", "storyboard-sheet": "storyboard.png"}[mode]
    )
    sentinel = b"another producer owns this file"

    class OtherWriter:
        def validate(self, node):
            pass

        def frame(self, node, time, size):
            target.write_bytes(sentinel)
            return Image.new("RGB", size, "red")

    def publish():
        scene = Scene(Canvas(100, 100)).wait(1)
        if mode == "frame":
            return save_frame(scene, 0.5, target, size=(100, 100), renderer=OtherWriter(), overwrite=overwrite)
        return render_storyboard(scene, [0.5], tmp_path, size=(100, 100), renderer=OtherWriter(), overwrite=overwrite)

    if overwrite:
        publish()
        with Image.open(target) as image:
            assert image.getpixel((50, 50)) == (255, 0, 0)
    else:
        with pytest.raises(FileExistsError):
            publish()
        assert target.read_bytes() == sentinel
    assert not list(tmp_path.glob(".*.tmp"))


@pytest.mark.parametrize("existing", [False, True])
def test_failed_png_encode_preserves_output_and_removes_temporary(tmp_path, monkeypatch, existing):
    target = tmp_path / "frame.png"
    if existing:
        target.write_bytes(b"original")

    def broken(image, filename, *args, **kwargs):
        Path(filename).write_bytes(b"partial encode")
        raise ValueError("deliberate PNG encoding failure")

    monkeypatch.setattr(Image.Image, "save", broken)
    with pytest.raises(ValueError, match="deliberate"):
        save_frame(Scene(Canvas(100, 100)).wait(1), 0.5, target, size=(100, 100), overwrite=existing)
    assert target.read_bytes() == b"original" if existing else not target.exists()
    assert not list(tmp_path.glob(".*.tmp"))
