"""Explicit subprocess preparation, verified cache references and atomic assets."""

from __future__ import annotations

import json
import math
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from concurrent.futures import CancelledError
from contextlib import contextmanager
from dataclasses import asdict
from fractions import Fraction
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from faceless_champ.components import finite
from faceless_champ.prepared import PreparedFrameSource, _digest, _file_digest, _write_manifest

from .model import ManimError, ManimRenderOptions, request_record

__all__ = ["load_manim", "manim_capabilities", "prepare_manim"]

CAPABILITY_METADATA = {
    "prepare_manim": {
        "family": "manim",
        "tags": ["manim", "mathematical animation", "preparation", "transparent"],
        "preparation": "explicit",
        "preparation_requirements": ["manim>=0.22,<0.23", "Cairo", "FFmpeg/ffprobe"],
        "playback_requirements": ["Pillow"],
        "output_formats": ["rgba-png-sequence"],
        "use_when": "Prepare authored mathematical scenes once, then replay them on FacelessChamp timelines.",
        "avoid": "Preparation runs trusted Python; it is not a sandbox. No implicit execution during playback.",
        "documentation": "docs/core/manim.md",
    }
}


def _atomic_json(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".reference-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(record, stream, sort_keys=True, allow_nan=False)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


class _Job:
    def __init__(self, work, log, timeout, output_limit, cancel):
        self.work, self.log = work, log
        self.deadline = time.monotonic() + finite(timeout, "timeout", 0.001)
        if type(output_limit) is not int or output_limit < 1:
            raise ValueError("output_limit must be a positive byte count")
        if cancel is not None and not callable(cancel):
            raise TypeError("cancel must be callable")
        self.output_limit, self.cancel = output_limit, cancel

    def check(self):
        if self.cancel is not None and self.cancel():
            raise CancelledError("Manim preparation cancelled")
        if time.monotonic() >= self.deadline:
            raise ManimError("MANIM_TIMEOUT", "Manim preparation deadline exceeded", log=str(self.log))
        if self.log.exists() and self.log.stat().st_size > min(self.output_limit, 8 * 1024**2):
            raise ManimError("MANIM_OUTPUT_LIMIT", "Preparation log limit exceeded", log=str(self.log))
        size = sum(p.stat().st_size for p in self.work.rglob("*") if p.is_file())
        log_size = self.log.stat().st_size if self.log.exists() and not self.log.is_relative_to(self.work) else 0
        if size + log_size > self.output_limit:
            raise ManimError("MANIM_OUTPUT_LIMIT", "Preparation output limit exceeded", log=str(self.log))

    @staticmethod
    def stop(process):
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        elif process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            pass
        # Descendants may survive an already-exited parent; close the whole group.
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        elif process.poll() is None:
            process.kill()
        process.wait(timeout=2)

    def run(self, command, *, env=None, stdout=None):
        self.check()
        with self.log.open("ab") as log:
            try:
                process = subprocess.Popen(
                    command,
                    cwd=self.work,
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=stdout if stdout is not None else log,
                    stderr=log,
                    start_new_session=os.name == "posix",
                )
            except OSError as exc:
                raise ManimError("MANIM_DEPENDENCY", f"Cannot start {command[0]}: {exc}", log=str(self.log)) from exc
            try:
                while process.poll() is None:
                    self.check()
                    time.sleep(0.05)
                self.check()
                if process.returncode:
                    raise ManimError(
                        "MANIM_RENDER", f"Preparation subprocess exited {process.returncode}", log=str(self.log)
                    )
            finally:
                self.stop(process)

    def worker(self, mode, request, python):
        input_path, output_path = self.work / f"{mode}-input.json", self.work / f"{mode}-result.json"
        input_path.write_text(json.dumps(request, sort_keys=True, allow_nan=False))
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env.update(
            PYTHONHASHSEED=str(request["options"]["seed"]),
            PYTHONDONTWRITEBYTECODE="1",
            OPENBLAS_NUM_THREADS="1",
            OMP_NUM_THREADS="1",
            MKL_NUM_THREADS="1",
        )
        env["PATH"] = str(Path(python).parent) + os.pathsep + env.get("PATH", "")
        self.run(
            [python, "-s", "-B", str(Path(__file__).with_name("_worker.py")), mode, str(input_path), str(output_path)],
            env=env,
        )
        try:
            result = json.loads(output_path.read_text())
            if not isinstance(result, dict):
                raise TypeError("Expected a worker result object")
        except (OSError, ValueError, TypeError) as exc:
            raise ManimError("MANIM_ASSET", f"Invalid worker result: {exc}", log=str(self.log)) from exc
        if "error" in result:
            raise ManimError(result["error"], result["message"], log=str(self.log))
        return result


@contextmanager
def _lock(cache, key, job):
    if os.name != "posix":
        raise ManimError("MANIM_PLATFORM", "Preparation currently supports POSIX; prepared playback is portable")
    import fcntl

    directory = cache / "locks"
    directory.mkdir(exist_ok=True)
    with (directory / (key + ".lock")).open("a") as stream:
        while True:
            job.check()
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                time.sleep(0.05)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def _load(cache, key, record):
    reference = cache / "requests" / (key + ".json")
    if not reference.is_file():
        raise ManimError("MANIM_UNPREPARED", "Run fc-kit prepare or prepare_manim before playback")
    try:
        ref = json.loads(reference.read_text())
        if ref["request"] != record:
            raise ValueError("Request mismatch")
        directory = (cache / ref["asset"]).resolve()
        if not directory.is_relative_to((cache / "assets").resolve()):
            raise ValueError("Prepared reference escapes cache assets")
        source = PreparedFrameSource(directory)
        if source.provenance["request"] != record:
            raise ValueError("Prepared request mismatch")
        return source
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ManimError("MANIM_ASSET", f"Invalid prepared asset; prepare with refresh=True: {exc}") from exc


def load_manim(spec, *, cache_dir, options=None, python=None):
    """Load a matching prepared request without probing or executing any engine."""
    options = options or ManimRenderOptions()
    key, record = request_record(spec, options, python)
    return _load(Path(cache_dir).resolve(), key, record)


def _tool_identity(job, name):
    executable = shutil.which(name)
    if executable is None:
        raise ManimError("MANIM_DEPENDENCY", f"{name} is required during preparation; install FFmpeg")
    path = job.work / f"{name}-version.txt"
    with path.open("wb") as output:
        job.run([executable, "-version"], stdout=output)
    return {"path": executable, "version": path.read_text(errors="replace")[:4000]}


def manim_capabilities(*, python=None, probe=False):
    """Static support metadata by default; probe=True explicitly starts a worker."""
    result = {
        "engine": "manim-ce",
        "supported_version": ">=0.22,<0.23",
        "renderer": "cairo",
        "output_formats": ["rgba-png-sequence"],
        "probed": False,
    }
    try:
        result["installed_version"] = version("manim") if python is None else None
    except PackageNotFoundError:
        result["installed_version"] = None
    if probe:
        with tempfile.TemporaryDirectory(prefix="fc-manim-probe-") as directory:
            work = Path(directory)
            job = _Job(work, work / "probe.log", 60, 8 * 1024**2, None)
            try:
                runtime = job.worker(
                    "probe", {"options": asdict(ManimRenderOptions())}, str(Path(python or sys.executable).absolute())
                )
                result.update(probed=True, ok=True, **runtime)
                result["installed_version"] = runtime["runtime"]["packages"].get("manim")
                result["tools"] = {name: _tool_identity(job, name) for name in ("ffmpeg", "ffprobe")}
            except ManimError as exc:
                result.update(probed=True, ok=False, error=exc.code, message=str(exc))
    return result


def prepare_manim(
    spec, *, cache_dir, options=None, python=None, timeout=600, output_limit=2 * 1024**3, refresh=False, cancel=None
):
    """Prepare trusted Manim code once; no Manim import occurs in this process.

    Runtime probing is explicit here, including on a warm cache. Normal playback
    uses load_manim or PreparedFrameSource without the producer environment.
    """
    options = options or ManimRenderOptions()
    key, record = request_record(spec, options, python)
    cache = Path(cache_dir).resolve()
    cache.mkdir(parents=True, exist_ok=True)
    logs = cache / "logs"
    logs.mkdir(exist_ok=True)
    log = logs / (key + "-" + uuid.uuid4().hex[:12] + ".log")
    with tempfile.TemporaryDirectory(prefix=".preparing-", dir=cache) as directory:
        work = Path(directory)
        job = _Job(work, log, timeout, output_limit, cancel)
        with _lock(cache, key, job):
            request = {"options": record["options"]}
            probe = job.worker("probe", request, record["python"])
            tools = {name: _tool_identity(job, name) for name in ("ffmpeg", "ffprobe")}
            execution = _digest(
                {
                    "request": record,
                    "probe": probe,
                    "tools": tools,
                    "adapter": {p.name: _file_digest(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
                }
            )
            if not refresh:
                try:
                    existing = _load(cache, key, record)
                except ManimError as exc:
                    if exc.code != "MANIM_UNPREPARED":
                        raise
                else:
                    if existing.provenance["execution"] == execution:
                        return existing
            root = work / "source"
            root.mkdir()
            for name, expected in record["spec"]["inputs"].items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(spec.source_root / name, target)
                if _file_digest(target) != expected:
                    raise ManimError("MANIM_STALE", "Input changed while staging; retry preparation")
            request.update(spec=record["spec"], source_root=str(root), media_dir=str(work / "media"))
            rendered = job.worker("render", request, record["python"])
            movie = Path(rendered["path"]).resolve()
            if not movie.is_relative_to(work) or not movie.is_file():
                raise ManimError("MANIM_ASSET", "Manim output must be a movie in the staging directory")
            info_path = work / "media-info.json"
            with info_path.open("wb") as output:
                job.run(
                    [
                        tools["ffprobe"]["path"],
                        "-v",
                        "error",
                        "-count_frames",
                        "-show_streams",
                        "-of",
                        "json",
                        str(movie),
                    ],
                    stdout=output,
                )
            streams = json.loads(info_path.read_text())["streams"]
            if len(streams) != 1 or streams[0]["codec_type"] != "video":
                raise ManimError("MANIM_SCENE", "Manim preparation accepts visuals only; add narration through Core")
            stream = streams[0]
            size, fps = [stream["width"], stream["height"]], Fraction(stream["avg_frame_rate"])
            resolved = probe["resolved"]
            if (
                size != resolved["size"]
                or abs(float(fps) - resolved["fps"]) > 0.001
                or stream["codec_name"] != "qtrle"
                or stream["pix_fmt"] != "argb"
                or Fraction(stream["r_frame_rate"]) != fps
                or abs(float(stream.get("start_time", 0))) > 1e-6
            ):
                raise ManimError("MANIM_ASSET", "Output does not match the requested lossless CFR/alpha profile")
            count = int(stream["nb_read_frames"])
            if count < 1 or not math.isfinite(count / float(fps)):
                raise ManimError("MANIM_ASSET", "Scene produced no usable frames")
            asset = work / "asset"
            (asset / "frames").mkdir(parents=True)
            job.run(
                [
                    tools["ffmpeg"]["path"],
                    "-v",
                    "error",
                    "-xerror",
                    "-i",
                    str(movie),
                    "-map",
                    "0:v:0",
                    "-an",
                    "-fps_mode",
                    "passthrough",
                    "-pix_fmt",
                    "rgba",
                    "-threads",
                    "1",
                    "-start_number",
                    "0",
                    str(asset / "frames/%08d.png"),
                ]
            )
            prepared = _write_manifest(
                asset,
                size=size,
                fps=fps,
                provenance={
                    "engine": "manim-ce",
                    "request": record,
                    "execution": execution,
                    "runtime": probe["runtime"],
                    "resolved": resolved,
                    "tools": tools,
                },
            )
            if prepared.frame_count != count:
                raise ManimError("MANIM_ASSET", "PNG count differs from the rendered movie")
            job.check()
            destination = cache / "assets" / prepared.fingerprint
            destination.parent.mkdir(exist_ok=True)
            if destination.exists():
                try:
                    PreparedFrameSource(destination)
                except ValueError:
                    # Repair by publishing a fresh generation, never rewriting
                    # a directory that another reader may still reference.
                    destination = destination.with_name(destination.name + "-" + uuid.uuid4().hex[:12])
                    asset.rename(destination)
            else:
                asset.rename(destination)
            _atomic_json(
                cache / "requests" / (key + ".json"), {"request": record, "asset": str(destination.relative_to(cache))}
            )
            return PreparedFrameSource(destination)
