"""Chess rules, source-clock playback, JSON diagnostics, and renderer contracts."""

import builtins
import json
from copy import deepcopy
from dataclasses import replace

import pytest

from faceless_champ import Canvas, ChessChamp, ChessScript, ChessTheme, Group, PillowRenderer, RectangleMask, Scene
from faceless_champ.chess import ChessDataError


@pytest.fixture(autouse=True)
def rules_dependency():
    pytest.importorskip("chess")


def data(moves=(), **kwargs):
    return {
        "schema_version": 1,
        "duration": max(4, len(moves) * 2 + 1),
        "moves": [{"at": i * 2 + 1, "duration": 0.5, "uci": move} for i, move in enumerate(moves)],
        **kwargs,
    }


def test_capture_commits_on_arrival_and_seeking_is_independent():
    script = ChessScript.from_dict(data(["e2e4", "d7d5", "e4d5"]))
    before = script.position_at(5.49)
    after = script.position_at(5.5)
    assert len(before.pieces) == 32 and len(after.pieces) == 31
    assert dict(before.pieces)[35] == "p"
    assert dict(after.pieces)[35] == "P"
    assert before.turn == "white" and after.turn == "black"
    assert after.san == "exd5"
    assert script.position_at(0) == script.initial
    assert script.position_at(99) == after
    assert deepcopy(script).position_at(5.5) == after
    assert script.active_move(1).uci == "e2e4"
    assert script.active_move(1.5) is None


@pytest.mark.parametrize(
    "uci,origins,destinations",
    [
        ("e1g1", (4, 7), (6, 5)),
        ("e1c1", (4, 0), (2, 3)),
        ("e8g8", (60, 63), (62, 61)),
        ("e8c8", (60, 56), (58, 59)),
    ],
)
def test_castling_animates_both_pieces(uci, origins, destinations):
    turn = "w" if uci[1] == "1" else "b"
    script = ChessScript(data([uci], initial_fen=f"r3k2r/8/8/8/8/8/8/R3K2R {turn} KQkq - 0 1"))
    move = script.active_move(1.25)
    assert tuple(m[0] for m in move.moving) == origins
    assert tuple(m[1] for m in move.moving) == destinations
    assert all(s not in dict(move.after.pieces) for s in origins)
    assert all(s in dict(move.after.pieces) for s in destinations)


def test_en_passant_removes_captured_pawn_on_arrival():
    script = ChessScript(data(["e5d6"], initial_fen="4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2"))
    assert 35 in dict(script.position_at(1.49).pieces)
    after = dict(script.position_at(1.5).pieces)
    assert 35 not in after and after[43] == "P"


@pytest.mark.parametrize("promotion", ["q", "r", "b", "n"])
def test_promotion_keeps_pawn_until_arrival(promotion):
    script = ChessScript(data(["a7a8" + promotion], initial_fen="7k/P7/8/8/8/8/8/7K w - - 0 1"))
    assert script.active_move(1.25).moving[0][2] == "P"
    assert dict(script.position_at(1.5).pieces)[56] == promotion.upper()


def test_check_and_checkmate_and_reject_following_move():
    script = ChessScript(data(["f2f3", "e7e5", "g2g4", "d8h4"]))
    final = script.position_at(8)
    assert final.status == "Checkmate" and final.check_square == 4 and final.san == "Qh4#"
    with pytest.raises(ChessDataError, match="already ended") as error:
        ChessScript(data(["f2f3", "e7e5", "g2g4", "d8h4", "a2a3"]))
    assert error.value.move_index == 4


@pytest.mark.parametrize(
    "fen,status",
    [
        ("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", "Stalemate"),
        ("7k/8/8/8/8/8/8/K7 w - - 0 1", "Draw"),
        ("7k/8/8/8/8/8/R7/K7 w - - 150 80", "Draw"),
    ],
)
def test_terminal_positions(fen, status):
    assert ChessScript(data(initial_fen=fen)).initial.status == status
    with pytest.raises(ChessDataError, match="already ended"):
        ChessScript(data(["a1b1"], initial_fen=fen))


def test_fivefold_repetition_is_automatic_but_threefold_is_not():
    cycle = ["g1f3", "g8f6", "f3g1", "f6g8"]
    assert ChessScript(data(cycle * 2)).position_at(100).status == ""
    assert ChessScript(data(cycle * 4)).position_at(100).status == "Draw"
    with pytest.raises(ChessDataError, match="already ended"):
        ChessScript(data(cycle * 4 + ["e2e4"]))


@pytest.mark.parametrize("moves", [["e7e5"], ["e2e5"], ["e2e4", "e4e5"], ["0000"], ["a7a8"]])
def test_illegal_moves_report_path_and_index(moves):
    with pytest.raises(ChessDataError) as error:
        ChessScript(data(moves))
    assert error.value.path.endswith(".uci") and error.value.move_index is not None


