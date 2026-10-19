"""Offline Colab contract tests. Never allocate a VM, install remotely or render."""

import os
import subprocess
import sys
import time
import types
import zipfile
from pathlib import Path

import colab_common as common
import colab_control as control
import colab_remote as worker
import colab_render as driver
import numpy as np
import pytest
import render


def test_export_defaults_and_required_colab_spellings():
    for argv in (["--colab"], ["--colab", "--quality4k", "--fps", "30"], ["--colab", "--resume", "--quality", "4k"]):
        args = render.parse_args(argv)
        assert args.full and args.quality == "4k" and args.fps == 30
    for argv in (["--full"], ["--preview"], ["--range", "0", "2"], ["--frame", "0"]):
        args = render.parse_args(argv)
        assert args.quality == "4k" and args.fps == 30
    assert render.parse_args(["--preview", "--quality", "low", "--fps", "10"]).quality == "low"
    for argv in (["--resume"], ["--colab", "--fps", "15"], ["--colab", "--quality", "low"], ["--colab", "--preview"]):
        with pytest.raises(SystemExit):
            render.parse_args(argv)


def test_dispatch_before_drawing_runtime(monkeypatch):
    calls = []
    monkeypatch.setattr(driver, "start", lambda **kwargs: calls.append(kwargs))
    render.main(["--colab", "--resume"])
    assert calls == [{"resume": True, "output": None, "overwrite": False}]


def test_check_stays_local_even_with_colab(monkeypatch):
    import scene.qa
    import scene.story

    class Renderer:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

    monkeypatch.setattr(driver, "start", lambda **_: pytest.fail("--check allocated a VM"))
    monkeypatch.setattr(scene.story, "RoadsterRenderer", Renderer)
    monkeypatch.setattr(scene.story, "build_master", lambda: None)
    monkeypatch.setattr(scene.qa, "check_project", lambda _: {"passed": True})
    render.main(["--check", "--colab"])


def test_input_bundle_keeps_current_source_fonts_and_excludes_private_state(tmp_path):
    files = common.inputs()
    names = set(files)
    for name in (
        "audio.mp3",
        "cue-per-word.srt",
        "normal-subtitle.srt",
        "scene-plan.md",
        "source-fingerprints.json",
        "scene/v1_drawing.py",
    ):
        assert str(common.PROJECT / name) in names
    assert "repo/src/faceless_champ/__init__.py" in names
    assert "repo/src/faceless_champ/assets/DejaVuSans.ttf" in names
    assert "repo/assets/fonts/DMSans[opsz,wght].ttf" in names
    assert not any(
        set(Path(name).parts) & {".git", ".aws", ".codex", ".agents", ".venv", "media", "output", "__pycache__"}
        for name in names
    )
    assert not any(Path(name).name.startswith(".env") or Path(name).suffix == ".pyc" for name in names)
    # Small representative archive exercises the same allowlist writer.
    selected = {name: files[name] for name in names if name.endswith("scene/v1_drawing.py")}
    archive = tmp_path / "bundle.zip"
    common.bundle(archive, selected)
    with zipfile.ZipFile(archive) as stream:
        assert set(stream.namelist()) == set(selected)


def test_timing_uses_decoded_audio_tail_and_frame_quantized_chapters(tmp_path, monkeypatch):
    (tmp_path / "cue-per-word.srt").write_text("1\n00:00:00,000 --> 00:00:02,001\nx\n")
    common.atomic_json(tmp_path / "cue-plan.json", {"chapters": [{"start": 0}, {"start": 1.011}]})
    monkeypatch.setattr(common, "decoded_audio_duration", lambda _: 2.072)
    clock = common.timing(tmp_path)
    assert clock["expected_frames"] == 63
    assert clock["chapters"] == [{"chapter": 1, "first": 0, "stop": 31}, {"chapter": 2, "first": 31, "stop": 63}]
    assert clock["audio_duration"] == 2.072


@pytest.fixture
def job():
    return {
        "job_id": "a" * 32,
        "session": "roadster-offline-test",
        "created": time.time() - 1,
        "input_fingerprint": "source",
        "settings_fingerprint": "settings",
        "expected_frames": 300,
        "audio_duration": 10,
        "profile": common.profile(),
        "inventory": {},
    }


