# Programming Value v2 — outline written before animation code

Visual thesis: As AI makes code easier to produce, programming becomes more valuable for understanding systems, choosing worthwhile problems, and judging solutions.

## Design and timing contract

Faceless Champ / Faceless Champ Kit; 1920×1080, 30 fps. Pure black background, 96 px safe margins. Cinematic depth comes from layered geometry, restrained halos, moving information tokens, and gentle group zooms. No titles or subtitles. Short object labels and integrated expressions only. Inter for ideas, DejaVu Sans Mono for code, STIX for mathematical notation. Sizes: ideas 76, labels 40, code 34, minimum 32 design pixels.

White #F4F7FB; supporting labels #AAB4C3; AI/code #56B4E9; systems/usefulness #009E73; human judgment #E69F00; failure/rejected choices #CC79A7. Meaning also uses shape, position and symbols. Dark surfaces #10151D; text is never blurred. All graphics are constructed: no image placeholders. Numerical scaling examples are hypothetical; economic arrows are conceptual, not market data.

Preserve audio.mp3 (SHA256 396814cccc3fcf3d84942980e140659a4cbb0fdb63c50835893f04b34bef3256) and cue-per-word.srt (SHA256 1edb26d6ec2d8a3aa3560829630eabb99fcd3c6dcb62308bc3aab8f70444b254). Read all 1,379 cues; preserve six 1 ms overlaps, 80 ms lead-in and audio tail. Source cue starts define every shot boundary except the introductory preview subdivisions. Attach narration once at master zero. Full audio duration currently 493.152 s, last cue ends 492.880 s; probe on build.

## Intro: recurring motifs, source seconds 0–24.400

| Seconds | Visual preview | Attention event |
|---|---|---|
| 0–3 | Code assembles faster along the AI branch | Code reveal and cursor movement |
| 3–6 | Separate tasks connect into a workflow | New edge and token arrival |
| 6–9 | A prototype meets growing demand | Load multiplication |
| 9–12 | Questions filter a generated application | Question checkpoints |
| 12–15 | Human context guides an AI system | Context joins the decision |
| 15–18 | Complexity separates into useful modules | Modules assemble |
| 18–21 | Programming / developers / learning predictions | Three objects acquire question marks |
| 21–24.400 | Code-output comparison leaves an unresolved choice | Useful branch gains focus |

These are visual previews, not assertions that the narration has already explained each concept. Their shapes return at full scale later.

## Six chapters: original cue indices [first, following)

Each row is a distinct shot. Its proof is expressed by a change in objects, not a sentence overlay. Reveal components progressively. At every gap approaching 3 s, cue a new relevant focus, path reveal, token arrival, comparison, or transformation. Continuous background motion alone does not count. Never add unrelated decoration to satisfy cadence.

