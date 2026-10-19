# Neural network graphics — native Skia

A silent 60-second Faceless Champ scene, 1920 × 1080 at 30 FPS. All visible
geometry and key text use the Skia CPU renderer through public Faceless Champ
components. Native Python; no Docker or external assets. No headings or subtitles.

| Seconds | Visual |
| --- | --- |
| 0–13.5 | Four-layer network, activation pulses and forward-flowing packets |
| 13–26 | Scattered embeddings resolve into three semantic neighborhoods |
| 25.5–39 | Token connections and a causal attention matrix with a moving query |
| 38.5–51.5 | Coral gradient arrows flow backward; illustrative loss decreases |
| 51–60 | Return to the forward network with traveling signals |

The neural weights and sigmoid activation sizes are deterministic. Embedding
coordinates, attention scores, and loss values are authored illustrations rather
than output from a trained model. Causal attention rows normalize to one;
future-token cells are masked. Colors distinguish signal, latent structure, and
backward gradients. Small labels identify tokens, axes, variables, and loss only.

Run from the repository root:

```bash
.venv/bin/python my-project/skia-neural-network/render.py --overwrite
```

Output: `output/skia-neural-network.mp4` inside this project.

Optional source-clock samples:

```bash
.venv/bin/python my-project/skia-neural-network/render.py --frame 33 --overwrite
.venv/bin/python my-project/skia-neural-network/render.py --preview --overwrite
.venv/bin/python my-project/skia-neural-network/render.py --range 39 44 --output /tmp/backprop.mp4
```

`--quality 4k` selects 3840 × 2160; default is 1080p. `--preview` exports only
seconds 3–5. JSON sidecars record source range and renderer identity.

Verification is limited to five key frames, a repeated-frame determinism check,
project lint, and a two-second MP4 sample with metadata/decode checks. The full
60-second export has not been verified. No broad package tests or benchmarks
were run.