def result_for(job, payload=b"offline-artifact"):
    digest = __import__("hashlib").sha256(payload).hexdigest()
    part = {"path": "remote/transfer/part-00000", "bytes": len(payload), "sha256": digest}
    return {
        "ok": True,
        **{key: job[key] for key in ("job_id", "input_fingerprint", "settings_fingerprint")},
        "files": [{**part, "path": job.get("artifact_path", common.OUTPUT), "parts": [part]}],
        "report": {"frames": job["expected_frames"], "video_decode_verified": True, "audio_alignment_verified": True},
    }


@pytest.mark.parametrize(
    "field,value",
    [("job_id", "stale"), ("ok", False), ("input_fingerprint", "other"), ("settings_fingerprint", "other")],
)
def test_reject_stale_results(job, field, value):
    result = result_for(job)
    result[field] = value
    with pytest.raises(ValueError):
        common.validate_result(result, job)


@pytest.mark.parametrize(
    "mutation", ["traversal", "bad_hash", "missing_parts", "bad_size", "unverified", "wrong_frames"]
)
def test_reject_corrupt_manifest(job, mutation):
    result = result_for(job)
    file = result["files"][0]
    if mutation == "traversal":
        file["parts"][0]["path"] = "../../private"
    elif mutation == "bad_hash":
        file["sha256"] = "oops"
    elif mutation == "missing_parts":
        file["parts"] = []
    elif mutation == "bad_size":
        file["bytes"] = "1"
    elif mutation == "unverified":
        result["report"]["audio_alignment_verified"] = False
    elif mutation == "wrong_frames":
        result["report"]["frames"] = 299
    with pytest.raises(ValueError):
        common.validate_result(result, job)


def test_legacy_remote_completed_does_not_mean_downloaded(job):
    data = common.telemetry({"job_id": job["job_id"], "stage": "completed", "updated": time.time()}, job)
    assert data["phase"] == "ready_to_download"
    with pytest.raises(ValueError, match="Conflicting"):
        common.telemetry({**data, "phase": "rendering"}, job)
    with pytest.raises(ValueError, match="timestamp"):
        common.telemetry({"job_id": job["job_id"], "phase": "rendering", "updated": 0}, job)


def test_checkpoint_rejects_changed_source_interval_and_partial_data(tmp_path, job, monkeypatch):
    clip = tmp_path / "chapter-01.mp4"
    clip.write_bytes(b"checkpoint")
    record = clip.with_suffix(".json")
    chapter = {"chapter": 1, "first": 0, "stop": 30}
    data = {
        **common.file_record(clip, "remote/chapters/chapter-01.mp4"),
        "interval": chapter,
        **{key: job[key] for key in ("input_fingerprint", "settings_fingerprint")},
    }
    common.atomic_json(record, data)
    monkeypatch.setattr(common, "verify_video", lambda *_: None)
    assert common.checkpoint_valid(clip, record, job, chapter)
    assert not common.checkpoint_valid(clip, record, {**job, "input_fingerprint": "changed"}, chapter)
    assert not common.checkpoint_valid(clip, record, job, {**chapter, "first": 1})
    clip.write_bytes(b"partial")
    assert not common.checkpoint_valid(clip, record, job, chapter)


@pytest.fixture
def offline_pipeline(tmp_path, monkeypatch):
    state = tmp_path / "media/colab"
    source = tmp_path / "input.py"
    source.write_text("# source\n")
    files = {"repo/source.py": source}
    monkeypatch.setattr(driver, "STATE", state)
    monkeypatch.setattr(driver, "ROOT", tmp_path)
    monkeypatch.setattr(driver, "inputs", lambda: files)
    monkeypatch.setattr(driver, "source_integrity", dict)
    monkeypatch.setattr(driver, "timing", lambda: {"expected_frames": 300, "audio_duration": 10, "chapters": []})
    monkeypatch.setattr(driver.time, "sleep", lambda _: None)
    calls = []
    payload = b"offline-artifact"

    class FakeCLI:
        def __call__(self, arguments, deadline=45):
            args = list(map(str, arguments))
            calls.append((args, deadline))
            assert 0 < deadline <= 300
            if args[0] == "sessions":
                return "[colab] No active sessions found on server.\n"
            if args[0] == "url":
                return "https://colab.research.google.com/notebooks/empty.ipynb?dbu=test"
            if args[0] == "exec":
                script = Path(args[args.index("--file") + 1]).read_text()
                compile(script, "<remote-launch>", "exec")
                return "ROADSTER_LAUNCH_OK:" + common.read_json(state / "session.json")["job_id"]
            if args[0] == "download":
                saved = common.read_json(state / "session.json")
                path = Path(args[-1])
                if args[-2].endswith("status.json"):
                    common.atomic_json(
                        path, {"job_id": saved["job_id"], "phase": "ready_to_download", "updated": time.time()}
                    )
                elif args[-2].endswith("result.json"):
                    common.atomic_json(path, result_for(saved, payload))
                elif "/transfer/" in args[-2]:
                    path.write_bytes(payload)
                else:
                    pytest.fail(f"Unexpected remote read: {args}")
            return ""

    def verified(path, saved):
        assert path.read_bytes() == payload
        assert not any(args[0] == "stop" for args, _ in calls)
        return {"full_export_verified": True, "encoded_visual_inspection_passed": False}

    monkeypatch.setattr(driver, "CLI", FakeCLI)
    monkeypatch.setattr(driver, "verify_local", verified)
    return state, calls, tmp_path / common.OUTPUT


