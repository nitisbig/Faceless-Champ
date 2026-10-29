# Exploded turbofan assembly

A 10-second, silent, graphics-only build123d integration scene. Original stylized
high-bypass turbofan geometry, inspired by commercial jet engines; not a
dimensionally accurate Boeing engine or a manufacturer model. Black `#000000`
background throughout. All geometry is generated locally with build123d, prepared
with `parts_from_cad`, and animated/rendered through public ArchChamp APIs.

Run from the repository root with the native Python environment:

```bash
# Default: full 10 seconds, 1920×1080, 30 fps.
.venv/bin/python my-project/build123d-jet-engine/render.py --overwrite

# Lightweight motion preview: full 10 seconds, 960×540, 12 fps.
.venv/bin/python my-project/build123d-jet-engine/render.py --preview --overwrite

# Still frame or structural/key timeline checks.
.venv/bin/python my-project/build123d-jet-engine/render.py --frame 4.5 --overwrite
.venv/bin/python my-project/build123d-jet-engine/render.py --check
```

Outputs go to this project's `media/` folder. `--output`, `--width`, and `--fps`
override the default full export. Requires the existing native `cad` optional
dependencies plus FFmpeg for video; no Docker, downloads, audio, or external assets.

The engine holds assembled for the opening second, separates in staggered motion
from 1–3.6 seconds, remains exploded for inspection, reassembles from 6.05–8.7
seconds, then holds assembled to 10 seconds. The camera moves gently while the
fan, compressor, turbine modules, and shaft rotate. Casing halves lift apart to
reveal the core. All motion is source-time driven and supports arbitrary seeking.

Verification is intentionally limited to key source-time checks, a representative
frame, and the lightweight preview. The default 1080p export is not verified until
it is rendered and inspected separately.
