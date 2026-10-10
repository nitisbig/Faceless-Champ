# Programming Value — v2

The default version is the black-background cinematic redesign: 43 cue-selected shots, six recurring visual motifs in the opening 24 seconds, sharp Inter typography, STIX operators, constructed diagrams, and one unchanged master narration track. There are no title or subtitle overlays. The new outline and research references are in [scene/outline-v2.md](scene/outline-v2.md).

```bash
python3 render.py --preview                         # 0–12 s, 960×540 / 30 fps
python3 render.py --full                            # 1920×1080 / 30 fps, 2× AA
python3 render.py --range 246.64 264.88 --resolution 1080p
python3 render.py --scene systems
python3 render.py --frame 489 --resolution 1080p
python3 render.py --storyboard                      # two samples per shot
python3 render.py --check                           # source protection / timing / cadence
python3 render.py --audit-layout                    # all 14,795 frame times
python3 verify_v2.py --clips                        # full decode, audio QA, frames, six clips
python3 render.py --version v1 --preview            # original scene remains available
```

V2 media and reports have separate names. The full file is **output/programming-value-v2-full.mp4**. Add `--overwrite` explicitly when replacing an existing output. The legacy image-mode argument remains compatible; v2 constructs its artwork and does not depend on images or display placeholders.

Palette: AI/code sky blue, systems/usefulness green, judgment amber, rejected choices pink; white and slate labels on pure black. Fonts and their licenses are bundled in assets/fonts/. Numerical scale examples are hypothetical. The three-second cadence directs attention to the explanation; retention uplift has not been measured.

V2 uses the existing Faceless Champ primitives, animation tracks, cue clock, audio mixer and exporter. Its project renderer caches small 2×-supersampled layers and downsamples them with Lanczos, avoiding repeated resizing of an otherwise empty 4K canvas. It retains the standard renderer for unsupported masks or nonuniform transforms. Preview/full frame schedules stay on the original source clock.

Full v2 exports save verified, frame-aligned ten-second video chunks. Rerunning `--full` reuses completed chunks only when source files, fonts, scene/library code and export settings match. The final mux joins the silent chunks and attaches the original audio once, avoiding audio cuts or accumulated timing offsets. Checkpoint progress is in output/v2-chunks/*/checkpoint.json.

See [VERIFICATION-v2.md](VERIFICATION-v2.md) for the completed export's actual validation status.

## Original version

Six chapters synchronized to the unchanged audio.mp3 and 1,379 original word cues. The outline is in [scene/outline.md](scene/outline.md), executable cue-selected composition in scene/story.py, and artwork prompts in [img-info.md](img-info.md).

From this directory:

```bash
python3 render.py --image placeholder
python3 render.py --storyboard --image placeholder
python3 render.py --list-scenes
python3 render.py --scene systems --image placeholder
python3 render.py --range 250.4 265 --image placeholder
python3 render.py --frame 264.5 --image placeholder
```

For `--version v1`, the default renders only 0–12 seconds at 960×540 / 15 fps. `--scene` previews one entire selected chapter. `--range` uses original source-audio seconds. Add `--overwrite` to replace the chosen output, or `--output PATH` to choose another destination. Frames use PNG paths; storyboard output is a directory. `--fps` and `--resolution 540p|720p|1080p|4k|WIDTHxHEIGHT` customize exports while preserving the design aspect ratio.

The script uses the repository .venv when available and imports both libraries from their source directories in the main checkout. It works from any calling directory. Dependencies belong to the main packages; no rendering code is copied here.

Place `1.png`–`4.png` in **images/**. Default `--image auto` loads existing files and labels missing slots. `placeholder` always forces boxes; `required` fails for missing artwork. Existing corrupt files fail in auto/required modes. Continuous transcript captions are off; short explanatory labels remain on screen.

`python3 render.py --version v1 --full` renders the original composition at 1920×1080 / 30 fps. The existing v1 full file was probed at 1280×720 / 15 fps; v1 1080p and 4K exports were not validated in this redesign.

Reusable changes live in faceless_champ and facelesschamp_kit: shared measured text fitting, delayed/finite placement lifetimes, original-cue timing within segments, responsive text cards, workflow blocks and real labeled image reservations. The charts and scaling examples are conceptual/hypothetical, not economic measurements.

Generated media and timeline.json are saved under output/. The report records exact chapter/placement windows, all original cue timestamps, narration checksums, selected render range and image mode.
