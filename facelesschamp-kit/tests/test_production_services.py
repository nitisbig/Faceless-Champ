"""The important M5 contracts: source clock, ownership and atomic recovery."""

import json
from concurrent.futures import CancelledError

import pytest
from faceless_champ import Canvas, ExportSettings, PillowRenderer, Scene, Text

from facelesschamp_kit import CompiledVideo, media_probe, public_capabilities, rendering


def compiled_video():
    scene = Scene(Canvas(160, 90))
    scene.add(Text("Source time", font_size=12, position=(80, 45)))
    scene.wait(2)
    return CompiledVideo(scene, {}, None)


class Session(PillowRenderer):
    closed = False

    @property
    def identity(self):
        assert not self.closed, "Provenance read after session close"
        return {"backend": "pillow", "renderer": "m5-test"}

    def close(self):
        self.closed = True
        super().close()


def test_compiled_operations_own_only_their_sessions(tmp_path, monkeypatch):
    compiled = compiled_video()
    sessions = []

    def create(*args, **kwargs):
        session = Session(1)
        sessions.append(session)
        return session

    monkeypatch.setattr(rendering, "create_renderer", create)
    frame = compiled.frame(0.75, size=(160, 90))
    assert frame.size == (160, 90) and sessions[-1].closed
    result = compiled.save_frame(0.75, tmp_path / "frame.png", size=(160, 90))
    assert result["source_range"] is None and result["rendering"]["renderer"] == "m5-test"
    assert result["rendering"]["fonts"] and sessions[-1].closed
    assert result["settings"]["size"] == [160, 90]
    json.dumps({k: v for k, v in result.items() if k != "output"})
    caller = Session(1)
    sheet = compiled.storyboard([1.5, 0.25, 1.5], tmp_path / "sheet", size=(160, 90), renderer=caller)
    assert sheet["output"].is_file() and not caller.closed
    assert [p.name for p in sorted((tmp_path / "sheet").glob("[0-9]*.png"))] == [
        "01-0001.500s.png",
        "02-0000.250s.png",
        "03-0001.500s.png",
    ]
    caller.close()
    single = compiled.storyboard(iter([0.25]), tmp_path / "single", size=(160, 90), columns=4)
    assert single["settings"]["columns"] == 1


def test_export_cancellation_preserves_destination_and_recovers(tmp_path, monkeypatch):
    compiled = compiled_video()
    settings = ExportSettings(width=160, height=90, fps=10, antialias=1, preset="ultrafast")
    output = tmp_path / "clip.mp4"
    output.write_bytes(b"previous artifact")
    session = Session(1)
    monkeypatch.setattr(rendering, "create_renderer", lambda *args, **kwargs: session)
    with pytest.raises(CancelledError):
        compiled.export(output, settings=settings, overwrite=True, cancel=lambda: True)
    assert session.closed and output.read_bytes() == b"previous artifact"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["clip.mp4"]
    monkeypatch.undo()
    progress = []
    result = compiled.export(
        output,
        settings=settings,
        start_time=0.5,
        end_time=1,
        overwrite=True,
        progress=lambda a, b: progress.append((a, b)),
    )
    assert result["source_range"] == [0.5, 1] and progress[-1] == (5, 5)
    assert result["settings"]["width"] == 160 and result["settings"]["fps"] == 10
    assert any(s["codec_type"] == "video" for s in media_probe(output)["streams"])
    with pytest.raises(FileExistsError):
        compiled.export(output, settings=settings)


def test_invalid_samples_and_static_capabilities(tmp_path):
    compiled = compiled_video()
    for time in (-1, float("nan"), compiled.duration):
        with pytest.raises(ValueError):
            compiled.frame(time, size=(160, 90))
    result = public_capabilities()
    assert "CompiledVideo" in result["packages"]["facelesschamp_kit"]["exports"]
    assert "ChessChamp" not in str(result)
    json.dumps(result)
