# Stock analysis: visual plan

Core visual thesis: NVIDIA's growth is impressive, but the stock's next test is whether that growth can exceed the expectations already priced in.

## Canvas and design

1080 × 1620 (2:3), 30 fps design; testing at 540 × 810, 12 fps.
White #FFFFFF background, terracotta #C15F3C emphasis, stone #B1ADA1
rules and secondary elements, cream #F4F3EE panels. Dark #292724 typography
keeps small explanatory labels legible. Editorial Cormorant Garamond headlines,
DM Sans labels, licensed Material Symbols for chip, power, and rates.
72 px side margins; heading at y=200–330, visual at y=500–1100,
conclusion at y=1240–1390, quiet source label near y=1510.
Reveal each comparison progressively; avoid a six-panel grid that shrinks labels.
Scenes cut on exact cue boundaries, with short component fades/slide entrances.
No overlapping chapter crossfades or retimed audio. No full narration captions.

## Six scenes

| Scene | Source seconds / first cue | What it proves | Visual and cue anchors |
| --- | --- | --- | --- |
| opening | 0–7.280 / 1 | A rising stock creates a valuation question. | NVDA wordmark; conceptual line draws at cue 6 (1.360); high marker at cue 8 (2.160); question at cue 16 (4.880). Image 1: chip detail. |
| growth | 7.280–24.430 / 20 | Revenue growth is supported by AI infrastructure demand. | Chart appears with growth at cue 25 (8.890); previous-year bar first; new-quarter bar and $96.2B at cue 36 (13.140); +106% YoY at cue 39 (14.400); data-center image 2 and AI-to-NVIDIA flow at cues 48, 55, 61 (17.900, 21.420, 22.900). |
| expectations | 24.430–38.540 / 65 | A high valuation sets a high performance hurdle. | Price/expectation conceptual diagram; valuation label at cue 77 (28.710); expectation hurdle at cue 80 (30.770); ordinary growth at cue 89 (34.830); exceptional growth at cue 92 (36.280). No numeric market capitalization. |
| risks | 38.540–47.280 / 96 | Competition, power, and interest rates can obstruct the thesis. | Three stacked illustrated rows; chip competition at cue 96 (38.540), power bottleneck at cue 103 (40.830), rates pressure at cue 111 (44.000). Icon and directional arrow explain each effect. |
| verdict | 47.280–59.150 / 119 | Company quality and investment expectations are separate questions. | Strong business card at cue 126 (49.040); expectation card at cue 134 (51.900); future-growth line at cue 147 (55.770) passes expectation hurdle at cue 151 (56.840); final question at cue 154 (58.080). Image 3: abstract compute sculpture. |
| closing | 59.150–62.088 / 155 | This is an analytical comparison. | Calm closing statement, 'Analysis / Not financial advice', at cues 157 and 159; hold through the original audio tail. |

Timing comes from the original 160 word cues. SRT ends at 61.840s;
audio metadata is 62.088s. Preserve the tail. The transcript misrecognizes NVIDIA
as 'and video' / 'video', and speaks 'asterisk' several times; preserve both inputs.

## Data and image policy

Revenue comparison: NVIDIA Q2 FY2026 $46.7B versus Q2 FY2027 $96.2B,
+106% YoY, rounded from the company's dated earnings release:
https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-Second-Quarter-Fiscal-2027/
Display fiscal-quarter/source labels. All price and expectation lines are conceptual,
persistently labeled; no invented stock prices or forecasts. The spoken valuation
('five, $8 trillion') is ambiguous and undated; use a qualitative valuation label.
Image slots use image/1.png, 2.png, 3.png; prompts and placement in img-info.md.

## Verification order

First render the opening as a small working clip; then compose all scenes,
inspect a storyboard, and render short key-animation ranges around revenue,
valuation, risks, and the verdict. Decode clips and inspect timing/audio metadata.
Do not render the entire narration during implementation.
