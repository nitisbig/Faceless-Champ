# Programming Value — scene outline

Visual thesis: As AI makes code cheaper to produce, programming's value shifts toward understanding systems, choosing useful problems, and judging solutions.

## Design

1920×1080 landscape; 72 px safe margins; white background. Terracotta #C15F3C accents, #F4F3EE cards, #B1ADA1 supporting marks, #292724 text. Bundled DejaVu Sans; 88 px headlines, 44 px labels, 32 px secondary copy. No persistent title or transcript captions. Alternate full-frame diagrams, two-column comparisons, 2×2 and 2×3 grids. Motion responds to meaningful phrases, not every filler word. Each chapter proves one claim with several shots.

## Six chapters

| ID | Original source time | Original cue range | Proof and shots |
|---|---|---|---|
| code-value | 0–107.560 | 1–305 | Cheaper code makes deciding what to build more valuable. Code race; prediction cards; syntax toolkit; conceptual cost/value relationship; useful versus useless applications. |
| systems | 107.560–174.400 | 306–476 | Programming reveals connections inside separate tasks. Inputs/outputs; business tasks; connected five-step workflow; information token; duplicate entry removed; improved workflow. |
| optimization | 174.400–229.760 | 477–619 | Working solutions must handle scale and resource constraints. Prototype; data ×1,000; 10→10 million users; $1→$1,000 cost; resource trade-offs; simplify/delegate/automate/eliminate. |
| better-questions | 229.760–330.880 | 620–902 | Structural understanding improves outcomes from the same AI. Two users; generic app; seven requirements questions; evaluation; technical knowledge still matters; four professional applications. |
| human-judgment | 330.880–401.840 | 903–1101 | Human context determines which solutions deserve to exist. AI capabilities; solving versus choosing; lived context; responsibilities; impressive but wrong solution; human intentions into systems. |
| useful-systems | 401.840–audio end | 1102–1379 | Programming remains useful when it develops understanding and judgment. Changing task value; code quantity versus usefulness; decomposition; systems/patterns/design/optimization; complexity resolves into a working system. |

## Timing and assets

cue-per-word.srt is authoritative: 1,379 cues, six 1 ms overlaps, last cue ends 492.880 s. Preserve source timestamps and indices, opt into overlap_tolerance=0.001, attach audio once at master zero. The current audio is 493.152 s; probe its duration rather than hard-coding the end. First visuals cover the 80 ms lead-in; hold the closing system through the audio tail.

The executable beat sheet is scene/story.py: every shot has explicit original start/end cue indices; motions use Segment.cue_time. This outline is written before scene implementation. Four image reservations are documented in ../img-info.md. Charts are conceptual or hypothetical examples from the narration, not measured economic data.

## Preview order

First render only 0–12 s at 960×540/15 fps. Inspect typography, geometry and encoded frames; then complete the remaining chapters. Inspect a 24-frame storyboard and selected short clips around 139.210, 189.130, 250.400, 391.040 and 480 s. Never render the full narration during development.