def test_mocked_complete_lifecycle_releases_only_after_verified_download(offline_pipeline):
    state, calls, output = offline_pipeline
    assert driver.start() == output
    assert output.read_bytes() == b"offline-artifact"
    saved = common.read_json(state / "session.json")
    assert saved["phase"] == "completed" and saved["gpu_released"]
    assert saved["profile"]["video"]["fps"] == 30
    assert [args[0] for args, _ in calls].count("new") == 1
    assert [args[0] for args, _ in calls][-1] == "stop"
    assert not (state / "render-inputs.zip").read_bytes().find(b"credentials") >= 0


def test_completed_remote_recovery_downloads_without_launching(offline_pipeline, monkeypatch):
    state, calls, output = offline_pipeline
    monkeypatch.setattr(driver, "monitor", lambda *_: None)
    driver.start()
    calls.clear()
    driver.main(["--status"])
    assert [args[0] for args, _ in calls] == ["download"]
    assert not output.exists()
    calls.clear()
    driver.main(["--download", "--stop-after-download"])
    assert output.exists()
    assert not any(args[0] in {"new", "exec", "upload"} for args, _ in calls)
    assert common.read_json(state / "session.json")["gpu_released"]


def test_three_bounded_read_failures_preserve_remote_job(offline_pipeline, monkeypatch):
    state, calls, _ = offline_pipeline
    monkeypatch.setattr(driver, "remote_status", lambda *_: (_ for _ in ()).throw(RuntimeError("timeout")))
    with pytest.raises(RuntimeError, match="three failures"):
        driver.start()
    assert not any(args[0] == "stop" for args, _ in calls)
    assert common.read_json(state / "session.json")["phase"] == "setup"
    assert [args[0] for args, _ in calls].count("new") == 1


def test_failed_local_verification_preserves_existing_output_and_gpu(offline_pipeline, monkeypatch):
    _, calls, output = offline_pipeline
    output.parent.mkdir(parents=True)
    output.write_bytes(b"existing")
    monkeypatch.setattr(driver, "verify_local", lambda *_: (_ for _ in ()).throw(ValueError("bad audio")))
    with pytest.raises(ValueError, match="bad audio"):
        driver.start(overwrite=True)
    assert output.read_bytes() == b"existing"
    assert not any(args[0] == "stop" for args, _ in calls)


def test_failed_transfer_is_rejected_before_local_decode(offline_pipeline, monkeypatch):
    _, calls, _ = offline_pipeline
    original = driver.CLI

    class CorruptCLI(original):
        def __call__(self, arguments, deadline=45):
            result = super().__call__(arguments, deadline)
            if str(arguments[0]) == "download" and "/transfer/" in str(arguments[-2]):
                Path(arguments[-1]).write_bytes(b"corrupt")
            return result

    monkeypatch.setattr(driver, "CLI", CorruptCLI)
    monkeypatch.setattr(driver, "verify_local", lambda *_: pytest.fail("Corrupt transfer reached the decoder"))
    with pytest.raises(ValueError, match="size/SHA-256"):
        driver.start()
    assert not any(args[0] == "stop" for args, _ in calls)


