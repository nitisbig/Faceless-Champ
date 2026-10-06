# Stock-analysis artwork — originals preserved

Save these exact PNG names in the project's **image/** folder. Default
`python3 render.py` loads existing files and uses named boxes for missing ones.
`--image placeholder` always forces boxes; `--image required` requires all three.
The redesign uses the existing three PNGs unchanged. The prompts below are archival; no replacement artwork is requested.

Use sRGB PNG. Slots use `fit="cover"`; allow cropping around the subject.
Keep quiet editorial imagery with white #FFFFFF, cream #F4F3EE, stone #B1ADA1,
and small terracotta #C15F3C accents. Avoid text, logos, watermarks, numerical
claims and green brand colors. Charts and labels are drawn separately in code.

| File | Scene / source seconds | Slot: left, top, width, height | Suggested source size |
| --- | --- | --- | --- |
| 1.png | opening, 0.550–7.280 | 72, 1089, 936, 282 | 1872×564 |
| 2.png | growth, 18.150–24.430 | 72, 427, 936, 448 | 1872×896 |
| 3.png | verdict, 47.620–59.150 | 72, 417, 936, 222 | 1872×444 |

## 1.png — Compute, up close

Prompt: Wide editorial macro illustration of an advanced AI processor on an
off-white surface, fine etched circuit lines, pale stone casing, one subtle
terracotta copper accent, soft daylight, restrained tactile materials. Center
the chip in a wide 22:7 composition with generous negative space. No text,
logos, labels, numbers or charts. Quiet supporting artwork for an animated chart.

Stock alternative: licensed macro photo of an unbranded chip or circuit board
with neutral lighting. Crop to the central chip and keep the background quiet.

## 2.png — Infrastructure demand

Prompt: Calm architectural view down a modern data-center aisle, cream and pale
stone server racks with fine terracotta cable accents, diffuse daylight, clean
geometry, restrained editorial realism. Landscape 92:53 composition with the
aisle centered and racks away from the edges. No neon, logos, people, readable
display text, statistics or identifiable brand-specific hardware.

Stock alternative: licensed still of a server aisle or data-center buildout.
Use a neutral color grade. For stock footage, extract a licensed still: ImageSlot
currently imports images/GIFs, rather than video files.

## 3.png — Growth meets a hurdle

Prompt: Minimal physical sculpture of layered stone compute tiles on an
off-white studio surface, one tile accented in terracotta, soft side lighting,
refined editorial art direction. Very wide 89:21 banner, centered sculpture,
low visual density and generous negative space. No text, arrows, charts, logos,
or investment promises; the comparison diagram is drawn separately in code.

Stock alternative: licensed still-life of semiconductor components, neutral
architectural steps, or stacked stone blocks. Keep contrast below the headline.