| Chapter / source window | Cues | What the shot proves and what changes |
|---|---|---|
| Code value / 0–107.560 | 68–106 | Code production accelerates while a useful outcome still needs understanding: output stacks grow beside a guided system. |
| | 106–173 | Language, syntax, loops, functions and structures assemble into software: a compact code apparatus reveals its modules. |
| | 173–210 | Documentation, debugging and boilerplate compress into a prompt-driven pipeline. |
| | 210–232 | Production cost falls; decision importance rises: conceptual opposing curves, no invented numerical axis. |
| | 232–258 | Working software can miss the real need: two apps receive the same input, only one produces the useful output. |
| | 258–300 | Problem selection, dependencies, failure anticipation and design form a guided system. |
| | 300–306 | Programming is a thinking process: problem → understanding → useful system. |
| Systems / 107.560–174.400 | 306–339 | Isolated tasks become a connected system with feedback and constraints. |
| | 339–380 | Requests, information, spreadsheets, invoices and follow-ups are separate visible stages. |
| | 380–410 | The same five stages form one information pipeline; a token changes state as it passes through. |
| | 410–440 | Manual repetition and duplicate entry are waste: paired routes highlight the same duplicated datum. |
| | 440–477 | Removing redundancy creates a simpler enter-once workflow; obsolete branches fade away. |
| Optimization / 174.400–229.760 | 477–506 | A correct answer is a starting point: prototype input reaches output, then demand arrives. |
| | 506–539 | Load changes the problem: data ×1→×1,000; users 10→10 million; cost $1→$1,000 at original spoken cues. |
| | 539–558 | Time, memory, resources and scalability constrain one another: a resource balance shifts deliberately. |
| | 558–591 | Repetition exists outside software too: daily-work cycles expose repeated decisions. |
| | 591–620 | Simplify, delegate, automate and eliminate each change a different part of the process. |
| Better questions / 229.760–330.880 | 620–664 | Two users share one AI; the first branch produces a generic working app. |
| | 664–718 | The second branch asks seven questions: audience, problem, data, mistakes, cost, growth, restraint. Reveal at cues 674,680,685,691,699,703,709. |
| | 718–771 | Questions, trade-offs and evaluation filter the result into a useful system. |
| | 771–814 | Thinking broadens production skill; reliable, secure and complex systems still require technical knowledge. |
| | 814–870 | Researcher, designer, creator and entrepreneur turn ideas into testable systems; reveal at cues 828,836,847,857. |
| | 870–903 | An idea becomes a prototype and an accessible working system. |
| Human judgment / 330.880–401.840 | 903–924 | Capability plus human context can produce a useful outcome. |
| | 924–969 | AI can generate, analyze, propose, discover and create: capabilities join a central model. |
| | 969–987 | Solving a specified problem differs from choosing a worthwhile problem. |
| | 987–1042 | Frustrations, relationships, responsibilities and consequences supply lived context; reveal at cues 1003,1010,1015,1027. |
| | 1042–1077 | A technically impressive result can fail the need: compare output quality with fit to purpose. |
| | 1077–1102 | Human intention translates into a system that acts. |
| Useful systems / 401.840–end | 1102–1160 | Tasks, jobs and syntax advantages change while understanding retains value. |
| | 1160–1198 | More code and more usefulness are different: code stacks contrast with a coherent working network. |
| | 1198–1247 | Complexity decomposes; inefficiency is removed; AI is guided; the result is evaluated. |
| | 1247–1293 | Systems, patterns, design and optimization return as four working modules at cues 1276,1281,1286,1291. |
| | 1293–1329 | AI-generated code remains directed by a human goal; understanding opens multiple possible routes. |
| | 1329–end | The opening complexity motif resolves into a working system. Hold through the final words and audio tail. |

## Motion and layout contract

Entrance 0.35–0.55 s; meaningful transformations 0.6–1.2 s; mild pulses ≤1.035×. Keep diagrams visible while new information joins. At most one dominant motion at once. Label reveals use spoken cue anchors. Camera-like movement affects graphic groups, not labels. Fixed node centers and reserved connectors prevent arrow/label collisions. Remove complete shot groups at exact source boundaries; only the final system holds through the audio tail.

Implementation refinement after the first working render: animate aligned expression terms with STIX operator writes. The film-specific renderer downsamples cached 2× layers with Lanczos; profiling found full-canvas RGBA downsizing dominated runtime. Representative comparisons to the standard 2× renderer differed by under 0.4 average channel levels out of 255; inspect the actual encoded export before marking completion.

## Build and acceptance order

1. Implement opening 0–12 s and render at 960×540/30. Inspect encoded frames before implementing the remainder.
2. Complete every shot, inspect a shot-based storyboard and clips from every chapter; refine typography, spacing, depth and cadence.
3. Audit every final-frame time for safe bounds, text/diagram collisions, transformed spacing, lifetimes and ≤3 s attention gaps. Allow only documented containment, path/node joins and halos.
4. Export a separate full MP4 at 1920×1080/30, H.264 CRF18/medium, 2× antialiasing. Decode all frames; verify count/FPS/duration and source-audio alignment. Do not call the full export verified from excerpts alone.

## Research informing design

- Mayer & Moreno, *Nine Ways to Reduce Cognitive Load in Multimedia Learning*: signaling, coherence, spatial/temporal contiguity, and reduced redundant text. https://carpentries.github.io/instructor-training/files/papers/mayer-reduce-cognitive-load-2003.pdf
- Okabe & Ito, *Color Universal Design*: distinguishable colors and redundant visual coding. https://jfly.uni-koeln.de/color/index.html
- W3C contrast and use-of-color guidance: check actual adjacent colors and add non-color cues. https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html and https://www.w3.org/WAI/WCAG21/Understanding/use-of-color.html
- Gruber et al., *States of Curiosity Modulate Hippocampus-Dependent Learning*: the opening unresolved question is a creative application of curiosity research, not evidence of a guaranteed video-retention gain. https://pubmed.ncbi.nlm.nih.gov/25284006/

The three-second cadence is the user's design requirement. Neither a universal best palette nor a guaranteed retention increase is claimed.