def test_audio_validation_rejects_truncated_windows(job, monkeypatch, tmp_path):
    rng = np.random.default_rng(123)
    samples = rng.normal(size=80000).astype("<f4")
    info = {
        "streams": [
            {"codec_type": "audio", "codec_name": "aac", "sample_rate": "48000", "start_time": "0", "duration": "10"}
        ]
    }
    monkeypatch.setattr(common, "verify_video", lambda *_: info)
    monkeypatch.setattr(common.subprocess, "check_output", lambda args: samples.tobytes())
    report = common.verify_export(tmp_path / "encoded.mp4", job)
    assert report["audio_alignment_verified"] and len(report["audio_windows"]) == 3
    monkeypatch.setattr(
        common.subprocess,
        "check_output",
        lambda args: (samples[:-1000] if "encoded.mp4" in args[args.index("-i") + 1] else samples).tobytes(),
    )
    with pytest.raises(ValueError, match="Truncated"):
        common.verify_export(tmp_path / "encoded.mp4", job)


def test_three_second_test_retains_master_clock_and_full_export_identity():
    clock = {
        "expected_frames": 22149,
        "audio_duration": 738.272666667,
        "chapters": [{"chapter": 1, "first": 0, "stop": 1548}, {"chapter": 2, "first": 1548, "stop": 3028}],
    }
    sample = common.select_test(clock, 3)
    assert sample["expected_frames"] == 90 and sample["audio_duration"] == 3
    assert sample["master_frames"] == 22149 and sample["artifact_path"] == common.SAMPLE_OUTPUT
    assert sample["chapters"] == [{"chapter": 1, "first": 0, "stop": 90}]
    assert clock["chapters"][0]["stop"] == 1548
    for seconds in (0, -1, 0.1, 31, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="between 1 and 30"):
            common.select_test(clock, seconds)


def test_sample_dispatches_and_downloads_separately(offline_pipeline, monkeypatch):
    state, calls, full_output = offline_pipeline
    sample_output = driver.start(test_seconds=3)
    assert sample_output != full_output and sample_output.name == Path(common.SAMPLE_OUTPUT).name
    assert sample_output.read_bytes() == b"offline-artifact" and not full_output.exists()
    saved = common.read_json(state / "session.json")
    assert saved["is_sample"] and saved["expected_frames"] == 90 and saved["master_frames"] == 300
    assert saved["gpu_released"] and [args[0] for args, _ in calls].count("new") == 1
    calls.clear()
    monkeypatch.setattr(driver, "start", lambda **kwargs: calls.append(kwargs))
    render.main(["--colab", "--test-seconds", "3"])
    assert calls == [{"resume": False, "output": None, "overwrite": False, "test_seconds": 3}]
    calls.clear()
    driver.main(["--test-seconds", "3"])
    assert calls == [{"resume": False, "output": None, "overwrite": False, "test_seconds": 3}]


def test_sample_audio_checks_complete_windows_and_never_certifies_full_export(job, monkeypatch, tmp_path):
    rng = np.random.default_rng(32)
    source = rng.normal(size=80000).astype("<f4")
    sample = source[:24000]
    info = {
        "streams": [
            {"codec_type": "audio", "codec_name": "aac", "sample_rate": "48000", "start_time": "0", "duration": "3"}
        ]
    }
    sample_job = {**job, "is_sample": True, "audio_duration": 3, "expected_frames": 90}
    monkeypatch.setattr(common, "verify_video", lambda *_: info)
    monkeypatch.setattr(
        common.subprocess,
        "check_output",
        lambda args: (sample if "encoded.mp4" in args[args.index("-i") + 1] else source).tobytes(),
    )
    report = common.verify_export(tmp_path / "encoded.mp4", sample_job)
    assert report["audio_alignment_verified"] and report["sample_export_verified"]
    assert not report["full_export_verified"] and len(report["audio_windows"]) == 3
    assert len({w["offset"] for w in report["audio_windows"]}) == 3
    sample = sample[:-1000]
    with pytest.raises(ValueError, match="Truncated"):
        common.verify_export(tmp_path / "encoded.mp4", sample_job)


def test_sample_allocation_failure_preserves_test_scope(offline_pipeline, monkeypatch, capsys):
    state, calls, _ = offline_pipeline
    original = driver.CLI

    class UnavailableCLI(original):
        def __call__(self, arguments, deadline=45):
            result = super().__call__(arguments, deadline)
            if arguments[0] == "new":
                raise unavailable_error()
            return result

    monkeypatch.setattr(driver, "CLI", UnavailableCLI)
    with pytest.raises(RuntimeError, match=r"Retry later.*--test-seconds 3"):
        driver.start(test_seconds=3)
    assert [args[0] for args, _ in calls] == ["new", "sessions"]
    assert common.read_json(state / "session.json")["phase"] == "allocation_failed"
    assert "Retry later: python3 render.py --colab --test-seconds 3" in capsys.readouterr().out
    calls.clear()
    for seconds in (-1, 0.5, 31, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="between 1 and 30"):
            driver.start(test_seconds=seconds)
    assert not calls


