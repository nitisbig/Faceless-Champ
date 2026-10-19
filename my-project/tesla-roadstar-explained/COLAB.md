# Colab export for render.py

Test a few seconds through the complete upload, T4 render, download and media
verification workflow before a full export:

```bash
python3 cola_render.py --test-seconds 3
python3 cola_render.py
```

`cola_render.py` is an alias for `colab_render.py`; both accept the same options.
The default action exports the complete film. `--test-seconds` accepts 1–30
seconds and uses the unchanged 3840×2160/30 FPS NVENC profile. It samples the
opening on the original master clock and trims only the sample's narration to
that interval. The sample goes to `output/colab-test-4k-30fps.mp4`, passes full
decode and beginning/middle/end audio checks, and releases the owned GPU after
verified download. A sample never marks the full export verified.

The main entrypoint also accepts `python3 render.py --colab --test-seconds 3`.
If monitoring disconnects, `--resume` retains the saved job's sample/full scope.

```bash
python3 render.py --colab
python3 render.py --colab --fps 30 --quality4k
python3 render.py --colab --resume --fps 30 --quality 4k
python3 colab_render.py --status
python3 cola_render.py --diagnose
python3 colab_render.py --download --stop-after-download
```

Full export commands use the complete v1 film with `RoadsterRenderer`, the current
Faceless Champ source checkout, the same fonts and models, and unchanged source
narration/cues. The separate `render_v2.py` entrypoint retains its own workflow.
Local `render.py` exports remain available. All `render.py` exports default to
4K/30 FPS; lower local preview settings remain explicit options. `--check` stays
local even with `--colab`.

The installed `google-colab-cli` must already be authenticated using its normal
login flow. This adapter uses the existing login and isolates session state and
history under ignored `media/colab/cli/`. No credentials or CLI state enter the
upload. `python3` can submit and monitor without the visualization packages;
local media verification uses the repository `.venv` if that interpreter lacks
NumPy. Local FFmpeg/ffprobe are required.

## Fixed export profile

`colab-profile.json` records T4, 3840×2160, constant 30 FPS, Python 3.12 in a
separate venv, Manim 0.21.0, PyAV 18.1.0, NumPy 2.5.3 and Pillow 12.3.0.
Project visualization packages are pinned in `requirements-colab.txt`.
Manim is installed to retain the skill's dependency profile; this film uses its
existing Pillow/PyVista renderer. No Cairo scene is introduced.

