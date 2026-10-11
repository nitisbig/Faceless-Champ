"""Data-driven chess scaffolding, composition, diagnostics and narration."""

import builtins
import json
import wave
from types import SimpleNamespace

import pytest
from faceless_champ import Canvas, ChessScript, PillowRenderer

from facelesschamp_kit import BuildContext, KitError, Project, Video
from facelesschamp_kit.blocks import ChessBoard
from facelesschamp_kit.cli import main
from facelesschamp_kit.scaffold import init_project
from facelesschamp_kit.templates import chesschamp


@pytest.fixture(autouse=True)
def rules_dependency():
    pytest.importorskip("chess")


def script():
    return ChessScript({"schema_version": 1, "duration": 3, "moves": [{"at": 1, "duration": 0.5, "uci": "e2e4"}]})


def audio(root, duration=4):
    path = root / "voice.wav"
    with wave.open(str(path), "wb") as out:
        out.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
        out.writeframes(b"\0\0" * int(8000 * duration))
    return path


@pytest.mark.parametrize("canvas", [Canvas(1920, 1080), Canvas(1080, 1920)])
def test_block_layout_named_child_and_fresh_instances(tmp_path, canvas):
    ctx = BuildContext(tmp_path, canvas=canvas)
    block = ChessBoard(script())
    a, b = block.compose(ctx, ctx.bounds), block.compose(ctx, ctx.bounds)
    assert a.root is not b.root and a.children["board"] is a.root
    assert a.bounds == ctx.bounds
    video = Video(ctx)
    video.segment("board", duration=3).add(block)
    compiled = video.compile()
    PillowRenderer(1).frame(compiled.composition, 1.25, (384, 216))


def test_playback_overflow_including_audio_tail(tmp_path):
    for voice in (None, SimpleNamespace(duration=8, track=None)):
        video = Video(BuildContext(tmp_path))
        video.voice = voice
        video.segment("board", duration=2).add(ChessBoard(script()))
        with pytest.raises(KitError, match="MOTION_WINDOW"):
            video.compile()


def test_delayed_placement_and_source_offset(tmp_path):
    video = Video(BuildContext(tmp_path, canvas=Canvas(1920, 1080)))
    video.segment("board", start=3, duration=3).add(ChessBoard(script(), source_start=1), at=1, duration=2)
    compiled = video.compile()
    renderer = PillowRenderer(1)
    assert (
        renderer.frame(compiled.composition, 4.1, (384, 216)).tobytes()
        != renderer.frame(compiled.composition, 4.5, (384, 216)).tobytes()
    )


def test_scaffold_build_fingerprint_and_cli(tmp_path, capsys):
    root = init_project(tmp_path / "demo", "chesschamp")
    assert (root / "data.json").is_file()
    assert "facelesschamp-kit[chess]" in (root / "pyproject.toml").read_text()
    assert "landscape" in (root / "facelesschamp.toml").read_text()
    first = Project(root).build("main")
    assert first.duration == 10
    value = json.loads((root / "data.json").read_text())
    value["players"]["white"] = "New name"
    (root / "data.json").write_text(json.dumps(value))
    assert Project(root).build("main").report["fingerprint"] != first.report["fingerprint"]
    assert main(["--project", str(root), "validate", "main", "--json"]) == 0
    assert '"duration": 10' in capsys.readouterr().out
    value["moves"][0]["uci"] = "e2e5"
    (root / "data.json").write_text(json.dumps(value))
    assert main(["--project", str(root), "validate", "main", "--json"]) == 1
    error = json.loads(capsys.readouterr().err)["error"]
    assert error["code"] == "CHESS_DATA"
    assert error["field"] == "$.moves[0].uci" and error["move_index"] == 0


def test_missing_json_and_dependency_diagnostics(tmp_path, monkeypatch):
    ctx = BuildContext(tmp_path)
    with pytest.raises(KitError, match="CHESS_DATA"):
        chesschamp(ctx)
    (tmp_path / "data.json").write_text('{"schema_version":1,"duration":2,"moves":[]}')
    original = builtins.__import__

    def missing(name, *args, **kwargs):
        if name == "chess":
            raise ImportError("missing")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing)
    with pytest.raises(KitError, match="CHESS_DEPENDENCY"):
        chesschamp(ctx)


def test_audio_only_once_at_zero_and_final_hold(tmp_path):
    path = audio(tmp_path)
    video = Video(BuildContext(tmp_path, canvas=Canvas(1920, 1080)))
    voice = video.narration(audio=path)
    segment = video.segment("board", duration=3)
    segment.add(ChessBoard(script()))
    compiled = video.compile()
    assert compiled.duration == 4
    assert len(compiled.composition.audio) == 1
    assert compiled.composition.audio[0].start == 0
    assert compiled.report["narration"]["subtitle_checksum"] is None
    assert compiled.report["narration"]["cues"] == []
    assert compiled.report["diagnostics"][0]["code"] == "AUDIO_TAIL_HOLD"
    renderer = PillowRenderer(1)
    assert (
        renderer.frame(compiled.composition, 3, (384, 216)).tobytes()
        == renderer.frame(compiled.composition, 3.9, (384, 216)).tobytes()
    )
    with pytest.raises(KitError, match="subtitles"):
        voice.between("start")
    with pytest.raises(KitError, match="subtitles"):
        segment.cue_time(1)
    with pytest.raises(KitError, match="one master"):
        video.narration(audio=path)


def test_audio_only_caption_and_marker_guards(tmp_path):
    path = audio(tmp_path)
    for options in ({"captions": True}, {"markers": {"start": 1}}):
        video = Video(BuildContext(tmp_path))
        with pytest.raises(KitError, match="subtitles"):
            video.narration(audio=path, **options)
        assert video.voice is None
    video = Video(BuildContext(tmp_path))
    video.narration(audio=path)
    video.segment("board", duration=3).add(ChessBoard(script()))
    video.context.captions = True
    with pytest.raises(KitError, match="subtitles"):
        video.compile()


def test_template_resolves_audio_asset(tmp_path):
    root = init_project(tmp_path / "demo", "chesschamp")
    audio(root, duration=11)
    (root / "assets/manifest.json").write_text(json.dumps({"voice": {"type": "audio", "path": "voice.wav"}}))
    value = json.loads((root / "data.json").read_text())
    value["narration"] = {"audio": "voice"}
    (root / "data.json").write_text(json.dumps(value))
    compiled = Project(root).build("main")
    assert compiled.duration == 11 and len(compiled.composition.audio) == 1
    assert compiled.report["narration"]["audio_checksum"]