def test_encoder_uses_fixed_nvenc_profile_and_thread_cap(monkeypatch, tmp_path):
    stream = types.SimpleNamespace(codec_context=types.SimpleNamespace())
    calls = []

    class Container:
        def add_stream(self, codec, rate):
            calls.append((codec, rate))
            return stream

    def opened(path, mode, **kwargs):
        assert mode == "w" and kwargs["options"] == {"movflags": "+faststart"}
        return Container()

    monkeypatch.setitem(sys.modules, "av", types.SimpleNamespace(open=opened))
    monkeypatch.setattr(os, "sched_getaffinity", lambda _: set(range(32)))
    settings = common.profile()
    worker.open_encoder(tmp_path / "video.mp4", settings)
    assert calls == [("h264_nvenc", 30)]
    assert (stream.width, stream.height, stream.pix_fmt) == (3840, 2160, "yuv420p")
    assert stream.options == {"preset": "p6", "tune": "hq", "rc": "vbr", "cq": "18", "b": "0", "rc-lookahead": "8"}
    assert stream.codec_context.thread_count == 8


def test_deadline_helper_kills_only_local_invocation(tmp_path, monkeypatch, capsys):
    killed = []

    class Hung:
        pid = 98765
        attempts = 0

        def communicate(self, timeout=None):
            if timeout is not None:
                raise subprocess.TimeoutExpired("fake", timeout)
            return "", "Bearer private-token"

    monkeypatch.setattr(control, "find_cli_python", lambda _: sys.executable)
    monkeypatch.setattr(control.subprocess, "Popen", lambda *_, **__: Hung())
    monkeypatch.setattr(control.os, "killpg", lambda *args: killed.append(args))
    result = control.main(["--state-dir", str(tmp_path), "--deadline", "0.1", "--", "status", "-s", "saved"])
    assert result == 124 and killed == [(98765, control.signal.SIGKILL)]
    text = capsys.readouterr().err
    assert "private-token" not in text and "remote VM/job was not stopped" in text


@pytest.mark.parametrize("fail", [False, True])
@pytest.mark.parametrize("sample", [False, True])
def test_worker_preserves_frame_order_absolute_clock_and_bounded_owned_copies(tmp_path, job, monkeypatch, fail, sample):
    if sample:
        job.update(is_sample=True, expected_frames=90, master_frames=300)
    shared = np.zeros((2, 2, 4), dtype=np.uint8)
    times, encoded, outstanding = [], [], []
    counts = {"created": 0, "finished": 0}
    settings = job["profile"]["video"]
    settings.update(width=2, height=2)
    chapter = {"chapter": 2, "first": 30, "stop": 36}

    class Renderer:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def validate(self, _):
            pass

        def frame(self, master, at, size):
            times.append(at)
            shared.fill(len(times))
            return types.SimpleNamespace(convert=lambda _: shared)

    def copied(array, format):
        counts["created"] += 1
        outstanding.append(counts["created"] - counts["finished"])
        return types.SimpleNamespace(array=array)

    def encode(container, stream, frame):
        time.sleep(0.002)
        if fail and frame.pts == 1:
            raise RuntimeError("encoder failure")
        encoded.append((frame.pts, frame.time_base, int(frame.array[0, 0, 0])))
        counts["finished"] += 1

    path = tmp_path / "remote/chapters/chapter-02.mp4"
    partial = path.with_suffix(".partial.mp4")
    monkeypatch.setattr(worker, "ROOT", tmp_path)
    monkeypatch.setattr(worker, "checkpoint_valid", lambda *_: False)
    monkeypatch.setattr(worker, "open_encoder", lambda *_: (types.SimpleNamespace(close=lambda: None), None))
    monkeypatch.setattr(worker, "encode", encode)
    monkeypatch.setattr(worker, "finish", lambda *_: partial.write_bytes(b"encoded"))
    monkeypatch.setattr(
        worker, "verify_video", lambda path, frames, _: frames == 6 or pytest.fail("Wrong chapter length")
    )
    monkeypatch.setitem(sys.modules, "av", types.SimpleNamespace(VideoFrame=types.SimpleNamespace(from_ndarray=copied)))
    monkeypatch.setitem(
        sys.modules,
        "scene.story",
        types.SimpleNamespace(RoadsterRenderer=Renderer, build_master=lambda: types.SimpleNamespace(duration=10)),
    )
    status = types.SimpleNamespace(update=lambda **_: None)
    if fail:
        with pytest.raises(RuntimeError, match="encoder failure"):
            worker.render_chapter(job, chapter, status)
        assert not path.exists() and not path.with_suffix(".json").exists()
    else:
        assert worker.render_chapter(job, chapter, status) == path
        assert times == [index / 30 for index in range(30, 36)]
        assert [(pts, pixel) for pts, _, pixel in encoded] == list(enumerate(range(1, 7)))
        assert max(outstanding) <= 2
        assert common.read_json(path.with_suffix(".json"))["interval"] == chapter


