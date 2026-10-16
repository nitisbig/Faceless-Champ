# ChessChamp tutorials and analysis

Install `facelesschamp-kit[chess]` (or install the freshly built core and kit wheels with
the chess extra). Chess rendering requires the optional GPL-3.0-or-later `chess` rules
package. The downloaded chessboard and twelve piece PNGs are bundled in the core;
the renderer needs no online services.

```bash
fc-kit init my-chess --template chesschamp
cd my-chess
fc-kit validate main --json
fc-kit frame main --time 3.6 -o output/board.png
fc-kit storyboard main -o output/storyboard
fc-kit preview main -o output/preview.mp4
fc-kit render main -o output/main.mp4
```

Edit the required **root `data.json`**. The starter shows White's e4, Black's d5, and
White's capture, with commentary, an arrow, and square highlights. The ten-second
example is a complete short demonstration. Longer projects are only fully verified
after a complete export is decoded and visually inspected.

See the [core data contract](../../docs/chesschamp.md#required-datajson) for all input
fields, special moves, validation, and timing rules. Player names, orientation,
starting FEN, moves, and annotations all belong in JSON. The default format is
landscape; switching the project to `shorts` lays out commentary below the square board.

## Reusable APIs

```python
from facelesschamp_kit.templates import chesschamp


def build(ctx):
    return chesschamp(ctx, data="data.json")
```

The template returns an editable `Video`. Paths resolve from the project root, not
the invoking directory. Missing JSON and invalid fields produce `CHESS_DATA` diagnostics
with `field` and, for moves, zero-based `move_index`. Missing chess rules produce
`CHESS_DEPENDENCY`. Project reports fingerprint JSON and audio inputs.

`ChessBoard(script, theme=None, source_start=0, assets=None)` is available from
`facelesschamp_kit.blocks`. It composes a fresh core `ChessChamp` fitting its allocated
bounds and exposes the named child `board`. Use it inside any segment, including delayed
placements; remaining script duration must fit the authored placement. A narration tail
cannot hide overflowing moves. Component transforms and entry animations work normally.

## Optional existing audio

Register an audio asset in `assets/manifest.json`:

```json
{"voiceover": {"type": "audio", "path": "assets/audio/voiceover.wav"}}
```

Then add this root field to `data.json`:

```json
"narration": {"audio": "voiceover"}
```

The template attaches that track exactly once at master zero. JSON move and annotation
times stay unchanged. Longer audio extends the final position hold; shorter audio leaves
the remainder silent. Source-clock range exports retain the correct board and audio offset.
No speech is generated. Keep `captions = false` for audio-only narration.

For Python authors, `video.narration(audio=path)` now supports audio without an SRT.
The existing `subtitles=...`, `markers=...`, and caption workflow remains available.
Cue windows, `segment.cue_time`, and captions require subtitles and fail explicitly
without them. Commentary text in JSON is independent of subtitle captions.

## Supplied artwork and SAN notation

The core now renders the framed board and twelve downloaded PNG pieces by default.
Use `ChessAssets(directory, board_grid=...)` in `ChessBoard(..., assets=...)`, or put
`assets.directory` and `assets.board_grid` in data.json for another local set. Paths
in JSON resolve from the JSON file's directory. Reports fingerprint the artwork.
