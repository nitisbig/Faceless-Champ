"""Bounded checkpoint execution and atomic, browser-free prepared assets."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

from faceless_champ.components import finite

from facelesschamp_kit.playground.model import PlaygroundError, PlaygroundScript, json_copy, valid_canvas_value


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _versions(web):
    versions = {"python": platform.python_version(), "executable": sys.executable, "driver": 2}
    for package in (
        ("faceless-champ", "facelesschamp-kit", "playwright") if web else ("faceless-champ", "facelesschamp-kit")
    ):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "unavailable"
    if web:
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as engine:
                executable = Path(engine.chromium.executable_path)
                versions["chromium"] = str(executable)
                if executable.is_file():
                    stat = executable.stat()
                    versions["chromium_stat"] = [stat.st_size, stat.st_mtime_ns]
        except ImportError as exc:
            raise PlaygroundError(
                "PLAYGROUND_DEPENDENCY", "Install facelesschamp-kit[web] and Chromium explicitly"
            ) from exc
    versions["implementation"] = hashlib.sha256(
        b"".join(p.read_bytes() for p in sorted(Path(__file__).parent.glob("*.py")))
    ).hexdigest()
    return versions


def _kill(process):
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif process.poll() is None:
        process.kill()
    process.wait()


def _python(checkpoint, directory, timeout, output_limit):
    root = directory / "source"
    out, err, emission = (directory / name for name in ("stdout", "stderr", "emissions"))
    emission.touch()
    env = os.environ.copy()
    # Import the same installed/source core as the preparing process, also under editable installs.
    env["PYTHONPATH"] = os.pathsep.join([str(Path(__file__).resolve().parents[2]), str(root)])
    env.update(
        FACELESS_PLAYGROUND_EMIT=str(emission),
        FACELESS_PLAYGROUND_INPUTS=json.dumps(checkpoint.inputs),
        FACELESS_PLAYGROUND_LIMIT=str(output_limit),
        PYTHONHASHSEED="0",
        PYTHONDONTWRITEBYTECODE="1",
    )
    with out.open("wb") as stdout, err.open("wb") as stderr:
        runner = (
            "import os, runpy, sys; "
            "import resource; resource.setrlimit(resource.RLIMIT_FSIZE, (int(sys.argv[2]), int(sys.argv[2]))); "
            if os.name == "posix"
            else "import os, runpy, sys; "
        )
        runner += "sys.path.insert(0, os.path.dirname(sys.argv[1])); runpy.run_path(sys.argv[1], run_name='__main__')"
        process = subprocess.Popen(
            [sys.executable, "-u", "-c", runner, str(root / checkpoint.entrypoint), str(output_limit)],
            cwd=root,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            start_new_session=os.name == "posix",
        )
        start = time.monotonic()
        try:
            while True:
                if sum(p.stat().st_size for p in (out, err, emission)) >= output_limit:
                    raise PlaygroundError("PLAYGROUND_OUTPUT_LIMIT", "Checkpoint output limit exceeded")
                if process.poll() is not None:
                    break
                if time.monotonic() - start > timeout:
                    raise PlaygroundError("PLAYGROUND_TIMEOUT", f"Checkpoint exceeded {timeout:g}s timeout")
                time.sleep(0.01)
        finally:
            _kill(process)  # Also terminate descendants that outlive a successful parent.
    values, events = {}, []
    try:
        for line in emission.read_text(encoding="utf-8").splitlines():
            record = json_copy(json.loads(line))
            if set(record) != {"kind", "name", "value"} or not isinstance(record["name"], str) or not record["name"]:
                raise ValueError("Expected kind, nonempty name, and value")
            if record["kind"] == "value":
                if record["name"] in values:
                    raise ValueError(f"Duplicate emitted value {record['name']!r}")
                values[record["name"]] = record["value"]
            elif record["kind"] == "event":
                events.append({"name": record["name"], "value": record["value"]})
            else:
                raise ValueError("Unknown emission kind")
    except (ValueError, TypeError, KeyError) as exc:
        raise PlaygroundError("PLAYGROUND_EMISSION", f"Invalid emitted JSON: {exc}") from exc
    return {
        "values": values,
        "events": events,
        "stdout": out.read_text(errors="replace"),
        "stderr": err.read_text(errors="replace"),
        "exit_code": process.returncode,
    }


def validate_result(script, checkpoint, result):
    failed = result["exit_code"] != 0
    if failed != checkpoint.expected_failure:
        message = "Expected failure, but checkpoint succeeded" if checkpoint.expected_failure else result["stderr"]
        raise PlaygroundError("PLAYGROUND_EXECUTION", message or "Checkpoint failed", checkpoint=checkpoint.id)
    if failed:
        return
    items = {i.id: i for i in script.items}
    from PIL import ImageColor

    for binding in script.bindings:
        if binding.key not in result["values"]:
            raise PlaygroundError(
                "PLAYGROUND_BINDING", f"Missing emitted value {binding.key!r}", checkpoint=checkpoint.id
            )
        value = result["values"][binding.key]
        kind = items[binding.target].kind
        valid = True
        if binding.property in {"label", "color"}:
            valid = isinstance(value, str)
            if valid and binding.property == "color":
                try:
                    ImageColor.getcolor(value, "RGBA")
                except ValueError:
                    valid = False
        else:
            valid = valid_canvas_value(kind, value)
        if not valid:
            raise PlaygroundError(
                "PLAYGROUND_BINDING",
                f"Invalid {binding.property} for {kind} {binding.target!r}",
                checkpoint=checkpoint.id,
            )
    for event in script.events:
        if event.checkpoint == checkpoint.id and event.cell is not None:
            item = items[event.target]
            binding = next((b for b in script.bindings if b.target == item.id and b.property == "value"), None)
            data = result["values"][binding.key] if binding else item.value
            rows = [data] if item.kind == "vector" else data
            row, column = event.cell
            if rows is None or row >= len(rows) or column >= len(rows[row]):
                raise PlaygroundError(
                    "PLAYGROUND_BINDING", "Event cell is outside tensor bounds", checkpoint=checkpoint.id
                )
    names = [e["name"] for e in result["events"]]
    for binding in script.events:
        if binding.checkpoint == checkpoint.id and names.count(binding.event) != 1:
            raise PlaygroundError(
                "PLAYGROUND_BINDING", f"Event {binding.event!r} must be emitted exactly once", checkpoint=checkpoint.id
            )
    scheduled = [e.event for e in sorted(script.events, key=lambda e: e.at) if e.checkpoint == checkpoint.id]
    indices = [names.index(name) for name in scheduled]
    if indices != sorted(indices):
        raise PlaygroundError(
            "PLAYGROUND_BINDING", "Authored event order differs from execution", checkpoint=checkpoint.id
        )


class PreparedPlayground:
    """Verified immutable manifest plus lazily loaded captured browser frames."""

    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        try:
            record = json.loads((self.directory / "manifest.json").read_text())
            if record["schema"] != 1 or _digest(record["identity"]) != record["fingerprint"]:
                raise ValueError("Unsupported schema or invalid fingerprint")
            self._script = PlaygroundScript.from_record(record["identity"]["script"])
            inventory = {
                str(p.relative_to(self.directory))
                for p in self.directory.rglob("*")
                if p.is_file() and p != self.directory / "manifest.json"
            }
            if inventory != set(record["assets"]):
                raise ValueError("Incomplete asset inventory")
            for name, digest in record["assets"].items():
                path = (self.directory / name).resolve()
                if not path.is_relative_to(self.directory) or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                    raise ValueError(f"Missing or corrupt asset {name}")
            if _digest(record["results"]) != record["results_digest"]:
                raise ValueError("Corrupt results")
            if len(record["results"]) != len(self._script.checkpoints):
                raise ValueError("Missing checkpoint results")
            for c, result in zip(self._script.checkpoints, record["results"]):
                validate_result(self._script, c, result)
                if c.runtime == "web":
                    from facelesschamp_kit.web import WebCapture

                    capture_path = (self.directory / result["capture"]).resolve()
                    if not capture_path.is_relative_to(self.directory):
                        raise ValueError("Capture escapes prepared directory")
                    web = WebCapture(capture_path)
                    if len(web.frames) != web.count:
                        raise ValueError("Incomplete web capture")
            self._manifest = json_copy(record)
            self._frozen = True
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            raise PlaygroundError("PLAYGROUND_ASSET", f"Invalid prepared playground; prepare again: {exc}") from exc

    def __setattr__(self, name, value):
        if getattr(self, "_frozen", False):
            raise AttributeError("PreparedPlayground is immutable; prepare a new generation")
        object.__setattr__(self, name, value)

    @property
    def script(self):
        return PlaygroundScript.from_record(self._script.record())

    @property
    def fingerprint(self):
        return self._manifest["fingerprint"]

    @property
    def results(self):
        return json_copy(self._manifest["results"])

    def __deepcopy__(self, memo):
        # Source, results, and frames are immutable for the lifetime of the asset.
        return self


def prepare_playground(
    script, *, cache_dir=".playground-cache", timeout=10, output_limit=1_000_000, fps=15, refresh=False
):
    if not isinstance(script, PlaygroundScript):
        raise TypeError("Expected PlaygroundScript")
    script = PlaygroundScript.from_record(script.record())
    timeout, fps = finite(timeout, "timeout", 0.001), finite(fps, "fps", 0.001)
    if type(output_limit) is not int or output_limit < 1:
        raise PlaygroundError("PLAYGROUND_SPEC", "output_limit must be a positive integer")
    identity = {
        "script": script.record(),
        "timeout": timeout,
        "output_limit": output_limit,
        "fps": fps,
        "runtime": _versions(script.mode == "web"),
    }
    key = _digest(identity)
    cache = Path(cache_dir).resolve()
    cache.mkdir(parents=True, exist_ok=True)
    destination = cache / key
    latest = cache / (key + ".latest.json")
    if latest.exists() and not refresh:
        try:
            resolved = (cache / json.loads(latest.read_text())["asset"]).resolve()
            if not resolved.is_relative_to(cache):
                raise ValueError("Cache reference escapes its directory")
            return PreparedPlayground(resolved)
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            raise PlaygroundError("PLAYGROUND_ASSET", f"Invalid cache reference; prepare with refresh: {exc}") from exc
    if destination.exists() and not refresh:
        return PreparedPlayground(destination)
    # Refresh publishes a new immutable generation; existing readers keep their asset.
    if destination.exists():
        destination = cache / (key + "-" + uuid.uuid4().hex[:12])
    with tempfile.TemporaryDirectory(prefix=".preparing-", dir=cache) as staging:
        staging = Path(staging)
        results = []
        for index, checkpoint in enumerate(script.checkpoints):
            try:
                with tempfile.TemporaryDirectory(prefix="checkpoint-") as work:
                    work = Path(work)
                    root = work / "source"
                    root.mkdir()
                    for name, source in checkpoint.files.items():
                        path = root / name
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(source, encoding="utf-8", newline="")
                    if checkpoint.runtime == "python":
                        result = _python(checkpoint, work, timeout, output_limit)
                    else:
                        from facelesschamp_kit.web import WebCapture

                        (work / "request.json").write_text(
                            json.dumps(
                                {
                                    "script": script.record(),
                                    "index": index,
                                    "fps": fps,
                                    "timeout": timeout,
                                    "output_limit": output_limit,
                                }
                            )
                        )
                        env = os.environ.copy()
                        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
                        with (work / "browser.log").open("wb") as log:
                            worker = subprocess.Popen(
                                [sys.executable, "-m", "facelesschamp_kit.playground.web_worker", str(work)],
                                stdout=log,
                                stderr=log,
                                env=env,
                                cwd=work,
                                start_new_session=os.name == "posix",
                            )
                            try:
                                started = time.monotonic()
                                while worker.poll() is None:
                                    if time.monotonic() - started > timeout:
                                        raise PlaygroundError("PLAYGROUND_TIMEOUT", "Browser checkpoint timed out")
                                    if (work / "browser.log").stat().st_size > output_limit:
                                        raise PlaygroundError(
                                            "PLAYGROUND_OUTPUT_LIMIT", "Browser log exceeds output limit"
                                        )
                                    time.sleep(0.02)
                            finally:
                                _kill(worker)
                        if worker.returncode:
                            raise PlaygroundError(
                                "PLAYGROUND_BROWSER", (work / "browser.log").read_text(errors="replace")[-8000:]
                            )
                        response = json.loads((work / "response.json").read_text())
                        capture = WebCapture(response["capture"])
                        target = f"web-{index}"
                        shutil.copytree(capture.directory, staging / target)
                        errors = capture.manifest.get("errors", [])
                        result = {
                            "values": {},
                            "events": [],
                            "stdout": "\n".join(capture.manifest.get("console", [])),
                            "stderr": "\n".join(errors),
                            "exit_code": 1 if errors else 0,
                            "capture": target,
                        }
                    validate_result(script, checkpoint, result)
                    results.append(result)
            except PlaygroundError as exc:
                exc.scope.setdefault("checkpoint", checkpoint.id)
                raise
            except (OSError, ValueError, RuntimeError) as exc:
                raise PlaygroundError("PLAYGROUND_PREPARE", str(exc), checkpoint=checkpoint.id) from exc
        assets = {
            str(p.relative_to(staging)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in staging.rglob("*")
            if p.is_file()
        }
        record = {
            "schema": 1,
            "identity": identity,
            "fingerprint": key,
            "results": results,
            "results_digest": _digest(results),
            "assets": assets,
        }
        (staging / "manifest.json").write_text(json.dumps(record, sort_keys=True, allow_nan=False))
        PreparedPlayground(staging)
        try:
            staging.rename(destination)
        except OSError:
            if not destination.is_dir():
                raise
    prepared = PreparedPlayground(destination)
    fd, name = tempfile.mkstemp(prefix=".latest-", dir=cache)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump({"asset": destination.name}, stream)
        os.replace(name, latest)
    finally:
        Path(name).unlink(missing_ok=True)
    return prepared
