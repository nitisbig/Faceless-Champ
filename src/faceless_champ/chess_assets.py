"""Offline chess artwork with measured board squares and bounded resized sprites."""

import hashlib
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageOps

PIECE_FILES = {
    symbol: f"{side}-{name}.png"
    for side, symbols in (("white", "KQRBNP"), ("black", "kqrbnp"))
    for symbol, name in zip(symbols, ("king", "queen", "rook", "bishop", "knight", "pawn"))
}


class ChessAssets:
    """Load an entire board/piece set once. Public image access is unnecessary.

    ``board_grid`` is the square playing area in source-image pixels as
    (left, top, right, bottom). Omit it for an unframed board image.
    Source pixels are captured at construction and shared by scene snapshots.
    """

    def __init__(self, directory, *, board_grid=None):
        self.directory = Path(directory).resolve()
        paths = {"board": self.directory / "chessboard.png"}
        paths.update({symbol: self.directory / name for symbol, name in PIECE_FILES.items()})
        images, checksums = {}, {}
        for symbol, path in paths.items():
            try:
                raw = path.read_bytes()
                with Image.open(path) as source:
                    image = ImageOps.exif_transpose(source).convert("RGBA").copy()
            except (OSError, ValueError) as exc:
                raise ValueError(f"Cannot load chess asset {path}: {exc}") from exc
            checksums[path.name] = hashlib.sha256(raw).hexdigest()
            if symbol != "board":
                # Some downloaded cutouts have near-transparent noise at their edges.
                box = image.getchannel("A").point(lambda alpha: 255 if alpha > 8 else 0).getbbox()
                if box is None:
                    raise ValueError(f"Chess piece is entirely transparent: {path}")
                image = image.crop(box)
            images[symbol] = image
        board = images["board"]
        if board.width != board.height:
            raise ValueError("Chess board image must be square")
        grid = tuple(board_grid) if board_grid is not None else (0, 0, board.width, board.height)
        if len(grid) != 4 or any(type(v) not in (int, float) for v in grid):
            raise ValueError("board_grid requires four numeric source-image coordinates")
        left, top, right, bottom = grid
        if not (0 <= left < right <= board.width and 0 <= top < bottom <= board.height):
            raise ValueError("board_grid must lie inside the board image")
        if abs((right - left) - (bottom - top)) > 1e-6:
            raise ValueError("board_grid must be square")
        self.board_grid = grid
        self.board_width = board.width
        images["board-black"] = board.transpose(Image.Transpose.ROTATE_180)
        self._images, self._checksums = images, checksums
        self._cache = OrderedDict()
        self._cache_bytes = 0
        self._cache_limit = 32 * 1024 * 1024

    def __deepcopy__(self, memo):
        # Artwork is private and never mutated; resized caches do not affect frames.
        return self

    @classmethod
    def bundled(cls):
        return _bundled()

    @property
    def checksums(self):
        return dict(self._checksums)

    def _resized(self, symbol, width, height):
        key = (symbol, width, height)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        image = self._images[symbol].resize((width, height), Image.Resampling.LANCZOS)
        count = width * height * 4
        if count <= self._cache_limit:
            while self._cache and self._cache_bytes + count > self._cache_limit:
                _, old = self._cache.popitem(last=False)
                self._cache_bytes -= old.width * old.height * 4
            self._cache[key] = image
            self._cache_bytes += count
        return image

    def _board_image(self, size, orientation):
        return self._resized("board-black" if orientation == "black" else "board", size, size)

    def _piece_image(self, symbol, cell):
        image = self._images[symbol]
        heights = {"k": 0.90, "q": 0.90, "b": 0.84, "n": 0.83, "r": 0.76, "p": 0.67}
        ratio = min(cell * 0.84 / image.width, cell * heights[symbol.lower()] / image.height)
        return self._resized(symbol, max(1, round(image.width * ratio)), max(1, round(image.height * ratio)))


@lru_cache(maxsize=1)
def _bundled():
    return ChessAssets(Path(__file__).parent / "assets/chess", board_grid=(87, 87, 1167, 1167))