@pytest.mark.parametrize(
    "patch,path",
    [
        ({"schema_version": True}, "schema_version"),
        ({"schema_version": 2}, "schema_version"),
        ({"duration": 0}, "duration"),
        ({"duration": float("nan")}, "duration"),
        ({"duration": 10**400}, "duration"),
        ({"orientation": "sideways"}, "orientation"),
        ({"initial_fen": "bad"}, "initial_fen"),
        ({"initial_fen": "8/8/8/8/8/8/8/8 w - - 0 1"}, "initial_fen"),
        ({"players": {"white": ""}}, "players.white"),
        ({"moves": {}}, "moves"),
        ({"extra": 1}, "extra"),
        ({"narration": {}}, "narration.audio"),
    ],
)
def test_invalid_configuration(patch, path):
    with pytest.raises(ChessDataError) as error:
        ChessScript(data() | patch)
    assert path in error.value.path


@pytest.mark.parametrize("at,duration", [(1.2, 0.5), (0, 0.5), (3, 2), (3, 0), (True, 1)])
def test_timing_validation(at, duration):
    value = data(["e2e4", "e7e5"], duration=4)
    value["moves"][1].update(at=at, duration=duration)
    with pytest.raises(ChessDataError):
        ChessScript(value)


def test_annotations_half_open_overlaps_and_invalid_squares():
    note = {"type": "text", "at": 0, "duration": 1, "text": "Look here"}
    arrow = {"type": "arrow", "at": 0, "duration": 2, "from": "e2", "to": "e4"}
    value = data(annotations=[note, dict(note, at=1), arrow])
    script = ChessScript(value)
    assert len(script.annotations_at(0)) == 2
    assert len(script.annotations_at(1)) == 2
    assert script.annotations_at(2) == ()
    for annotation in [
        dict(note, at=0.5),
        dict(arrow, to="e9"),
        dict(arrow, to="e2"),
        dict(note, color="not-a-color"),
        {"type": "highlight", "at": 0, "duration": 1, "squares": []},
    ]:
        with pytest.raises(ChessDataError):
            ChessScript(data(annotations=[note, annotation]))


def test_json_file_required_and_diagnostics(tmp_path):
    with pytest.raises(ChessDataError, match="cannot read"):
        ChessScript.from_json(tmp_path / "data.json")
    path = tmp_path / "data.json"
    path.write_text("{")
    with pytest.raises(ChessDataError, match="cannot read"):
        ChessScript.from_json(path)
    path.write_text(json.dumps(data()))
    assert ChessScript.from_json(path).duration == 4


def test_optional_dependency_error(monkeypatch):
    original = builtins.__import__

    def missing(name, *args, **kwargs):
        if name == "chess":
            raise ImportError("missing")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing)
    with pytest.raises(ImportError, match=r"faceless-champ\[chess\]"):
        ChessScript(data())


def test_layout_orientation_and_source_offset():
    script = ChessScript(data(["e2e4"]))
    board = ChessChamp(script, width=900, height=600)
    reverse = ChessChamp(ChessScript(data(orientation="black")), width=900, height=600)
    assert board.square_center("a1") == reverse.square_center("h8")
    offset = ChessChamp(script, width=900, height=600, source_start=1)
    assert board.frame_image(1.25).tobytes() == offset.frame_image(0.25).tobytes()
    with pytest.raises(ValueError, match="source_start"):
        ChessChamp(script, source_start=99)
    with pytest.raises(ValueError, match="cannot fit"):
        ChessChamp(ChessScript(data(players={"white": "X" * 300})))
    with pytest.raises(ValueError, match="cannot fit"):
        ChessChamp(ChessScript(data(annotations=[{"type": "text", "at": 0, "duration": 1, "text": "X" * 500}])))


def test_renderer_cache_transforms_masks_and_random_access():
    board = ChessChamp(ChessScript(data(["e2e4", "d7d5", "e4d5"])), width=900, height=600)
    board.mask = RectangleMask(width=900, height=600)
    group = Group(board, position=(480, 320), scale=0.9, rotation=2, opacity=0.9)
    scene = Scene(Canvas(960, 640))
    scene.add(group)
    scene.wait(8)
    cached, uncached = PillowRenderer(1), PillowRenderer(1, frame_cache_mb=0)
    cached.validate(scene)
    originals = {}
    for t in (0, 1.25, 1.5, 5.25, 5.5, 7, 1.25, 0):
        frame = cached.frame(scene, t, (480, 320)).tobytes()
        assert frame == uncached.frame(scene, t, (480, 320)).tobytes()
        if t in originals:
            assert frame == originals[t]
        originals[t] = frame
    assert originals[0] != originals[1.25] != originals[1.5]
    assert scene.bounds_at(board, 0) == scene.bounds_at(board, 5)


def test_theme_is_immutable_and_portrait_renders():
    theme = replace(ChessTheme(), accent="#FF0000")
    board = ChessChamp(ChessScript(data()), width=952, height=1792, theme=theme)
    assert board.frame_image(0, 0.25).size == (238, 448)
    assert deepcopy(theme) == theme


