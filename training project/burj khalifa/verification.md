# Burj Khalifa — verification evidence

Verified locally on 2026-10-14. The complete **182.200-second timeline is
authored**. The complete/full-HD film is **intentionally unrendered**;
`full_export_verified: false` remains the status.

## Source clock and model

- All 436 original word cues retain their indices and times. The intentional
  1 ms overlap between cues 231/232 is accepted without editing either SRT.
- Narration is attached once at master zero. The derived mono 48 kHz PCM WAV has
  8,745,600 samples = 182.200 seconds. Original source hashes are recorded in
  [verification.json](verification.json).
- The last cue ends at 181.880. No authored motion extends into the final
  0.320-second hold. HD frames at 181.880 and 182.190 were pixel-identical.
- Tests inspect actual geometry: 828 m spire endpoint, 3.7 m raft thickness,
  192 separate closed pile cylinders, finite coordinates and a manifold soil
  surface for the capped section. Member sizes and pile/setback arrangements
  remain schematic; this is not surveyed CAD or a physical simulation.

## Automated validation

| Check | Result |
|---|---|
| Complete core suite | 551 passed, 2 skipped |
| Complete kit suite, separate process | 211 passed |
| Project content/timing tests | 3 passed |
| Newly built core wheel, outside source imports | 29 ArchChamp tests passed |
| Project build against that installed wheel | Passed; core import resolved under `/tmp/burj-wheel-test` |
| Source-time viewport/camera sampling | 2,208 states; zero findings |
| Annotation sampling | 2,430 observations; zero overflow/overlap findings |
| Whole-timeline safe-margin sampling | Zero findings at 0.1-second intervals |
| Ruff and Git whitespace checks | Passed |

Easing tests cover quarter-time interpolation, endpoints, JSON round trips,
legacy linear defaults, camera and section interpolation, immediate visibility,
invalid easing and out-of-order evaluation. Project tests verify source cues,
contiguous chapters, one master narration, actual pile population and final hold.

Runtime: core 0.1.5, kit 0.1.0rc7, PyVista 0.49.1, VTK 9.7.1, NumPy 2.5.3.
The core wheel was built offline from this checkout. Existing third-party
runtimes were reused for isolated package validation.

## Encoded excerpt evidence

Seven three-second MP4s were checked: **21 seconds, 315 H.264 frames total**.
Each is 960×540 at 15 FPS with 2× supersampling and narration. FFprobe frame
counts/dimensions/rates and complete FFmpeg decoding pass for every file.

| Chapter | Source interval | Audio correlation | Best lag |
|---|---|---|---|
| Introduction | 3–6 s | 0.999463 | 0 samples |
| Geometry | 20–23 s | 0.999669 | 0 samples |
| Structure | 47–50 s | 0.999736 | 0 samples |
| Aerodynamics | 94–97 s | 0.999419 | 0 samples |
| Foundation | 114–117 s | 0.999714 | 0 samples |
| Construction | 142–145 s | 0.999848 | 0 samples |
| Final reveal | 177–180 s | 0.999744 | 0 samples |

Audio correlation compares each decoded excerpt with its original MP3 interval.
Lag checks compare every integer sample offset within ±10 ms. This establishes
alignment for these excerpts, not a completed full-film audio verification.

## Visual inspection

- Inspected the [25-frame final storyboard](output/storyboard-final/storyboard.png),
  including flower inspiration, inward daylight/outward views, structural
  separation/reassembly, load directions, torsion, vortices, capped soil,
  raft/piles, pumping, façade, coated glass, steel spire and the final reveal.
- Inspected a frame extracted from every encoded excerpt. File paths and raw
  measurements are in the machine-readable verification record.
- Inspected [the structural HD still](output/structure-hd.png) and
  [the final HD still](output/final-hd.png). Structural callouts anchor to modeled
  walls/columns and have separate leaders. Labels stay concise and legible,
  without transcript overlays or chapter headings.
- Full-tower shots use restrained narrow silhouettes and roughly 70% frame
  height. Closeups provide detail. Wind, force, heat and foundation arrangements
  are identified as schematic. No measured simulation values are invented.

The storyboard/stills and excerpt decode/audio checks support this training
example's selected samples. They do not establish a completed full-HD/4K export
or frame-by-frame editorial review of the entire film.

Run commands, feature coverage and portability notes are in [README.md](README.md).
