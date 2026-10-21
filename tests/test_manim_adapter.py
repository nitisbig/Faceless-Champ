"""Engine-free orchestration tests using tiny real lossless movie fixtures."""

import subprocess
import sys
import time
from concurrent.futures import CancelledError
from pathlib import Path

import pytest
from PIL import Image

from faceless_champ.integrations.manim import (
    ManimError,
    ManimRenderOptions,
    ManimSceneSpec,
    load_manim,
    manim_capabilities,
    prepare_manim,
)
from faceless_champ.integrations.manim.prepare import _Job


@pytest.fixture
def scene_spec(tmp_path):
    source = tmp_path / "lesson.py"
    source.write_text("# trusted fixture v1\n")
    (tmp_path / "helper.py").write_text("value = 1\n")
    return ManimSceneSpec(source, "Lesson", inputs=("helper.py",), parameters={"value": 1})


@pytest.fixture
def fake_engine(monkeypatch):
    calls = []

    def worker(job, mode, request, python):
        assert Path(python).is_absolute()
        calls.append(mode)
        options = request["options"]
        resolved = {"size": [options["width"] or 20, options["height"] or 10], "fps": options["fps"] or 4}
        if mode == "probe":
            return {"resolved": resolved, "runtime": {"test_engine": 1, "packages": {"manim": "0.22.0"}}}
        root = Path(request["source_root"])
        assert (root / "helper.py").is_file()
        directory = job.work / "input"
        directory.mkdir()
        for index in range(4):
            color = (40 + 20 * index, 120, 220, 128 if options["background"] is None else 255)
            Image.new("RGBA", tuple(resolved["size"]), color).save(directory / f"{index:08d}.png")
        output = job.work / "scene.mov"
        job.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-framerate",
                str(resolved["fps"]),
                "-i",
                str(directory / "%08d.png"),
                "-an",
                "-c:v",
                "qtrle",
                "-pix_fmt",
                "argb",
                "-threads",
                "1",
                str(output),
            ]
        )
        return {"path": str(output), "resolved": resolved}

    monkeypatch.setattr(_Job, "worker", worker)
    return calls


def test_prepare_warm_cache_engine_free_load_and_refresh(scene_spec, fake_engine, tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    source = prepare_manim(scene_spec, cache_dir=cache)
    assert source.frame_count == 4 and source.duration == 1
    assert prepare_manim(scene_spec, cache_dir=cache).fingerprint == source.fingerprint
    assert fake_engine == ["probe", "render", "probe"]
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("Playback started a subprocess"))
    assert load_manim(scene_spec, cache_dir=cache).fingerprint == source.fingerprint
    session = source.open((20, 10))
    assert session.frame(0).getpixel((10, 5)) == (40, 120, 220, 128)
    session.close()


def test_inputs_settings_and_refresh_identity(scene_spec, fake_engine, tmp_path):
    cache = tmp_path / "cache"
    old = prepare_manim(scene_spec, cache_dir=cache)
    new = prepare_manim(scene_spec, cache_dir=cache, options=ManimRenderOptions(background="white"))
    assert old.fingerprint != new.fingerprint
    same = prepare_manim(scene_spec, cache_dir=cache, refresh=True)
    assert same.fingerprint == old.fingerprint
    (scene_spec.source_root / "helper.py").write_text("value = 2\n")
    with pytest.raises(ManimError) as error:
        load_manim(scene_spec, cache_dir=cache)
    assert error.value.code == "MANIM_UNPREPARED"


