# Replaceable editorial artwork

Save the four PNG files in `images/` beside this file. Run `python3 render.py --image auto` (the default) to load them. `--image placeholder` always shows named boxes, including when files exist; `--image required` reports missing or corrupt files. The geometry remains the same across modes. No network downloads or image generation are required to test the film.

All four images use a **760×466 design-pixel slot**, centered inside an 816×522 panel. Generate at roughly 1600×1000 (landscape). Images use contain fitting: preserve important details and leave comfortable margins. White or warm-paper edges work best. Do not put titles, labels, logos, or readable interface text into the artwork; those belong to the animated composition.

Shared style: editorial conceptual illustration, warm terracotta #C15F3C, stone #B1ADA1, warm paper #F4F3EE, white #FFFFFF, minimal dark #292724 linework, generous white space, tactile paper texture, clear silhouettes, sophisticated restrained detail. Match the style across all four images.

## 1.png — A machine can write code

- Scene: code-value, original cues 21–53, 7.040–18.360 s; right-hand slot.
- Purpose: make the opening question feel concrete without claiming that AI understands every problem.
- Prompt: "Editorial illustration of a compact computer terminal producing neat terracotta blocks of code while an abstract human hand holds a blank plan beside it. The plan and the code are visibly different objects. Warm terracotta and stone on white, subtle paper-cut depth, thin dark ink outlines, simple frontal composition, no readable text, no logos, no futuristic neon, no photorealism. Landscape 8:5 with all essential shapes inside the central seventy percent."
- Stock alternative: close-up of typing and a laptop, minimal neutral workspace; search `developer laptop hands warm daylight`. Extract a still, since this library does not import stock video.

## 2.png — The small-business workflow

- Scene: systems, original cues 339–379, 122.880–139.210 s; left-hand slot.
- Purpose: connect the diagram to everyday business work.
- Prompt: "Editorial illustration of a small-business owner's uncluttered desk with customer request envelopes, a ledger, an invoice and a laptop. A single terracotta thread quietly connects the objects. White background, warm paper shapes, thin dark outlines, no readable text or numbers, no logos, simple wide composition, tactile restrained illustration matching a modern educational explainer. Landscape 8:5."
- Stock alternative: small-business owner at a desk; search `small business invoices laptop desk natural light`.

## 3.png — Useful outside software jobs

- Scene: better-questions, original cues 814–869, 299.120–320.000 s; left-hand slot.
- Purpose: introduce the four narrated professional applications; adjacent cards reveal them at their spoken cues.
- Prompt: "One cohesive editorial illustration showing four small vignettes connected by a terracotta line: researcher with experiment apparatus, designer sketching a prototype, creator at an editing desk, entrepreneur testing a simple product. Equal visual importance, recognizable silhouettes, white and warm-paper background, stone accents, terracotta focus, subtle paper texture, no text, no logos, no busy collage borders. Landscape 8:5 with generous margins."
- Stock alternative: a licensed four-image collage of research, design, content production and startup prototyping. Keep lighting and palette consistent.

## 4.png — Human context and consequences

- Scene: human-judgment, original cues 987–1041, 363.200–381.280 s; left-hand slot.
- Purpose: illustrate lived context while the diagram explains judgment.
- Prompt: "Thoughtful editorial illustration of a person at a desk considering a simple branching plan. Around them are subtle motifs of relationships, a daily task, a responsibility and the effect of a decision on another person. Warm terracotta, stone and paper on pure white, thin dark linework, human and calm, no robot villain, no text, no logos, no moralistic symbols. Landscape 8:5, clean hierarchy and generous empty space."
- Stock alternative: person reflecting over a notebook at a desk; search `thoughtful planning notebook person daylight`.

Use artwork you have permission to use; record actual source and license in `assets/manifest.json` when supplying it. The manifest's initial entries are descriptions of intended user-supplied assets, not claims that artwork has already been obtained.