Encoding uses PyAV `h264_nvenc`, `yuv420p`, `preset=p6`, `tune=hq`, `rc=vbr`,
`cq=18`, `b=0`, `rc-lookahead=8` and MP4 `movflags=+faststart`. One ordered
encoder writer has at most two outstanding owned RGBA frame copies. Its codec
thread count follows available CPUs, capped at eight. PyAV's stream/codec APIs
are described in the [official documentation](https://pyav.basswood.io/docs/stable/api/video.html).

The T4 accelerates encoding. PyVista can use the VM's available OpenGL backend;
the adapter preserves the library's camera, depth peeling and rendering code.
Pillow, MathText, geometry generation and other software compositing remain CPU
work. No speedup estimate is asserted without a measured remote run.

The worker requests T4 explicitly, checks `nvidia-smi`, verifies pinned package
versions, then encodes and completely decodes a two-frame NVENC capability probe
at the exact export settings. A failed allocation/probe/setup stops that attempt;
there is no CPU encoder or alternative GPU fallback. Setup, installation and
the probe occur only when an export command is actually invoked.

## Source clock and checkpoints

The final frame count is derived from decoded narration samples and the last
word cue. For the current source this is 22,149 frames, ending at 738.300 seconds.
Original word timestamps and their five 1 ms overlaps remain unchanged. Each
frame samples the absolute master time `frame_index / 30`.

The ten chapter boundaries come from `cue-plan.json` and are rounded upward to
master frame indices. Chapters are video-only, fully decoded and atomically
renamed after completion. A checkpoint is reusable only with matching
source/settings fingerprints, frame interval, byte count, SHA-256 and full decode.
Only those checkpoints can enter a subsequent upload; interrupted chapters
restart at their beginning. Completed checkpoints are saved locally while
monitoring. Colab's temporary filesystem can expire.

The final mux concatenates the video chapters with stream copy and attaches the
complete original narration at master zero as AAC 192 kb/s, 48 kHz. It does not
use `-shortest` or trim the narration tail. The master remains 738.300 seconds;
the decoded source narration remains 738.272666667 seconds.

## Monitoring and recovery

`media/colab/session.json` stores the unique session/job IDs, browser URL, source
and settings fingerprints, remote root, output identity, phases and recovery
information. It contains no access/proxy tokens. The CLI's private runtime state
is in `media/colab/cli/`. Do not delete that state while a job is active.

The upload archive has an explicit input allowlist. It includes the current
core source and fonts in their existing parent-directory layout, source media,
both SRT files, input-hash documents, scene modules and required models/artwork.
It excludes `.git`, `.aws`, `.codex`, `.agents`, environments, credentials,
unrelated outputs, logs and incomplete checkpoints. Upload SHA-256 is checked
before safe extraction.

The notebook launches a detached native worker with a persistent log and PID.
The worker writes atomic `remote/status.json`, `remote/progress.json` and
`remote/result.json`; status has a five-second heartbeat. The local monitor
downloads status every 15 seconds. Each CLI call has its own local process-group
deadline; three consecutive failed status reads stop monitoring and retain the
remote job. Ctrl+C also disconnects locally without stopping the worker.

Phases are setup, rendering, muxing, remote verification, ready to download,
downloading, local verification and completed. The frame bar shows elapsed time
and measured recent render ETA, excluding reused chapters. Muxing/validation
show ETA as unavailable until measured information exists. Render ETA reaching
zero does not mean that finalization or transfer has completed.

`--status` only reads an existing saved job. `--resume` reconnects to it; it
downloads an already completed remote result rather than launching another render.
Only an explicit resume can relaunch a worker that reported failure. A status
read failure never triggers allocation, a kernel restart or remote cancellation.
If the VM has expired, the command reports that failure and retains local
checkpoints; it does not silently allocate another VM.

If Colab returns an allocation error such as **HTTP 503 Service Unavailable**,
the command stops after that one request and reports the error without a
traceback. A bounded read of the server's assignments distinguishes a failed
allocation from an uncertain outcome or a named session that actually exists.
No upload or worker is started after an allocation error.

Google's Colab client interprets allocation-stage HTTP 503 as the requested
accelerator being unavailable. The exporter cannot force T4 availability.
`python3 cola_render.py --diagnose` reads the installed CLI version, compute-unit
balance and saved allocation failure without requesting a VM. It also attempts
the detailed eligibility API; if that API denies access, eligibility remains
unknown. A zero paid-unit balance does not establish that free GPU quota is
exhausted. Check whether Colab's browser can connect to a T4 before retrying;
free GPU availability and usage limits can vary.

References: [Google's accelerator-unavailable handling](https://github.com/googlecolab/colab-vscode/pull/511/files)
and [Colab resource limits](https://research.google.com/colaboratory/faq.html#resource-limits).

When the server confirms that no session was assigned to this request, the job
is marked `allocation_failed`. Run `python3 render.py --colab` later to make one
new attempt; the previous record is archived automatically. This also repairs
older records stuck at `allocating`. `--resume` does not allocate a replacement
for a request that never received a VM. If a session exists, resume that session;
if the outcome is uncertain, the adapter retains it and requests no further GPU.

The local state contains the recovery commands. The worker log is at
`<remote_project>/remote/job.log`; failed-worker recovery downloads its tail into
`media/colab/job.log`. Only the owned GPU is released, after verified download.

The detached worker explicitly selects Matplotlib's `Agg` backend before
importing the scene. This prevents Colab's notebook-only inline backend from
leaking into the separate Python environment. If a worker reports failure and
its renderer inputs have been repaired, update the failed job on its existing
VM with `python3 cola_render.py --resume --refresh-inputs`. This preserves the
session and sample interval, refreshes source/settings fingerprints and rejects
active or already successful remote jobs. It does not request another VM.

## Download and verification

Remote success requires a matching job ID and input/settings fingerprints,
expected output identity, complete decode, expected H.264 dimensions/FPS/frame
count, AAC sample rate/start/duration, and complete source-audio alignment windows
near the beginning, middle and end. Truncated audio windows are rejected.

Output transfers use 16 MiB parts with individual sizes/hashes and cumulative
byte progress/ETA. Matching existing parts are reusable. The assembled file's
size/SHA-256 is checked before a second complete local decode and audio check.
Only then does it atomically replace the requested output, save the verification
report, export notebook history and release the GPU. Default output:
`output/full-4k-30fps.mp4`. An existing differing output requires `--overwrite`.

Automatic media verification and encoded visual inspection are separate fields.
The adapter never claims visual inspection from media checks. Implementation
tests use mocked Colab calls and synthetic arrays: no VM, installation, capability
probe, sample clip or complete film was executed during adaptation.

```bash
../../.venv/bin/python -m pytest -q tests/test_colab_render.py
```
