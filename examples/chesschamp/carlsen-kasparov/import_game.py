"""Convert supplied SAN/PGN notation to editable, authoritative data.json."""

import json
from pathlib import Path

from faceless_champ import ChessScript

root = Path(__file__).resolve().parent
script = ChessScript.from_pgn((root / "game.pgn").read_text(), move_duration=0.45, move_interval=0.7)
data = script.to_dict()
(root / "data.json").write_text(json.dumps(data, indent=2) + "\n")
print(f"Saved {len(script.moves)} legal plies, {script.duration:.2f} seconds, result {script.result}")