def test_failed_refresh_preserves_published_reference(scene_spec, fake_engine, tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    old = prepare_manim(scene_spec, cache_dir=cache)

    def fail(*args, **kwargs):
        raise ManimError("MANIM_RENDER", "fixture failure")

    monkeypatch.setattr(_Job, "worker", fail)
    with pytest.raises(ManimError, match="fixture failure"):
        prepare_manim(scene_spec, cache_dir=cache, refresh=True)
    assert load_manim(scene_spec, cache_dir=cache).fingerprint == old.fingerprint
    assert not list(cache.glob(".preparing-*"))


@pytest.mark.parametrize("failure", ["timeout", "cancel", "output"])
def test_supervision_bounds_stalled_children_and_logs(tmp_path, failure):
    log = tmp_path / "job.log"
    started = time.monotonic()
    job = _Job(
        tmp_path,
        log,
        0.25 if failure == "timeout" else 5,
        4096,
        (lambda: time.monotonic() - started > 0.2) if failure == "cancel" else None,
    )
    script = (
        "import time; time.sleep(30)"
        if failure != "output"
        else "print('x'*8192,flush=True); import time; time.sleep(30)"
    )
    with pytest.raises((ManimError, CancelledError)) as error:
        job.run([sys.executable, "-u", "-c", script])
    assert time.monotonic() - started < 4
    if failure != "cancel":
        assert error.value.code == ("MANIM_TIMEOUT" if failure == "timeout" else "MANIM_OUTPUT_LIMIT")


def test_capabilities_and_all_imports_never_load_manim_or_execute():
    code = """
import importlib.abc, subprocess, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'manim','numpy','cairo','manimpango','av'}:
            raise AssertionError('native import: '+fullname)
sys.meta_path.insert(0, Block())
subprocess.Popen = lambda *a, **k: (_ for _ in ()).throw(AssertionError('subprocess'))
import faceless_champ as core
for name in core.__all__: getattr(core,name)
from faceless_champ.integrations.manim import manim_capabilities
assert not manim_capabilities()['probed']
from facelesschamp_agent import CapabilityRegistry
assert CapabilityRegistry().search('symbolic transformation')
"""
    result = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert not manim_capabilities()["probed"]


def test_input_containment_and_parameter_snapshot(tmp_path):
    source = tmp_path / "scene.py"
    params = {"values": [1, 2]}
    spec = ManimSceneSpec(source, "Scene", parameters=params)
    params["values"].append(3)
    assert spec.parameters == {"values": [1, 2]}
    for inputs in (("../escape.py",), (str(source),)):
        with pytest.raises(ValueError):
            ManimSceneSpec(source, "Scene", inputs=inputs)
    for options in ({"fps": 0}, {"width": 10}, {"seed": -1}):
        with pytest.raises(ValueError):
            ManimRenderOptions(**options)


def test_selected_virtual_environment_executable_keeps_its_symlink(tmp_path):
    from faceless_champ.integrations.manim.model import request_record

    source = tmp_path / "source.py"
    source.write_text("# input")
    python = tmp_path / "venv/bin/python"
    python.parent.mkdir(parents=True)
    python.symlink_to(sys.executable)
    _, record = request_record(ManimSceneSpec(source, "Lesson"), ManimRenderOptions(), python)
    assert record["python"] == str(python)


def test_corrupt_cache_refresh_publishes_a_repaired_generation(scene_spec, fake_engine, tmp_path):
    cache = tmp_path / "cache"
    old = prepare_manim(scene_spec, cache_dir=cache)
    (old.directory / "frames/00000000.png").write_bytes(b"corrupt")
    with pytest.raises(ManimError) as error:
        prepare_manim(scene_spec, cache_dir=cache)
    assert error.value.code == "MANIM_ASSET"
    repaired = prepare_manim(scene_spec, cache_dir=cache, refresh=True)
    assert repaired.fingerprint == old.fingerprint and repaired.directory != old.directory
    assert load_manim(scene_spec, cache_dir=cache).directory == repaired.directory


def test_concurrent_requests_render_once(scene_spec, fake_engine, tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=2) as workers:
        jobs = [workers.submit(prepare_manim, scene_spec, cache_dir=tmp_path / "cache") for _ in range(2)]
        sources = [job.result(timeout=30) for job in jobs]
    assert sources[0].fingerprint == sources[1].fingerprint
    assert fake_engine.count("render") == 1


def test_explicit_probe_uses_an_absolute_interpreter(fake_engine):
    result = manim_capabilities(python=".venv/bin/python", probe=True)
    assert result["probed"] and result["ok"]
    assert result["resolved"]["size"] == [20, 10]


@pytest.mark.skipif(sys.platform != "linux", reason="Linux process-state observation")
def test_timeout_stops_native_descendants(tmp_path):
    child_script = "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)"
    script = (
        "import pathlib,subprocess,sys,time; "
        f"child=subprocess.Popen([sys.executable,'-c',{child_script!r}]); "
        "pathlib.Path('child.pid').write_text(str(child.pid)); time.sleep(30)"
    )
    job = _Job(tmp_path, tmp_path / "job.log", 0.5, 4096, None)
    with pytest.raises(ManimError) as error:
        job.run([sys.executable, "-c", script])
    assert error.value.code == "MANIM_TIMEOUT"
    pid = int((tmp_path / "child.pid").read_text())
    state = Path(f"/proc/{pid}/stat")
    deadline = time.monotonic() + 2
    while state.exists() and state.read_text().split()[2] != "Z" and time.monotonic() < deadline:
        time.sleep(0.02)
    assert not state.exists() or state.read_text().split()[2] == "Z"
