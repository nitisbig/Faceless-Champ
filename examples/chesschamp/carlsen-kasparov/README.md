# Supplied chess UI example

The supplied Carlsen–Kasparov notation is stored unchanged in game.pgn. data.json
contains all 103 legal plies, player labels, the declared draw, and explicit timing.
It uses the supplied board and piece PNGs bundled in the core. No audio is attached.

From the repository root with the core and kit installed:

```bash
python examples/chesschamp/carlsen-kasparov/import_game.py
fc-kit --project examples/chesschamp/carlsen-kasparov validate main
fc-kit --project examples/chesschamp/carlsen-kasparov preview main --start 0 --end 74.85 -o output/chesschamp/carlsen-kasparov-silent.mp4
```

The complete UI replay is 74.85 seconds at the authored timing. The preview profile
is 1280×720 at 24 fps; the final profile is 1920×1080 at 30 fps. Use `render main` for
the final profile. Add `--overwrite` when deliberately replacing an existing output.

Edit import_game.py to change the default 0.45-second piece motion and 0.7-second
move interval, then regenerate data.json. Rendering consumes data.json directly.
The player attribution follows the supplied example; historical provenance was not checked.