def test_resume_interrupted_upload_reuses_existing_session(offline_pipeline, monkeypatch):
    state, calls, _ = offline_pipeline
    monkeypatch.setattr(driver, "monitor", lambda *_: None)
    driver.start()
    saved = common.read_json(state / "session.json")
    driver.save(saved, phase="uploading")
    calls.clear()
    driver.start(resume=True)
    assert not any(args[0] == "new" for args, _ in calls)
    assert [args[0] for args, _ in calls] == ["url", "upload", "upload", "exec"]


def test_detached_worker_uses_agg_despite_inherited_notebook_backend():
    script = """import colab_common, colab_remote
colab_remote.configure_environment({'profile': colab_common.profile()})
from scene.v1_drawing import V1Painter
import matplotlib
assert matplotlib.get_backend().lower() == 'agg'
print('AGG_WORKER_IMPORT_OK')
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=common.ROOT,
        env={**os.environ, "MPLBACKEND": "module://matplotlib_inline.backend_inline"},
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "AGG_WORKER_IMPORT_OK" in result.stdout


def test_repair_changed_inputs_reuses_failed_workers_vm(offline_pipeline, monkeypatch):
    state, calls, _ = offline_pipeline
    monkeypatch.setattr(driver, "monitor", lambda *_: None)
    driver.start(test_seconds=3)
    old = common.read_json(state / "session.json")
    (state.parents[1] / "input.py").write_text("# repaired renderer\n")
    monkeypatch.setattr(driver, "remote_status", lambda *_: {"phase": "failed"})
    calls.clear()
    driver.start(resume=True, refresh_inputs=True)
    repaired = common.read_json(state / "session.json")
    assert repaired["session"] == old["session"] and repaired["job_id"] == old["job_id"]
    assert repaired["input_fingerprint"] != old["input_fingerprint"]
    assert repaired["expected_frames"] == 90 and repaired["is_sample"]
    assert [args[0] for args, _ in calls] == ["upload", "upload", "exec"]
    assert list(state.glob(f"session-{old['job_id']}-before-repair-*.json"))


@pytest.mark.parametrize("phase", ["rendering", "ready_to_download"])
def test_repair_never_mutates_an_active_or_completed_remote_job(offline_pipeline, monkeypatch, phase):
    state, calls, _ = offline_pipeline
    monkeypatch.setattr(driver, "monitor", lambda *_: None)
    driver.start()
    original = common.read_json(state / "session.json")
    monkeypatch.setattr(driver, "remote_status", lambda *_: {"phase": phase})
    calls.clear()
    with pytest.raises(RuntimeError, match="requires a failed worker"):
        driver.start(resume=True, refresh_inputs=True)
    assert common.read_json(state / "session.json") == original and not calls


def test_transport_error_reports_status_without_traceback_or_private_request(capsys):
    error = RuntimeError("https://private.example/?token=secret")
    error.response = types.SimpleNamespace(status_code=503)
    assert control.report_request_error(error, ["new", "-s", "test", "--gpu", "T4"]) == 1
    output = capsys.readouterr().err
    failure = driver.CLIError("new", 1, output)
    assert failure.http_status == 503
    assert str(failure) == "Colab new failed: HTTP 503 Service Unavailable."
    assert "secret" not in output and "private.example" not in output and "Traceback" not in output


@pytest.mark.parametrize("eligibility", [True, False, None])
def test_account_diagnostics_never_allocates_or_treats_zero_balance_as_exhausted(monkeypatch, eligibility):
    calls = []
    monkeypatch.setattr(control.importlib.metadata, "version", lambda _: "0.7.4")

    class Client:
        colab_api_domain = "https://colab.pa.googleapis.com"

        def get_consumption_user_info(self):
            calls.append("usage")
            return types.SimpleNamespace(paid_compute_units_balance=0, assignments_count=0)

        def _issue_request(self, url, **kwargs):
            calls.append(url)
            assert kwargs == {"params": {"get_ccu_consumption_info": "true"}, "schema": dict, "timeout": 15}
            if eligibility is None:
                error = RuntimeError("secret token in untrusted response")
                error.response = types.SimpleNamespace(status_code=403)
                raise error
            return {
                "eligibleAccelerators": [{"models": ["T4"]}] if eligibility else [],
                "ineligibleAccelerators": [] if eligibility else [{"models": ["T4"]}],
                "access_token": "never publish",
                "freeCcuQuotaInfo": {"remainingTokens": "123", "token": "never publish"},
            }

    report = control.account_diagnostics(Client())
    assert report["t4_eligible"] is eligibility and report["paid_compute_units"] == 0
    assert report["allocation_requests"] == 0
    assert calls == ["usage", "https://colab.pa.googleapis.com/v1/user-info"]
    assert "never publish" not in str(report) and "secret" not in str(report)
    if eligibility is None:
        assert report["eligibility_http_status"] == 403


def test_diagnose_is_read_only_and_needs_no_saved_job(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(driver, "STATE", tmp_path / "state")

    class CLI:
        def __call__(self, arguments, deadline):
            calls.append(arguments)
            assert deadline == 45
            return '{"paid_compute_units": 0, "allocation_requests": 0}'

    monkeypatch.setattr(driver, "CLI", CLI)
    monkeypatch.setattr(driver, "start", lambda **_: pytest.fail("Diagnostics allocated a VM"))
    result = driver.main(["--diagnose"])
    assert calls == [["diagnostics"]] and result["allocation_requests"] == 0
    assert not (tmp_path / "state/session.json").exists()
    assert common.read_json(tmp_path / "state/diagnostics.json") == result


def unavailable_error():
    return driver.CLIError(
        "new", 1, control.ERROR_PREFIX + '{"kind":"http_error","http_status":503,"reason":"Service Unavailable"}'
    )


def test_allocation_503_stops_once_and_next_manual_attempt_is_not_blocked(offline_pipeline, monkeypatch):
    state, calls, output = offline_pipeline
    original = driver.CLI

    class UnavailableCLI(original):
        def __call__(self, arguments, deadline=45):
            result = super().__call__(arguments, deadline)
            if arguments[0] == "new":
                raise unavailable_error()
            return result

    monkeypatch.setattr(driver, "CLI", UnavailableCLI)
    with pytest.raises(RuntimeError, match="HTTP 503.*Retry later") as failed_request:
        driver.start()
    assert "could not supply the requested T4" in str(failed_request.value)
    assert "--diagnose" in str(failed_request.value)
    failed = common.read_json(state / "session.json")
    assert failed["phase"] == "allocation_failed" and failed["allocation_assigned"] is False
    assert failed["allocation_error"]["http_status"] == 503
    assert [args[0] for args, _ in calls] == ["new", "sessions"]
    assert not output.exists()
    # Each explicit invocation gets exactly one attempt; no automatic retries.
    calls.clear()
    with pytest.raises(RuntimeError, match="HTTP 503"):
        driver.start()
    assert [args[0] for args, _ in calls] == ["sessions", "new", "sessions"]
    assert common.read_json(state / "session.json")["job_id"] != failed["job_id"]
    assert common.read_json(state / f"session-{failed['job_id']}.json")["phase"] == "allocation_failed"


@pytest.mark.parametrize("server_response", ["orphan", "network_failure", "malformed"])
def test_uncertain_allocation_never_creates_another_gpu(offline_pipeline, monkeypatch, server_response):
    state, calls, _ = offline_pipeline
    original = driver.CLI

    class UncertainCLI(original):
        def __call__(self, arguments, deadline=45):
            result = super().__call__(arguments, deadline)
            if arguments[0] == "new":
                raise driver.CLIError("new", 124, "")
            if arguments[0] == "sessions":
                if server_response == "network_failure":
                    raise RuntimeError("Network unavailable")
                if server_response == "malformed":
                    return "unrecognized response"
                return "[?] orphan-endpoint | Hardware: T4 | Shape: Standard | Variant: GPU\n"
            return result

    monkeypatch.setattr(driver, "CLI", UncertainCLI)
    with pytest.raises(RuntimeError, match="unconfirmed"):
        driver.start()
    assert common.read_json(state / "session.json")["phase"] == "allocation_unknown"
    calls.clear()
    with pytest.raises(RuntimeError, match="unconfirmed"):
        driver.start()
    assert [args[0] for args, _ in calls] == ["sessions"]
    assert not any(args[0] in {"stop", "upload", "exec"} for args, _ in calls)


def test_named_session_after_allocation_error_is_preserved_for_resume(offline_pipeline, monkeypatch):
    state, calls, _ = offline_pipeline
    original = driver.CLI

    class AssignedCLI(original):
        def __call__(self, arguments, deadline=45):
            result = super().__call__(arguments, deadline)
            if arguments[0] == "new":
                raise driver.CLIError("new", 124, "")
            if arguments[0] == "sessions":
                name = common.read_json(state / "session.json")["session"]
                return f"[{name}] assigned-endpoint | Hardware: T4 | Shape: Standard | Variant: GPU\n"
            return result

    monkeypatch.setattr(driver, "CLI", AssignedCLI)
    with pytest.raises(RuntimeError, match="named session exists"):
        driver.start()
    assert common.read_json(state / "session.json")["phase"] == "allocated"
    assert [args[0] for args, _ in calls] == ["new", "sessions"]
    calls.clear()
    driver.start(resume=True)
    assert "new" not in [args[0] for args, _ in calls]
    assert common.read_json(state / "session.json")["phase"] == "completed"


def test_legacy_allocating_record_without_a_vm_allows_fresh_source_on_retry(offline_pipeline, monkeypatch):
    state, calls, output = offline_pipeline
    monkeypatch.setattr(driver, "monitor", lambda *_: None)
    driver.start()
    previous = common.read_json(state / "session.json")
    driver.save(previous, phase="allocating", url=None)
    (output.parents[1] / "input.py").write_text("# fixed renderer\n")
    calls.clear()
    driver.start()
    assert [args[0] for args, _ in calls] == ["sessions", "new", "url", "upload", "upload", "exec"]
    assert common.read_json(state / "session.json")["input_fingerprint"] != previous["input_fingerprint"]


def test_status_of_failed_allocation_reads_assignments_without_remote_files(offline_pipeline, monkeypatch, capsys):
    state, calls, _ = offline_pipeline
    monkeypatch.setattr(driver, "monitor", lambda *_: None)
    driver.start()
    driver.save(common.read_json(state / "session.json"), phase="allocating", url=None)
    calls.clear()
    driver.main(["--status"])
    assert [args[0] for args, _ in calls] == ["sessions"]
    assert common.read_json(state / "session.json")["phase"] == "allocation_failed"
    assert '"allocation_assigned": false' in capsys.readouterr().out
    calls.clear()
    with pytest.raises(RuntimeError, match="Retry later"):
        driver.start(resume=True)
    assert [args[0] for args, _ in calls] == ["sessions"]


def test_public_render_command_exits_cleanly_on_colab_failure(monkeypatch, capsys):
    def fail(**_):
        raise unavailable_error()

    monkeypatch.setattr(driver, "start", fail)
    assert render.command_line(["--colab"]) == 1
    error = capsys.readouterr().err
    assert error == "Render failed: Colab new failed: HTTP 503 Service Unavailable.\n"
    assert "Traceback" not in error


@pytest.mark.parametrize("kind", ["http", "connection"])
def test_installed_cli_transport_failures_are_caught_before_rich_tracebacks(tmp_path, kind):
    try:
        python = control.find_cli_python()
    except RuntimeError:
        pytest.skip("google-colab-cli is not installed")
    script = """import sys
from pathlib import Path
import requests
from colab_cli import cli
from colab_cli.client import ColabRequestError
import colab_control as helper
def fail():
    if sys.argv[-1] == 'connection':
        raise requests.ConnectionError('private URL and token must never appear')
    response = requests.Response()
    response.status_code = 503
    raise ColabRequestError('private URL and token must never appear', request=None, response=response)
kind = sys.argv[2]
def simulated_main():
    if kind == 'connection':
        raise requests.ConnectionError('private URL and token must never appear')
    fail()
cli.main = simulated_main
assert helper.invoke_cli(Path(sys.argv[1]), ['new', '-s', 'offline-test', '--gpu', 'T4']) == 1
"""
    result = subprocess.run(
        [python, "-c", script, str(tmp_path), kind], cwd=common.ROOT, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert control.ERROR_PREFIX in result.stderr
    assert "Traceback" not in result.stderr and "private URL" not in result.stderr
    error = driver.CLIError("new", 1, result.stderr)
    assert error.http_status == (503 if kind == "http" else None)
