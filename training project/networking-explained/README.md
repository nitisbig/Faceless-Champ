# Networking Explained — v2

A silent, exactly 120-second FlowChamp training scene following one laptop opening `example.com`. This revision uses the supplied `assets/Networking_UI_Pack_assets/` pack, rounded light cards, generous spacing and concise component labels. Blue identifies requests, violet identifies DNS, and teal identifies secure traffic and responses. The scene has no narration, audio, subtitles, title cards or explanatory paragraphs.

| Time | Story beat |
| --- | --- |
| 0–14s | Laptop and browser address |
| 14–28s | Wi-Fi router and local addresses |
| 28–46s | ISP route, DNS lookup and `203.0.113.10` reply |
| 46–62s | Web server and expanding route |
| 62–78s | TCP and TLS exchanges |
| 78–94s | `GET /` request and `200 OK` reply |
| 94–110s | Response packets progressively assemble the browser page |
| 110–116s | Complete request/response replay |
| 116–120s | Completed page and topology hold |

Run these commands from this folder:

```bash
cd 'training project/networking-explained'

# Default: structural checks only. No file is written.
python3 render.py
python3 render.py --check
python3 render.py --check --output /tmp/networking-explained-v2-check.json
python3 render.py --list-scenes

# Explicit visual review commands for your feedback pass.
python3 render.py --frame 40
python3 render.py --range 46 62 --quality low
python3 render.py --storyboard --quality low

# Explicit full export: 1920×1080, 60 FPS, exactly 120 seconds, no audio.
python3 render.py --full
```

The full-export command writes `output/networking-explained-v2-full-high-60fps.mp4`. Default frame, excerpt and storyboard names also include `v2`, preserving earlier outputs. Add `--overwrite` to replace an existing v2 output. `--output PATH` selects a PNG, MP4, storyboard directory or check-report JSON according to the chosen mode. Frame times must be in `[0, 120)`; excerpts must satisfy `0 <= START < END <= 120`.

Rendering defaults to `--quality high` at 1920×1080 / 60 FPS, 2× antialiasing and CRF 18. `--quality low` selects 960×540 / 30 FPS, 2× antialiasing and CRF 20. The final profile uses the encoder's `medium` preset; previews use `veryfast`. Native 60 FPS captures the eased motion at its intended cadence; `--fps 15|30|60` remains available as a manual override. Running with no rendering mode always performs checks, even when quality or FPS options are present. The runner selects the checkout's root `.venv` when available and imports the public core and kit APIs from this checkout.

`scene.py` holds the topology, motion, timing and continuous `FlowScript`; `page.py` holds the tutorial's browser-page illustration. `main.py` exposes the `build(ctx)` kit factory. The approved design now lives in core `FlowDesign.named("networking")`, with kit `FlowBackdrop`, `FlowCard`, `FlowPopup`, and `FlowCanvas(design="networking")` adapters. Eight unchanged icons from the supplied pack and the approved backdrop are bundled in the core package. Component entrances use shared eased pop, lift and settling. Bound Bézier paths carry a soft glow and native capsule packets, reshaping as their attached components move. Connection colors ease into and out of each active exchange. IP addresses are integrated into the node cards and the browser progressively assembles its page. `checks.py` performs structural timing, silence, asset, contrast, animation and layout checks without exporting images or video.

Addresses, traffic timings and protocol exchanges are illustrative. `203.0.113.10` is the teaching example's server address; the scene does not resolve `example.com` or generate real network traffic.

Implementation validation is structural only and recorded in `verification.json`; the report is the source of truth for the checks and sample counts. The visual design was approved by the user and promoted to the library. The migrated scene retains its story and authored geometry. No new frames, storyboards or video were exported during promotion, and existing outputs are preserved. A full export of the migrated scene remains unverified: `full_export_verified: false`.
