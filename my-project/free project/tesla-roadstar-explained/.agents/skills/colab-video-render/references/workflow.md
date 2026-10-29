# Applying the export workflow

## Project integration and source timing

Implement against the current project; the skill is not a replacement scene or
renderer. Identify the public render command, native render driver, complete
dependency/input graph, cue parser, compositor, chapter boundaries and media
validators. Keep ordinary local export available. `--colab` dispatches remotely
before a Docker launch; `--check` remains local and must not allocate a VM.

Derive the final frame count from decoded narration duration and the last cue at
the selected FPS, including the audio tail. Quantize visual events on that master
clock. Preserve cue files, audio speed and intentional tiny overlaps; do not
accumulate per-cue waits or shift the source clock to suit chapter boundaries.

The shared profile is `../assets/render-profile.json`. Generate the pinned pip
requirements and native encoder options from it or copy them exactly. Native
Colab rendering uses the same Cairo scene/camera/effects; GPU encoding does not
move geometry generation or a NumPy/Pillow compositor onto the GPU.

Bundle required source modules, source narration, both subtitle variants when
referenced, voiceover text when input hashing reads it, fonts/artwork/config, and
useful formula caches. Include only matching completed chapter checkpoints.
Exclude `.git`, venvs, environment/credential files, CLI state, unrelated outputs,
logs and incomplete chunks. Resolve the actual input graph: missing `voiceover.md`
can break a source-hash preflight even when rendering never reads the prose.

## Session, installation and worker

Use the installed `colab` CLI and its actual help rather than assuming its current
authentication default. Reuse the user's existing login. Do not print access
tokens, proxy tokens or HTTP authorization headers. `--logtostderr` does not fix
all CLI versions: the tested version still opened its default home-directory log
and emitted HTTP debug details. The bundled `colab_safe.py` redirects state/history
and suppresses that logging without modifying the installation.

The helper is noninteractive and assumes an existing login. If login is missing,
complete the CLI's normal authentication in the user's terminal before using the
bounded helper; do not generate or copy credentials into the skill.

Typical short calls, using a unique session name and absolute remote paths:

```bash
python3 "$SKILL_DIR/scripts/colab_safe.py" --state-dir ./media/colab --deadline 60 -- new -s VIDEO_SESSION --gpu T4
python3 "$SKILL_DIR/scripts/colab_safe.py" --state-dir ./media/colab --deadline 60 -- url -s VIDEO_SESSION
python3 "$SKILL_DIR/scripts/colab_safe.py" --state-dir ./media/colab --deadline 300 -- upload -s VIDEO_SESSION render-inputs.zip /content/render-inputs.zip
```

Persist a public session description before long work: session name, unique
`job_id`, browser URL, profile, input fingerprint, `/content/<session>` root,
expected output path/frame count, phase and timestamps. Keep runtime proxy state
in a private CLI subdirectory. Never put its tokens into public session metadata,
archives, notebooks or recovery instructions.

Check accelerator availability when executing an authorized export. Request T4
explicitly; do not silently request a more expensive accelerator or fall back to
CPU encoding. If allocation is refused, report it and stop allocation retries;
preserve an existing session rather than creating duplicates on a polling error.

Upload and verify the bundle's SHA-256 before extraction. On the VM, install the
apt packages from the profile, then create a venv explicitly with
`/usr/bin/python3.12 -m venv <remote-root>/.venv`. The notebook's default Python
may be 3.13 and may lack pip/ensurepip; installing Ubuntu's `python3-venv` alone
does not repair that interpreter. Do not replace or upgrade the notebook kernel.
Use the venv's Python and `python -m pip` to install the pinned packages.

During an authorized export, verify `nvidia-smi` and probe the exact PyAV
`h264_nvenc` stream at 3840×2160/30 FPS with the configured options. Check actual
encode/decode success. A listed codec or an installed package is insufficient.
Stop on incompatibility instead of silently changing the requested settings.

Launch an uploaded worker as a normal detached subprocess, not by running the
renderer directly in notebook `exec` semantics:

```python
with log_path.open("a") as log:
    child = subprocess.Popen(
        [str(venv_python), "-u", str(worker_script), "--job-id", job_id],
        cwd=remote_root, stdin=subprocess.DEVNULL,
        stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
    )
```

Store the worker PID. The worker owns setup, optional sample validation when
authorized, native rendering, muxing, media checks and final result creation.
Keep the notebook launch cell short. Use existing project recovery/process
ownership helpers where appropriate. A local timeout or disconnect must not kill
the remote worker. A detached worker does not guarantee unlimited Colab lifetime.

## Native encoder and narration

Configure a PyAV stream with `video.add_stream("h264_nvenc", rate=30)`, the profile
width/height/pixel format and all six encoder options. Open MP4 with
`options={"movflags": "+faststart"}`. Use a single writer to preserve frame order;
copy each RGBA frame into an owned `av.VideoFrame` before its camera buffer can
be reset. Bound outstanding frames to two and flush encoder packets before close.
Thread count is available CPU cores capped at eight.

