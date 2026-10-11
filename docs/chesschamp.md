# ChessChamp

ChessChamp renders standard chess tutorials and authored game analysis from timed JSON.
It validates legal moves and renders both sides; it does not provide interactive play,
engine evaluation or speech generation. SAN/PGN mainlines can be imported into timed JSON.

Install `pip install 'faceless-champ[chess]'`. The optional `chess` rules package is
[GPL-3.0-or-later](https://python-chess.readthedocs.io/en/latest/#license); review its
license when distributing software that uses it. Importing the core library does not
require this extra. Rendering uses the supplied PNG chessboard and twelve piece cutouts bundled with the core,
plus DejaVu Sans for labels. No network or browser is needed.

## Python API

```python
from faceless_champ import Canvas, ChessChamp, ChessScript, ChessTheme, Scene, render

script = ChessScript.from_json("data.json")
scene = Scene(Canvas(1600, 900, "#171E1A"))
board = ChessChamp(script, width=1600, height=900, position=(800, 450))
scene.add(board)
scene.wait(script.duration)
render(scene, "output/chess.mp4", fps=30)
```

`ChessScript.from_dict(data)` accepts the same document as `from_json(path)`.
The script compiles immutable positions, moves, and annotations once. `position_at(seconds)`
returns an immutable position with `pieces` (square-index/symbol pairs), `fen`, `turn`,
`check_square`, `status`, and the last completed move's `san`. Square indices run from
a1=0 to h8=63. `active_move(seconds)` and `annotations_at(seconds)` expose the timeline.
Invalid data raises `faceless_champ.chess.ChessDataError`, a `ValueError` carrying `path`
and a zero-based `move_index` for move errors. Missing optional rules raise `ImportError`.

`ChessChamp(script, *, width=1600, height=900, source_start=0, theme=None, assets=None, **component_options)`
is a normal Component: position, anchor, scale, rotation, opacity, groups, masks, and
measured bounds work as usual. Configure it before adding it to a scene. `source_start`
selects an offset into the original script; local scene age advances from that offset.
Playback holds its final position past the script end. Rendered frames are independent
of evaluation order. `square_center("e4")` returns viewport-local design coordinates.

`ChessTheme()` styles the surrounding panels, labels, annotations, and check highlights.
Board and piece colors come from the artwork.
Use `dataclasses.replace(ChessTheme(), accent="#FFCC44")` to customize `light`, `dark`,
`background`, `panel`, `foreground`, `muted`, `accent`, `check`, `white_piece`, or `black_piece`.
The viewport lays out commentary beside a landscape board and below a portrait board.
Without commentary it shows the recent move history, and declared results appear at the final move.
Squares never stretch. Text wraps and shrinks to an 18-pixel design minimum during
construction; oversized labels or commentary fail before export.

## Required data.json

See the complete [runnable example](../examples/chesschamp/data.json). A minimal document:

```json
{
  "schema_version": 1,
  "duration": 8,
  "players": {"white": "White", "black": "Black"},
  "orientation": "white",
  "moves": [
    {"at": 1, "duration": 0.5, "uci": "e2e4"},
    {"at": 4, "duration": 0.5, "uci": "e7e5"}
  ],
  "annotations": [
    {"type": "text", "at": 1.5, "duration": 2, "text": "White takes space in the center."},
    {"type": "arrow", "at": 1.5, "duration": 2, "from": "e2", "to": "e4"},
    {"type": "highlight", "at": 4.5, "duration": 2, "squares": ["e4", "e5"], "color": "#FFCC44"}
  ]
}
```

- Required: integer `schema_version: 1`, positive finite `duration`, and a `moves` array.
  An empty move list is a static lesson. Unknown fields fail explicitly.
- Optional: `players.white` and `players.black` (default White/Black), `orientation`
  (`white` or `black`, default white), and `initial_fen` (default standard start).
  Custom positions must be valid standard chess positions; FEN validity is not proof
  that a position is reachable through a historical game.
- Moves require numeric `at`, positive `duration`, and legal UCI `uci`. Use `e1g1` for
  kingside castling and `a7a8q` for promotion; q/r/b/n promotions are supported.
  Moves must be in time order, cannot overlap, and must end within the script.
  Turns, checks, castling rights, en passant, and king safety are enforced.
- Captures disappear and promotions change piece type at arrival. Castling moves king
  and rook together. Turns, SAN notation, and check status update at arrival. A moving
  piece passes directly between square centers, including a knight's visual motion.
- All times are absolute seconds from script zero. Gaps hold the position. Annotation
  intervals include their start and exclude their end; there is no automatic retiming.
- Annotations require `type`, `at`, positive `duration`, and kind-specific fields:
  `text` for commentary, `from`/`to` for arrows, `squares` for highlights. Optional `color`
  accepts Pillow color strings. Text intervals cannot overlap; visual annotations can.
- Automatic terminal states include mate, stalemate, insufficient material, fivefold
  repetition, and the 75-move rule. Claimable draws do not automatically end the script.
  Moves after an automatic terminal state are rejected. FEN alone has no prior repetition history.
- Optional `narration: {"audio": "voiceover"}` is a **kit asset ID**. Core ChessChamp is
  visual only; core callers attach audio once with `scene.add_audio(path, start=0)`.

Run `python examples/chesschamp/showcase.py -o output/chesschamp.mp4` for the sample.
For a complete project scaffold and optional narration, see the
[kit guide](../facelesschamp-kit/docs/chesschamp.md).

## Image artwork

`ChessAssets.bundled()` loads the supplied `chessboard.png` and all twelve files
`white-{king,queen,rook,bishop,knight,pawn}.png` and their `black-` equivalents. The
original PNGs are preserved. Rendering trims near-transparent padding, preserves
piece proportions, and uses smaller pawns than kings and queens.

For a custom set, use `ChessAssets(directory, board_grid=(left, top, right, bottom))`
and pass `assets=artwork` to ChessChamp or the kit ChessBoard block. The grid is the
square playing area inside the frame, in source-image pixels. It must be square and
inside the square board image. Omit the grid for an unframed board. Missing or invalid
images fail before export. Scene snapshots share captured image pixels; a bounded
32 MiB cache holds resized sprites.

Alternatively put the artwork configuration in data.json:

```json
"assets": {"directory": "assets/chess", "board_grid": [87, 87, 1167, 1167]}
```

Directory paths resolve relative to data.json. `from_dict(..., base_path=...)` sets
that base explicitly. The default bundled grid matches the supplied 1254-pixel board.
Rotating to Black's perspective also rotates the board image and its measured grid;
piece images stay upright. Kit reports include image checksums in their fingerprint.

## Import encoded moves

```python
import json
from pathlib import Path
from faceless_champ import ChessScript

script = ChessScript.from_pgn(
    Path("game.pgn").read_text(),
    move_duration=0.45, move_interval=0.7, lead_in=1, tail=2,
)
Path("data.json").write_text(json.dumps(script.to_dict(), indent=2))
```

The importer accepts numbered SAN movetext such as `1. d4 d5 2. c4 c6`, including
PGN headers, disambiguation, captures, castling, checks, and promotion. It imports one
mainline and rejects illegal moves. Headers provide player names and starting FEN;
`players={"white": ..., "black": ...}` can override names. Timing parameters are
seconds: interval is measured between move starts and must be at least move duration.
The returned immutable script can also be used directly.

The generated data.json remains the rendering authority. Optional `result` accepts
`*`, `1-0`, `0-1`, or `1/2-1/2`; the result displays after the final move, including an
agreed draw in a position that could otherwise continue.

The [supplied Carlsen–Kasparov example](../examples/chesschamp/carlsen-kasparov/data.json)
contains all 103 legal plies, lasts 74.85 seconds, and is silent. Its player names and
notation reproduce the user's supplied example. See its README for the importer and
kit rendering commands.
