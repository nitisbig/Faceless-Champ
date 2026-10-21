# Euler identity · 45 seconds

Equation-only derivation on pure black (`#000000`), with matching-symbol
transformations. Native Manim 0.22/Cairo prepares immutable frames; FacelessChamp
owns the 45-second timeline, viewport composition and MP4 export. No Docker or
audio. Production library code is unchanged.

From the repository root, using Python environments with FacelessChamp and Manim:

```bash
.venv/bin/python my-project/manim-euler/render.py \
  --manim-python /tmp/fc-manim-runtime/bin/python \
  --tex-bin /tmp/fc-manim-tex/.TinyTeX/bin/x86_64-linux
```

This exports `output/euler-identity.mp4` at 1920×1080/30. The `/tmp` paths above
refer to the native environments available on this machine; replace them on
other machines. If Manim is installed in the calling environment and TeX tools
are on PATH, both arguments can be omitted. FFmpeg/ffprobe are required.

Add `--preview` for a complete 640×360/15 preview, or `--frames` to prepare that
profile and compose six representative PNGs without encoding a movie. Add
`--overwrite` when replacing an MP4. Preparation is explicit and cached separately
for each profile; the first invocation prepares all 45 seconds even for stills.

| Time | Mathematics |
| --- | --- |
| 0–4 s | Exponential Taylor series |
| 4–9 s | Substitute z = iθ |
| 9–14 s | Simplify powers of i |
| 14–19 s | Group real and imaginary terms |
| 19–24 s | Identify cosine and sine series |
| 24–28 s | Euler's formula |
| 28–32 s | Substitute θ = π |
| 32–36 s | Evaluate cos π and sin π |
| 36–39 s | Simplify to −1 |
| 39–45 s | Rearrange; hold Euler's identity |

Each transition takes two seconds. The final identity holds for four seconds.

Validation: the complete native preview was exported at 640×360/15 (675 frames,
45 seconds), decoded with FFmpeg, and six representative composed frames were
inspected. Ruff and whitespace checks pass. The 1080p export has not been run.
