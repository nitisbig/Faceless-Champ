"""Validated chess scripts and deterministic, offline tutorial board rendering.

The optional ``chess`` rules package is imported only when constructing a script.
"""

from __future__ import annotations

import json
import math
from bisect import bisect_right
from dataclasses import dataclass, fields
from functools import lru_cache
from io import StringIO
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw

from .chess_assets import ChessAssets
from .components import Component, finite
from .typography import load_font


@lru_cache(maxsize=64)
def _font(size):
    return load_font(None, size)


class ChessDataError(ValueError):
    """Invalid chess input, with a JSON field path and optional zero-based move index."""

    def __init__(self, path, message, move_index=None):
        self.path, self.move_index = path, move_index
        super().__init__(f"{path}: {message}")


def _object(value, allowed, path, required=()):
    if not isinstance(value, dict):
        raise ChessDataError(path, "expected an object")
    for key in value:
        if key not in allowed:
            raise ChessDataError(f"{path}.{key}", "unknown field")
    for key in required:
        if key not in value:
            raise ChessDataError(f"{path}.{key}", "required field")


def _number(value, path, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ChessDataError(path, "expected a finite number")
    try:
        value = float(value)
    except OverflowError as exc:
        raise ChessDataError(path, "expected a finite number") from exc
    if not math.isfinite(value):
        raise ChessDataError(path, "expected a finite number")
    if value < 0 or (positive and value == 0):
        raise ChessDataError(path, "must be positive" if positive else "must be nonnegative")
    return float(value)


def _text(value, path):
    if not isinstance(value, str) or not value.strip():
        raise ChessDataError(path, "expected nonempty text")
    return value


def _square(value, path):
    if not isinstance(value, str) or len(value) != 2 or value[0] not in "abcdefgh" or value[1] not in "12345678":
        raise ChessDataError(path, "expected a square such as e4")
    return (int(value[1]) - 1) * 8 + ord(value[0]) - ord("a")


@dataclass(frozen=True)
class ChessPosition:
    pieces: tuple[tuple[int, str], ...]
    fen: str
    turn: str
    check_square: int | None
    status: str
    san: str = ""


def _position(board, san=""):
    outcome = board.outcome(claim_draw=False)
    status = (
        "Checkmate"
        if board.is_checkmate()
        else "Stalemate"
        if board.is_stalemate()
        else "Draw"
        if outcome
        else "Check"
        if board.is_check()
        else ""
    )
    return ChessPosition(
        tuple(sorted((square, piece.symbol()) for square, piece in board.piece_map().items())),
        board.fen(),
        "white" if board.turn else "black",
        board.king(board.turn) if board.is_check() else None,
        status,
        san,
    )


@dataclass(frozen=True)
class ChessMove:
    at: float
    duration: float
    uci: str
    before: ChessPosition
    after: ChessPosition
    moving: tuple[tuple[int, int, str], ...]

    @property
    def end(self):
        return self.at + self.duration


@dataclass(frozen=True)
class ChessAnnotation:
    type: str
    at: float
    duration: float
    text: str = ""
    squares: tuple[int, ...] = ()
    color: str | None = None


@dataclass(frozen=True, init=False)
class ChessScript:
    duration: float
    players: tuple[str, str]
    orientation: str
    initial: ChessPosition
    moves: tuple[ChessMove, ...]
    annotations: tuple[ChessAnnotation, ...]
    audio: str | None
    result: str
    asset_directory: Path | None
    board_grid: tuple | None

    def __init__(self, data, *, base_path=None):
        try:
            import chess
        except ImportError as exc:
            raise ImportError("ChessChamp requires pip install 'faceless-champ[chess]'") from exc
        _object(
            data,
            {
                "schema_version",
                "duration",
                "players",
                "orientation",
                "initial_fen",
                "moves",
                "annotations",
                "narration",
                "result",
                "assets",
            },
            "$",
            ("schema_version", "duration", "moves"),
        )
        if type(data["schema_version"]) is not int or data["schema_version"] != 1:
            raise ChessDataError("$.schema_version", "expected version 1")
        duration = _number(data["duration"], "$.duration", True)
        players = data.get("players", {})
        _object(players, {"white", "black"}, "$.players")
        names = tuple(_text(players.get(side, side.title()), f"$.players.{side}") for side in ("white", "black"))
        orientation = data.get("orientation", "white")
        if orientation not in ("white", "black"):
            raise ChessDataError("$.orientation", "expected white or black")
        fen = _text(data.get("initial_fen", chess.STARTING_FEN), "$.initial_fen")
        try:
            board = chess.Board(fen)
            if not board.is_valid():
                raise ValueError("invalid standard chess position")
        except ValueError as exc:
            raise ChessDataError("$.initial_fen", str(exc)) from exc
        result = data.get("result", "*")
        if result not in ("*", "1-0", "0-1", "1/2-1/2"):
            raise ChessDataError("$.result", "expected *, 1-0, 0-1, or 1/2-1/2")
        asset_directory, board_grid = None, None
        if "assets" in data:
            artwork = data["assets"]
            _object(artwork, {"directory", "board_grid"}, "$.assets", ("directory",))
            directory = _text(artwork["directory"], "$.assets.directory")
            asset_directory = ((Path(base_path) if base_path is not None else Path.cwd()) / directory).resolve()
            if "board_grid" in artwork:
                values = artwork["board_grid"]
                if not isinstance(values, list) or len(values) != 4:
                    raise ChessDataError("$.assets.board_grid", "expected [left, top, right, bottom] in image pixels")
                board_grid = tuple(_number(v, f"$.assets.board_grid[{i}]") for i, v in enumerate(values))
        initial = _position(board)
        if not isinstance(data["moves"], list):
            raise ChessDataError("$.moves", "expected an array")
        moves, previous_end = [], 0
        for index, item in enumerate(data["moves"]):
            path = f"$.moves[{index}]"
            try:
                _object(item, {"at", "duration", "uci"}, path, ("at", "duration", "uci"))
                at = _number(item["at"], path + ".at")
                run = _number(item["duration"], path + ".duration", True)
                if at < previous_end or at + run > duration:
                    raise ChessDataError(path + ".at", "moves must be ordered, non-overlapping, and within duration")
                uci = _text(item["uci"], path + ".uci")
                if board.is_game_over(claim_draw=False):
                    raise ChessDataError(path + ".uci", "game has already ended")
                try:
                    move = board.parse_uci(uci)
                    if not move or not board.is_legal(move):
                        raise ValueError("illegal move")
                except ValueError as exc:
                    raise ChessDataError(path + ".uci", str(exc)) from exc
                before = _position(board, moves[-1].after.san if moves else "")
                san = board.san(move)
                moving = [(move.from_square, move.to_square, board.piece_at(move.from_square).symbol())]
                if board.is_castling(move):
                    rank = chess.square_rank(move.from_square)
                    kingside = board.is_kingside_castling(move)
                    origin, destination = (
                        chess.square(7 if kingside else 0, rank),
                        chess.square(5 if kingside else 3, rank),
                    )
                    moving.append((origin, destination, board.piece_at(origin).symbol()))
                board.push(move)
                moves.append(ChessMove(at, run, uci, before, _position(board, san), tuple(moving)))
                previous_end = at + run
            except ChessDataError as exc:
                exc.move_index = index
                raise
        annotations = data.get("annotations", [])
        if not isinstance(annotations, list):
            raise ChessDataError("$.annotations", "expected an array")
        parsed, text_windows = [], []
        for index, item in enumerate(annotations):
            path = f"$.annotations[{index}]"
            if not isinstance(item, dict) or item.get("type") not in ("text", "arrow", "highlight"):
                raise ChessDataError(path + ".type", "expected text, arrow, or highlight")
            kind = item["type"]
            extra = {"text"} if kind == "text" else {"from", "to"} if kind == "arrow" else {"squares"}
            _object(item, {"type", "at", "duration", "color"} | extra, path, {"at", "duration"} | extra)
            at, run = _number(item["at"], path + ".at"), _number(item["duration"], path + ".duration", True)
            if at + run > duration:
                raise ChessDataError(path + ".duration", "annotation exceeds script duration")
            color = item.get("color")
            if color is not None:
                try:
                    ImageColor.getcolor(color, "RGBA")
                except (ValueError, TypeError, AttributeError) as exc:
                    raise ChessDataError(path + ".color", "expected a Pillow color string") from exc
            text, squares = "", ()
            if kind == "text":
                text = _text(item["text"], path + ".text")
                if any(at < end and start < at + run for start, end in text_windows):
                    raise ChessDataError(path + ".at", "commentary text intervals overlap")
                text_windows.append((at, at + run))
            elif kind == "arrow":
                squares = (_square(item["from"], path + ".from"), _square(item["to"], path + ".to"))
                if squares[0] == squares[1]:
                    raise ChessDataError(path + ".to", "arrow endpoints must differ")
            else:
                if not isinstance(item["squares"], list) or not item["squares"]:
                    raise ChessDataError(path + ".squares", "expected a nonempty array of squares")
                squares = tuple(_square(s, f"{path}.squares[{i}]") for i, s in enumerate(item["squares"]))
            parsed.append(ChessAnnotation(kind, at, run, text, squares, color))
        audio = None
        if "narration" in data:
            _object(data["narration"], {"audio"}, "$.narration", ("audio",))
            audio = _text(data["narration"]["audio"], "$.narration.audio")
        for name, value in (
            ("duration", duration),
            ("players", names),
            ("orientation", orientation),
            ("initial", initial),
            ("moves", tuple(moves)),
            ("annotations", tuple(parsed)),
            ("audio", audio),
            ("result", result),
            ("asset_directory", asset_directory),
            ("board_grid", board_grid),
        ):
            object.__setattr__(self, name, value)
        object.__setattr__(self, "_ends", tuple(move.end for move in moves))

    @classmethod
    def from_dict(cls, data, *, base_path=None):
        return cls(data, base_path=base_path)

    @classmethod
    def from_json(cls, path):
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as exc:
            raise ChessDataError("$", f"cannot read {path}: {exc}") from exc
        return cls(data, base_path=Path(path).resolve().parent)

    @classmethod
    def from_pgn(cls, pgn, *, move_duration=0.45, move_interval=0.7, lead_in=1, tail=2, players=None):
        """Import SAN/PGN mainline notation into the same validated timed model."""
        try:
            import chess.pgn
        except ImportError as exc:
            raise ImportError("ChessChamp requires pip install 'faceless-champ[chess]'") from exc
        _text(pgn, "$.pgn")
        run = _number(move_duration, "$.timing.move_duration", True)
        interval = _number(move_interval, "$.timing.move_interval", True)
        lead, hold = _number(lead_in, "$.timing.lead_in"), _number(tail, "$.timing.tail")
        if interval < run:
            raise ChessDataError("$.timing.move_interval", "must be at least move_duration")

        class StrictGame(chess.pgn.GameBuilder):
            def handle_error(self, error):
                raise ChessDataError("$.pgn", str(error), len(list(self.game.mainline_moves()))) from error

        stream = StringIO(pgn)
        game = chess.pgn.read_game(stream, Visitor=StrictGame)
        if game is None:
            raise ChessDataError("$.pgn", "expected a game")
        if chess.pgn.read_game(stream, Visitor=StrictGame) is not None:
            raise ChessDataError("$.pgn", "provide one game at a time")
        moves = [
            {"at": round(lead + i * interval, 9), "duration": run, "uci": move.uci()}
            for i, move in enumerate(game.mainline_moves())
        ]
        duration = (moves[-1]["at"] + run if moves else lead) + hold
        return cls.from_dict(
            {
                "schema_version": 1,
                "duration": duration,
                "moves": moves,
                "players": players
                or {
                    "white": game.headers.get("White", "White").replace("?", "White"),
                    "black": game.headers.get("Black", "Black").replace("?", "Black"),
                },
                "initial_fen": game.board().fen(),
                "result": game.headers.get("Result", "*"),
            }
        )

    def to_dict(self):
        """Serialize a script to the required data.json format (including imported games)."""
        data = {
            "schema_version": 1,
            "duration": self.duration,
            "players": dict(zip(("white", "black"), self.players)),
            "orientation": self.orientation,
            "initial_fen": self.initial.fen,
            "result": self.result,
            "moves": [{"at": m.at, "duration": m.duration, "uci": m.uci} for m in self.moves],
        }

        def name(square):
            return chr(97 + square % 8) + str(square // 8 + 1)

        annotations = []
        for a in self.annotations:
            item = {"type": a.type, "at": a.at, "duration": a.duration}
            if a.type == "text":
                item["text"] = a.text
            elif a.type == "arrow":
                item.update({"from": name(a.squares[0]), "to": name(a.squares[1])})
            else:
                item["squares"] = [name(square) for square in a.squares]
            if a.color is not None:
                item["color"] = a.color
            annotations.append(item)
        data["annotations"] = annotations
        if self.audio is not None:
            data["narration"] = {"audio": self.audio}
        if self.asset_directory is not None:
            data["assets"] = {"directory": str(self.asset_directory)}
            if self.board_grid is not None:
                data["assets"]["board_grid"] = list(self.board_grid)
        return data

    def position_at(self, time):
        """Logical position; the moving piece commits on arrival."""
        index = bisect_right(self._ends, finite(time, "time", 0))
        return self.moves[index - 1].after if index else self.initial

    def active_move(self, time):
        index = bisect_right(self._ends, time)
        return self.moves[index] if index < len(self.moves) and self.moves[index].at <= time else None

    def annotations_at(self, time):
        return tuple(a for a in self.annotations if a.at <= time < a.at + a.duration)


@dataclass(frozen=True)
class ChessTheme:
    light: str = "#EEEED2"
    dark: str = "#769656"
    background: str = "#171E1A"
    panel: str = "#232E27"
    foreground: str = "#F4F3E9"
    muted: str = "#BAC6B6"
    accent: str = "#F5C85B"
    check: str = "#E96355"
    white_piece: str = "#FFFCF1"
    black_piece: str = "#202822"

    def __post_init__(self):
        for field in fields(self):
            ImageColor.getcolor(getattr(self, field.name), "RGBA")


class ChessChamp(Component):
    """Square board and measured commentary panel with random-access playback."""

    def __init__(self, script, *, width=1600, height=900, source_start=0, theme=None, assets=None, **kwargs):
        super().__init__(**kwargs)
        if not isinstance(script, ChessScript):
            raise TypeError("script must be a ChessScript")
        self.script = script
        self.width, self.height = finite(width, "width", 360), finite(height, "height", 360)
        self.source_start = finite(source_start, "source_start", 0)
        self.duration = script.duration
        if self.source_start > self.duration:
            raise ValueError("source_start exceeds script duration")
        self.theme = ChessTheme() if theme is None else theme
        if not isinstance(self.theme, ChessTheme):
            raise TypeError("theme must be a ChessTheme")
        if assets is not None and not isinstance(assets, ChessAssets):
            raise TypeError("assets must be ChessAssets or None")
        self.assets = assets or (
            ChessAssets(script.asset_directory, board_grid=script.board_grid)
            if script.asset_directory is not None
            else ChessAssets.bundled()
        )
        self._layout()
        # Preflight every authored label; nothing wraps or shrinks during playback.
        self._labels = {name: self._fit(name, self.board_size, self.label_height, 30) for name in script.players}
        self._comments = {
            a.text: self._fit(a.text, self.panel_box[2] - 40, self.panel_box[3] - 130, 34)
            for a in script.annotations
            if a.type == "text"
        }

        self._headers = {
            side: self._fit(side.title() + " to move", self.panel_box[2] - 40, 45, 28) for side in ("white", "black")
        }
        self._headers["over"] = self._fit("Game over", self.panel_box[2] - 40, 45, 28)
        self._statuses = {}
        for state in (script.initial, *(move.after for move in script.moves)):
            status = " · ".join(filter(None, (state.san, state.status))) or "Starting position"
            self._statuses[status] = self._fit(status, self.panel_box[2] - 40, 55, 26)

        self._result_label = None
        if script.result != "*":
            result = {"1/2-1/2": "Draw · ½–½", "1-0": "White wins · 1–0", "0-1": "Black wins · 0–1"}[script.result]
            self._result_label = self._fit(result, self.panel_box[2] - 40, 55, 26)
        self._histories = {}
        for completed in range(1, len(script.moves) + 1):
            rows, previous_number = [], None
            for record in script.moves[max(0, completed - 10) : completed]:
                number = int(record.before.fen.split()[5])
                if record.before.turn == "white":
                    rows.append(f"{number}.  {record.after.san}")
                elif rows and previous_number == number:
                    rows[-1] += f"   {record.after.san}"
                else:
                    rows.append(f"{number}...  {record.after.san}")
                previous_number = number
            self._histories[completed] = self._fit("\n".join(rows), self.panel_box[2] - 40, self.panel_box[3] - 140, 28)

    def _layout(self):
        w, h = self.width, self.height
        margin = 28
        landscape = w >= h * 1.2
        self.board_size = min(h - 160, w * 0.62 - 2 * margin) if landscape else min(w - 2 * margin, h * 0.58 - 110)
        if self.board_size < 200:
            raise ValueError("ChessChamp viewport is too small for board and commentary")
        self.label_height = 36
        self.board_x = margin + (
            max(0, w * 0.62 - 2 * margin - self.board_size) / 2 if landscape else (w - 2 * margin - self.board_size) / 2
        )
        self.board_y = 70
        if landscape:
            x = w * 0.64
            self.panel_box = (x, 28, w - x - 28, h - 56)
        else:
            y = self.board_y + self.board_size + 78
            self.panel_box = (28, y, w - 56, h - y - 28)
        if self.panel_box[2] < 150 or self.panel_box[3] < 160:
            raise ValueError("ChessChamp viewport is too small for commentary")

        grid = self.assets.board_grid
        ratio = self.board_size / self.assets.board_width
        left, top = grid[:2]
        if self.script.orientation == "black":
            left, top = self.assets.board_width - grid[2], self.assets.board_width - grid[3]
        self._grid_x = self.board_x + left * ratio
        self._grid_y = self.board_y + top * ratio
        self._grid_size = (grid[2] - grid[0]) * ratio

    @staticmethod
    def _fit(text, width, height, maximum):
        for size in range(maximum, 17, -2):
            font = _font(size)
            lines = []
            for paragraph in text.split("\n"):
                line = ""
                for word in paragraph.split():
                    candidate = f"{line} {word}".strip()
                    if line and font.getlength(candidate) > width:
                        lines.append(line)
                        line = word
                    else:
                        line = candidate
                lines.append(line)
            if max(font.getlength(line) for line in lines) <= width and len(lines) * size * 1.4 <= height:
                return "\n".join(lines), size
        raise ValueError("ChessChamp text cannot fit; shorten it or enlarge the viewport")

    def square_center(self, square):
        if isinstance(square, str):
            square = _square(square, "square")
        if type(square) is not int or not 0 <= square < 64:
            raise ValueError("square must be a square name or integer from 0 through 63")
        file, rank = square % 8, square // 8
        col, row = (file, 7 - rank) if self.script.orientation == "white" else (7 - file, rank)
        cell = self._grid_size / 8
        return self._grid_x + (col + 0.5) * cell, self._grid_y + (row + 0.5) * cell

    def frame_key(self, age):
        return min(self.duration, self.source_start + max(0, age))

    def frame_image(self, age, factor=1):
        factor = finite(factor, "factor", 0.001)
        time = self.frame_key(age)
        theme, cell = self.theme, self._grid_size / 8
        image = Image.new(
            "RGBA", (max(1, round(self.width * factor)), max(1, round(self.height * factor))), theme.background
        )
        draw = ImageDraw.Draw(image)

        def rect(box, fill):
            draw.rectangle(tuple(round(v * factor) for v in box), fill=fill)

        def text(x, y, value, size=24, fill=None, anchor="la"):
            draw.multiline_text(
                (round(x * factor), round(y * factor)),
                value,
                font=_font(max(1, round(size * factor))),
                fill=fill or theme.foreground,
                anchor=anchor,
                spacing=round(size * 0.4 * factor),
            )

        board_image = self.assets._board_image(max(1, round(self.board_size * factor)), self.script.orientation)
        image.alpha_composite(board_image, (round(self.board_x * factor), round(self.board_y * factor)))
        state = self.script.position_at(time)
        annotations = self.script.annotations_at(time)
        overlay = Image.new("RGBA", image.size)
        ink = ImageDraw.Draw(overlay)
        highlights = [(s, a.color or theme.accent) for a in annotations if a.type == "highlight" for s in a.squares]
        if state.check_square is not None:
            highlights.append((state.check_square, theme.check))
        for square, color in highlights:
            x, y = self.square_center(square)
            ink.rectangle(
                tuple(round(v * factor) for v in (x - cell / 2, y - cell / 2, x + cell / 2, y + cell / 2)),
                fill=ImageColor.getcolor(color, "RGBA")[:3] + (115,),
            )
        image.alpha_composite(overlay)
        draw = ImageDraw.Draw(image)
        active = self.script.active_move(time)
        moving_origins = {m[0] for m in active.moving} if active else set()

        def piece(symbol, x, y):
            sprite = self.assets._piece_image(symbol, cell * factor)
            image.alpha_composite(sprite, (round(x * factor - sprite.width / 2), round(y * factor - sprite.height / 2)))

        for square, symbol in state.pieces:
            if square not in moving_origins:
                piece(symbol, *self.square_center(square))
        if active:
            progress = (time - active.at) / active.duration
            progress = progress * progress * (3 - 2 * progress)
            for origin, destination, symbol in active.moving:
                x, y = self.square_center(origin)
                dx, dy = self.square_center(destination)
                piece(symbol, x + (dx - x) * progress, y + (dy - y) * progress)
        for a in annotations:
            if a.type == "arrow":
                start, end = (self.square_center(s) for s in a.squares)
                vx, vy = end[0] - start[0], end[1] - start[1]
                length = math.hypot(vx, vy)
                ux, uy = vx / length, vy / length
                tip = cell * 0.28
                base = (end[0] - ux * tip, end[1] - uy * tip)
                color = a.color or theme.accent
                draw.line(
                    tuple((round(x * factor), round(y * factor)) for x, y in (start, base)),
                    fill=color,
                    width=max(1, round(cell * 0.1 * factor)),
                )
                draw.polygon(
                    [
                        (round(x * factor), round(y * factor))
                        for x, y in (
                            end,
                            (base[0] - uy * tip * 0.55, base[1] + ux * tip * 0.55),
                            (base[0] + uy * tip * 0.55, base[1] - ux * tip * 0.55),
                        )
                    ],
                    fill=color,
                )
        # Coordinates remain attached to board orientation.
        for col in range(8):
            file = col if self.script.orientation == "white" else 7 - col
            rank = 7 - col if self.script.orientation == "white" else col
            text(
                self._grid_x + (col + 0.5) * cell,
                self.board_y + self.board_size + 6,
                chr(97 + file),
                18,
                theme.muted,
                "ma",
            )
            text(self.board_x - 8, self._grid_y + (col + 0.5) * cell, str(rank + 1), 18, theme.muted, "rm")
        bottom_index = 0 if self.script.orientation == "white" else 1
        for index, y in ((1 - bottom_index, 18), (bottom_index, self.board_y + self.board_size + 34)):
            value, size = self._labels[self.script.players[index]]
            text(self.board_x, y, value, size)
        px, py, pw, ph = self.panel_box
        rect((px, py, px + pw, py + ph), theme.panel)
        concluded = self.script.result != "*" and time >= (self.script.moves[-1].end if self.script.moves else 0)
        header, size = self._headers[
            "over" if concluded or state.status in ("Checkmate", "Stalemate", "Draw") else state.turn
        ]
        text(px + 20, py + 20, header, size, theme.muted)
        status = " · ".join(filter(None, (state.san, state.status))) or "Starting position"
        value, size = self._result_label if concluded else self._statuses[status]
        text(px + 20, py + 65, value, size, theme.accent)
        if not concluded and not any(a.type == "text" for a in annotations):
            completed = bisect_right(self.script._ends, time)
            if completed:
                value, size = self._histories[completed]
                text(px + 20, py + 120, value, size, theme.muted)
        for a in annotations:
            if a.type == "text":
                value, size = self._comments[a.text]
                text(px + 20, py + 120, value, size, a.color)
        return image
