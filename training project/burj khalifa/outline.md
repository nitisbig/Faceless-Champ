# Burj Khalifa — cue-derived scene outline

Thesis: geometry joins architecture, structural engineering and aerodynamics into
one working system. This is an engineering explainer and a public-API training
example, with original procedural teaching geometry rather than a surveyed model.

The 436 original word cues are authoritative. Preserve the 1 ms overlap between
cues 231/232. Decode audio without time stretching: 8,745,600 mono samples at
48 kHz = 182.200 seconds. Last cue ends at 181.880; the last 0.320 seconds hold.
No headings or subtitles appear in the film. Component labels, dimensions and
small schematic notes are allowed. Use navy #0B1020, cyan geometry, amber active
components, orange forces, white labels, 96 px margins on a 1920×1080 canvas.

| Chapter | Source window | Cue boundary | Proof and acceptance |
|---|---|---|---|
| introduction | 0–13.960 | start–34 | Recognizable stepped tower, true 828 m dimension, wind/torsion schematic; settled camera at the geometry thesis. |
| geometry | 13.960–32.820 | 34–79 | Top-down Y plan, three distinct wings and hexagonal core; flower inset, daylight and view directions. |
| structure | 32.820–70.080 | 79–170 | Façade fades, real modeled walls/columns remain; wings explode and reconnect; lateral forces and torsion explained separately. |
| aerodynamics | 70.080–106.800 | 170–267 | Constant-section comparator with aligned vortices; three-wing setbacks and incoherent vortices at several elevations. |
| foundation | 106.800–128.840 | 267–314 | Camera travels below grade, capped soil cutaway, load path into 3.7 m raft and 192 schematic piles. |
| construction | 128.840–166.920 | 314–400 | Concrete pipe/packet travels above 600 m; representative façade assembly, coated glass/solar arrows, steel spire. |
| final | 166.920–182.200 | 400–end | Structural systems reconnect; aligned wireframe/solid crossfade and restrained orbit; all motion stops by 181.880. |

Schedule every explanation through cue indices, not paragraph duration estimates.
Use smaller shot placements for changing world-anchored annotations. Camera moves
use smooth easing and hold during dense explanations. Full-tower shots occupy
roughly 70% of frame height; foundation and floor-plan shots use separate framing.

## Geometry and engineering boundaries

- Z is vertical, coordinates are metres, height above grade is exactly 828 m.
- Model the core, three wings, walls, perimeter columns, stepped shell, façade,
  spire, raft, piles and soil separately. Batch repeated geometry into meshes.
- Raft thickness is 3.7 m; 192 piles are individually generated then batched.
  Their arrangement, setbacks and structural member dimensions are schematic.
- Glass modules stand for nearly 26,000 panels, not 26,000 modeled objects.
- Wind, force, heat and pump motion are explanatory graphics, not solver output.

## Sources

- Owner architecture: https://www.burjkhalifa.ae/the-tower/architecture-design/
- Owner structure/foundation/cladding: https://www.burjkhalifa.ae/the-tower/structures/
- Foundation testing contractor's paper, section 1 (192 piles):
  https://avestia.com/CSEE2023_Proceedings/files/paper/ICGRE/ICGRE_106.pdf
- Structural engineer's account (828 m, buttressed core):
  https://www.iccsafe.org/building-safety-journal/bsj-technical/a-tall-adventure-the-burj-khalifa-the-worlds-tallest-structure/
- Pump manufacturer (606 m achieved; film retains narration's “over 600 m”):
  https://www.putzmeister.com/web/middle-east/success-story-detail/-/asset_publisher/burj-khalifa-dubai-united-arab-emirates

## Verification boundary

Inspect a chapter-spanning storyboard and seven short encoded excerpts, decode
each fully, check audio against its source interval and sample layout throughout.
The full timeline is authored, but the complete/full-HD film is intentionally
unrendered. Report `full_export_verified: false` until that actual export is tested.
