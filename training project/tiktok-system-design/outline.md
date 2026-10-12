# Cue-authoritative scene outline

399 original word cues are the timing authority. Preserve the two 1 ms overlaps
with `overlap_tolerance=0.001`. Narration starts at master zero; the final state
holds until the audio ends (150.216 s in the supplied MP3). No captions or headings.
Muted context remains visible at chapter cuts; new services and emphasis follow the
listed word cues. The stages chapter begins with a video token, and the recommendation
chapter begins with the feed while the narration asks which video comes next.

| Scene | Boundary cues | Content and key triggers |
| --- | --- | --- |
| hook | 0 → 36 | Phone at cue 2; playback at 6; swipe at 9; next video at 11; viewers at 15; emphasize concurrency at 22 |
| stages | 36 → 63 | Upload at 46; processing at 48; delivery at 50; recommendations at 54; track one video at 59 |
| upload | 63 → 109 | Creator 65; request 72; gateway 75; authentication 79; upload service 86; file 89; object storage 93; metadata fields 99/100/103 and database 107 |
| processing | 109 → 162 | Raw file 111; upload 120; queued job 124; queue 127; workers 130; resolutions 139; thumbnail 141; safety 144; upload burst 155 |
| delivery | 162 → 246 | Viewer 164; feed 179; IDs 176; details 185; metadata emphasis 197; CDN 203/207; nearby copies 211/218; preload 228; swipe 241 |
| recommendations | 246 → 297 | Candidates 262; ranking 265; watch time 270; likes 272; skips 273; shares 274; video features 279; internal-design caveat 290 |
| events | 297 → 337 | Swipe 298; pipeline 305; analytics 309; interests 312; fresh signals 317; recommendations 321; likes/comments 322/324 |
| scaling | 337 → 369 | Load balancing 342; server distribution 345; cache 348; database 351; workers 353; independent growth 355; CDN 361 |
| together | 369 → audio end | Specialized services 381; APIs 385; queues 387; upload 390; recommendations 391; playback 393; concurrent paths through cue 399 and audio tail |

Use focused diagrams with stable symbols: rounded services, database/storage
cylinders, queues, and server racks. Neutral strokes are #B1ADA1, labels #F4F3EE,
active packets/highlights #C15F3C, with a black canvas and black card interiors.
Connections use authored ports and waypoints. This is an illustrative TikTok-like
architecture; the supplied narration's unpublished-internals caveat is retained.
