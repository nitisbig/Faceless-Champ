---
name: colab-video-render
description: Add or operate saved-session Google Colab T4 exports for narration-timed Manim/Cairo videos, using 4K/30 FPS, NVENC encoding, progress and ETA, chapter recovery, and verified downloads. Use for this video-export workflow, including a completed render with a stuck local monitor; not for model training or general GPU computing.
---

# Colab GPU video rendering

Apply the established native Manim/Cairo + T4 encoding workflow to the current
video project. Preserve its visuals, source-clock narration, and public entrypoint.
The portable configuration is [assets/render-profile.json](assets/render-profile.json).
Use these settings by default for this workflow; an explicit user override wins.

## Scope and implementation

- If asked for an exporter or `render.py` without rendering, implement and validate
  locally with mocked Colab calls. Do not allocate a VM, install packages remotely,
  execute a GPU probe, or start a sample/full render in that mode.
- When an actual export is authorized, continue through upload, setup, render,
  download and verification. Reuse existing authorization; creating this skill
  alone does not authorize a new export.
- Inspect the current renderer before adapting it. Cairo geometry and software
  effects remain on the CPU; the T4 accelerates H.264 encoding. Preserve the Cairo
  camera/compositor rather than switching to OpenGL to claim GPU acceleration.
- Read [references/workflow.md](references/workflow.md) when implementing or
  recovering the pipeline. It contains the installation, worker, telemetry,
  artifact and recovery contracts. Adapt scene names, inputs and chapter logic;
  do not copy a previous film's duration, cue counts, paths or session ID.

Expose this interface when adding the workflow to a Python video project:

```bash
python3 render.py --colab --fps 30 --quality4k
python3 render.py --colab --resume --fps 30 --quality4k
python3 colab_render.py --status
python3 colab_render.py --download --stop-after-download
```

Accept `--quality 4k` as well as the user's `--quality4k` spelling. Confirm that
the project implements these commands before presenting them as runnable.

## Fixed profile

- T4; 3840 × 2160; constant 30 FPS; Python **3.12** in a separate venv.
- Manim **0.21.0**, PyAV **18.1.0**, NumPy **2.5.3**, Pillow **12.3.0**.
- PyAV `h264_nvenc`, `yuv420p`, `preset=p6`, `tune=hq`, `rc=vbr`, `cq=18`,
  `b=0`, `rc-lookahead=8`; MP4 `movflags=+faststart`.
- One encoder writer and at most two queued RGBA frame copies. Preserve frame
  order and bound memory. Encoder thread count follows available CPUs, capped at 8.
- Mux the original narration with video stream copy and AAC **192 kb/s, 48 kHz**,
  starting at master zero. Retain the complete source audio tail and supplied
  word-cue times, including tiny intentional overlaps.

Do not silently substitute CPU encoding, a different accelerator, lower
resolution/FPS, or updated package versions. Explain an actual incompatibility
and resolve it within the user's scope.

## CLI and saved-session reliability

Use the installed `google-colab-cli`. For short commands, prefer the bundled
[scripts/colab_safe.py](scripts/colab_safe.py): it isolates CLI state/history,
suppresses HTTP debug logs, and enforces a local wall-clock deadline. For example,
from the project directory, with `SKILL_DIR` set to this skill's location:

```bash
python3 "$SKILL_DIR/scripts/colab_safe.py" --state-dir ./media/colab --deadline 60 -- sessions
python3 "$SKILL_DIR/scripts/colab_safe.py" --state-dir ./media/colab --deadline 60 -- new -s VIDEO_SESSION --gpu T4
```

Use a meaningful unique session name and save the browser URL, job ID, source
fingerprint, remote root, phases and recovery commands immediately. Keep CLI
credentials private and out of the upload bundle. A saved session is discoverable;
it does not make Colab's temporary VM storage permanent.

Launch the renderer as a detached native subprocess with a persistent log.
Poll atomically written status/progress/result JSON through file downloads;
avoid running a notebook `exec` cell for every status check. A CLI `--timeout`
is not a sufficient local watchdog: a real status call hung for hours in this
workflow while the remote render completed normally. Bound each local call and
stop after three consecutive read failures, preserving the saved job.

## Completion and recovery

Report the actual phase: setup, rendering, muxing, remote verification, download,
local verification, or completed. **100% frames does not mean downloaded.**
Estimate finalization from measured work; do not promise a fixed number of minutes.

When a monitor stalls, inspect saved metadata, the remote result/log and local
processes. A successful matching result means **download existing output**;
do not start another render. Cancel only the stalled local monitor when recovery
requires it. Status checks must not allocate, restart or stop a remote VM.

Accept completion only after the matching `job_id` and `ok: true`, transfer byte
counts/SHA-256, full video decode and expected dimensions/FPS/frame count, and
source-audio alignment checks pass. Keep encoded visual inspection separate from
automatic media checks. Release the owned GPU after a successful verified
download; preserve an active job on an intended local disconnect.

Validate adaptations without a full export when requested: parser/dispatch,
upload exclusions, deadline cleanup, stale/corrupt manifest rejection and recovery
from a completed remote job. Do not label mocks or sample clips as a full export.