Render complete chapters to `.partial.mp4`, validate dimensions/FPS/frame count,
then rename atomically. Reuse a chapter only when its source/settings fingerprint,
frame interval and complete decode match. An interrupted chapter restarts at its
beginning. Do not describe this as arbitrary-frame recovery.

Concatenate validated video chunks and mux the original narration with
`-c:v copy -c:a aac -b:a 192k -ar 48000 -threads 2 -movflags +faststart`.
Trim by source samples on the unchanged master clock, reset the selected audio
interval to zero and retain the full narration tail. AAC is a re-encoding;
do not promise byte-identical compressed audio.

## Telemetry and bounded monitoring

Write JSON atomically using temporary files plus rename. Distinguish phases at
their actual boundaries:

`setup → rendering → muxing → remote_verification → ready_to_download → downloading → local_verification → completed`

Remote status/progress include `job_id`, phase, heartbeat/update time, processed
and total frames, elapsed time, measured render FPS and `eta_seconds`. Maintain a
separate append-only job log. Render ETA uses recent measured work, excluding
initialization, reused chapters and chapter restarts. Provide an ASCII progress
bar; expose mux, validation and transfer progress as separate phases. A render
ETA of zero does not cover finalization. Estimate those phases from measured
decode/transfer rates or state explicitly that no reliable ETA is available.

Read status/progress/result through file downloads, for example:

```bash
python3 "$SKILL_DIR/scripts/colab_safe.py" --state-dir ./media/colab --deadline 45 -- download -s VIDEO_SESSION /content/VIDEO_SESSION/remote/status.json ./media/colab/remote-status.json
```

Read result only when expected; a missing result during an active render is not
failure. Check matching job IDs, timestamps and worker/log evidence. Avoid a new
Jupyter execution for every poll, and avoid a long-running kernel watcher that
blocks subsequent execution-based queries. If an exec is required, use both the
CLI execution timeout and an independent local deadline. Use distinct temporary
query filenames for concurrent callers.

Existing projects may call the phase field `stage`, and may use remote
`completed` to mean only that rendering and remote checks finished. Normalize
these explicitly in the adapter. Reject conflicting fields; do not infer a
local verified download from either remote spelling.

After three consecutive bounded read failures, end monitoring with saved recovery
details. Do not allocate another VM, restart a kernel or stop a healthy render to
repair a status query. If an actual worker failure is reported, include its log
tail and preserve checkpoints instead of blindly submitting again.

The generic CLI helper deliberately returns exit 124 when its wall-clock deadline
expires. It kills only that invocation's local process group. It does not stop the
remote session. Other CLI failures keep their original exit codes. A zero exit
from `colab exec` can still contain a Python traceback: require an explicit
structured success marker and the eventual result manifest.

## Download, verification and recovery

The remote success manifest is written only after checks pass:

```json
{
  "ok": true,
  "job_id": "unique-job-id",
  "files": [{"path": "media/exports/video.mp4", "bytes": 123, "sha256": "sha256-hex"}],
  "report": {"frames": 22574, "video_decode_verified": true, "audio_alignment_verified": true}
}
```

The example frame count is illustrative; compute it for the current film.
Paths must resolve within the intended project/output root. Validate the expected
job ID, output identity and input/settings fingerprint before accepting artifacts.

Download into temporary names and verify byte count/SHA-256 before replacing
existing output. The CLI contents API may buffer a whole base64 response before
creating the local file, so it may show no byte progress. For large outputs,
prepare 16–32 MiB parts on the VM with a manifest of each part's size/hash. Use
bounded downloads and a cumulative bytes/ETA bar, verify reusable parts, assemble
locally, then verify the full file's SHA-256. Bound any remote preparation exec;
do not resubmit a render merely to prepare transfers.

Decode the complete downloaded video, check its expected dimensions, rational
FPS, frame count and duration, then verify audio start time/sample rate and
complete source windows near the beginning, middle and end. Reject truncated
audio rather than shortening reference windows to make them pass. Source-audio
alignment and encoded visual inspection are separate claims. Do not mark visual
QA or a full export verified from mocks, a smoke probe, or a preview.

Record download/verification results and export notebook history. Release the
owned VM only after the requested artifacts are safely downloaded and verified,
or when the user explicitly cancels the remote job. Save checkpoints locally
while monitoring; VM expiry destroys remote temporary storage.

For a completed remote job with a frozen terminal, inspect local process age and
the successful matching remote result. End only the stalled local monitor, then
invoke the project's dedicated download command. Do not rerun a completed worker.
For an active worker after a local disconnect, reconnect to its saved session.
For an expired VM, restore matching local checkpoints into a newly authorized
session. Never imply that a status check or recovery link itself restarts rendering.