def make_artwork(directory, *, grid=(4, 4, 36, 36)):
    from PIL import Image, ImageDraw

    from faceless_champ.chess_assets import PIECE_FILES

    directory.mkdir()
    Image.new("RGB", (40, 40), "#284664").save(directory / "chessboard.png")
    for symbol, filename in PIECE_FILES.items():
        image = Image.new("RGBA", (20, 30))
        image.putpixel((0, 0), (255, 0, 0, 1))
        ImageDraw.Draw(image).rectangle((6, 4, 13, 25), fill="white" if symbol.isupper() else "black")
        image.save(directory / filename)
    return directory, grid


def test_artwork_mapping_inner_board_geometry_and_snapshots(tmp_path):
    from faceless_champ import ChessAssets

    folder, grid = make_artwork(tmp_path / "pieces")
    artwork = ChessAssets(folder, board_grid=grid)
    board = ChessChamp(ChessScript(data()), width=900, height=600, assets=artwork)
    white, black = board.square_center("a1"), board.square_center("a8")
    first = board.frame_image(0)
    assert first.getpixel(tuple(round(v) for v in white))[:3] == (255, 255, 255)
    assert first.getpixel(tuple(round(v) for v in black))[:3] == (0, 0, 0)
    assert board._grid_size == pytest.approx(board.board_size * 0.8)
    assert deepcopy(artwork) is artwork
    (folder / "white-rook.png").unlink()
    assert board.frame_image(0).tobytes() == first.tobytes()
    with pytest.raises(ValueError, match="white-rook.png"):
        ChessAssets(folder, board_grid=grid)
    assert artwork._cache_bytes <= artwork._cache_limit
    checksums = artwork.checksums
    checksums.clear()
    assert len(artwork.checksums) == 13


def test_asymmetric_board_grid_rotates_with_artwork(tmp_path):
    from faceless_champ import ChessAssets

    folder, _ = make_artwork(tmp_path / "pieces")
    artwork = ChessAssets(folder, board_grid=(2, 3, 26, 27))
    white = ChessChamp(ChessScript(data()), width=900, height=600, assets=artwork)
    black = ChessChamp(ChessScript(data(orientation="black")), width=900, height=600, assets=artwork)
    origin = (white.board_x, white.board_y)
    first = white.square_center("a1")
    second = black.square_center("a1")
    assert first[0] + second[0] == pytest.approx(2 * origin[0] + white.board_size)
    assert first[1] + second[1] == pytest.approx(2 * origin[1] + white.board_size)


@pytest.mark.parametrize("grid", [(0, 0, 50, 50), (4, 4, 30, 36), (0, 0, 0, 0), (1, 2, 3)])
def test_invalid_board_grid_fails_before_render(tmp_path, grid):
    from faceless_champ import ChessAssets

    folder, _ = make_artwork(tmp_path / "pieces")
    with pytest.raises(ValueError, match="board_grid"):
        ChessAssets(folder, board_grid=grid)


def test_san_pgn_import_result_and_json_roundtrip():
    notation = "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1/2-1/2"
    script = ChessScript.from_pgn(notation, move_duration=0.5, move_interval=1)
    assert len(script.moves) == 6
    assert script.moves[0].uci == "e2e4"
    assert script.moves[-1].after.san == "a6"
    assert script.result == "1/2-1/2" and script.duration == 8.5
    assert ChessScript.from_dict(script.to_dict()) == script
    board = ChessChamp(script)
    assert board.frame_image(6.6).tobytes() == board.frame_image(8).tobytes()


def test_pgn_and_json_roundtrip_preserves_castling_and_metadata():
    pgn = '[White "Fixture White"]\n[Black "Fixture Black"]\n[Result "1/2-1/2"]\n\n'
    pgn += "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 O-O 1/2-1/2"
    script = ChessScript.from_pgn(pgn)
    assert ChessScript.from_dict(script.to_dict()) == script
    assert len(script.moves) == 14 and script.moves[-1].after.san == "O-O"
    assert len([move for move in script.moves if len(move.moving) == 2]) == 2
    assert script.players == ("Fixture White", "Fixture Black")
    assert script.result == "1/2-1/2"


def test_pgn_import_illegal_move_and_timing_errors():
    with pytest.raises(ChessDataError, match="illegal"):
        ChessScript.from_pgn("1. e5 *")
    with pytest.raises(ChessDataError, match="at least"):
        ChessScript.from_pgn("1. e4 *", move_duration=1, move_interval=0.5)
    with pytest.raises(ChessDataError, match="one game"):
        ChessScript.from_pgn("1. e4 *\n\n1. d4 *")


def test_asset_directory_resolves_relative_to_data_json(tmp_path):
    from faceless_champ import ChessAssets

    folder, grid = make_artwork(tmp_path / "pieces")
    value = data(assets={"directory": "pieces", "board_grid": list(grid)})
    path = tmp_path / "data.json"
    path.write_text(json.dumps(value))
    script = ChessScript.from_json(path)
    assert script.asset_directory == folder
    assert ChessChamp(script).assets.checksums == ChessAssets(folder, board_grid=grid).checksums
