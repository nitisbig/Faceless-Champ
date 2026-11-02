"""Chunked and parallel export: identical pixels and audio to a single pass, resume, failures and cancel."""

import array
import multiprocessing
import subprocess
from concurrent.futures import CancelledError
from itertools import pairwise

import pytest
from PIL import Image

from faceless_champ import Canvas, FunctionSource, Scene, render
from faceless_champ.audio import probe

pytestmark = [
    pytest.mark.skipif(
        "fork" not in multiprocessing.get_all_start_methods(), reason="parallel export needs the fork start method"
    ),
    # Earlier tests in the session leave helper threads behind; a fresh render forks from a single thread.
    pytest.mark.filterwarnings("ignore:This process .* is multi-threaded, use of fork:DeprecationWarning"),
]
LOSSLESS = {"width": 160, "height": 90, "fps": 10, "antialias": 1, "crf": 0, "preset": "ultrafast"}


def _scene(fn=None, audio=None, seconds=3.0):
    def ramp(t, size):  # a lambda-like closure: unpicklable sources must still work in forked workers
        value = round(255 * t / seconds)
        return Image.new("RGB", size, (value, 255 - value, (value * 7) % 256))

    scene = Scene(Canvas(160, 90, "#000000"))
    source = FunctionSource(fn or ramp, size=(160, 90), duration=seconds)
    scene.add(source.viewport(width=160, height=90, position=(80, 45)))
    if audio is not None:
        scene.add_audio(audio, start=0.5, fade_in=0.2)
    return scene.wait_until(seconds)


def _frames(path):
    return subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
        capture_output=True,
        check=True,
    ).stdout


def _pcm(path):
    data = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", "48000", "pipe:1"],
        capture_output=True,
        check=True,
    ).stdout
    samples = array.array("f")
    samples.frombytes(data)
    return samples


def test_parallel_chunks_match_a_single_pass(tmp_path, tone):
    serial = render(_scene(audio=tone), tmp_path / "serial.mp4", **LOSSLESS)
    parallel = render(_scene(audio=tone), tmp_path / "parallel.mp4", workers=2, chunk_frames=7, **LOSSLESS)
    assert _frames(parallel) == _frames(serial)
    a, b = _pcm(serial), _pcm(parallel)
    assert len(a) == len(b) and max(abs(x - y) for x, y in zip(a, b)) < 1e-4
    video = next(s for s in probe(parallel)["streams"] if s["codec_type"] == "video")
    assert video["color_space"] == "bt709" and int(video["nb_frames"]) == 30
    assert not list(tmp_path.glob("faceless-champ-*"))


def test_parallel_source_range_matches_serial_range(tmp_path):
    kwargs = {"start_time": 0.7, "end_time": 2.6, **LOSSLESS}
    serial = render(_scene(), tmp_path / "serial.mp4", **kwargs)
    parallel = render(_scene(), tmp_path / "parallel.mp4", workers=3, chunk_frames=4, **kwargs)
    assert _frames(parallel) == _frames(serial)


def test_chunk_dir_resumes_and_rerenders_only_missing_chunks(tmp_path):
    calls = []

    def counted(t, size):
        calls.append(t)
        return Image.new("RGB", size, (round(80 * t), 40, 200))

    chunks = tmp_path / "chunks"
    first = render(_scene(counted), tmp_path / "a.mp4", chunk_dir=chunks, chunk_frames=10, **LOSSLESS)
    files = sorted(chunks.glob("chunk-*.mp4"))
    assert len(files) == 3 and len(calls) == 30
    files[1].unlink()
    calls.clear()
    second = render(_scene(counted), tmp_path / "b.mp4", chunk_dir=chunks, chunk_frames=10, **LOSSLESS)
    assert len(calls) == 10 and min(calls) >= 1.0 - 1e-9 and max(calls) < 2.0
    assert _frames(second) == _frames(first)
    other = render(_scene(counted), tmp_path / "c.mp4", chunk_dir=chunks, chunk_frames=10, **{**LOSSLESS, "crf": 1})
    assert other.is_file() and len(list(chunks.glob("chunk-*.mp4"))) == 6  # new settings, new chunks


def test_worker_failure_is_reported_and_nothing_is_published(tmp_path):
    def broken(t, size):
        if t > 2.0:
            raise ValueError("source exploded at the end")
        return Image.new("RGB", size, "white")

    with pytest.raises(RuntimeError, match="source exploded at the end"):
        render(_scene(broken), tmp_path / "out.mp4", workers=2, chunk_frames=5, **LOSSLESS)
    assert not (tmp_path / "out.mp4").exists()
    assert not list(tmp_path.glob("faceless-champ-*"))


def test_parallel_progress_is_monotonic_and_complete(tmp_path):
    seen = []
    render(
        _scene(), tmp_path / "out.mp4", workers=2, chunk_frames=5, progress=lambda d, t: seen.append((d, t)), **LOSSLESS
    )
    assert seen[0] == (0, 30) and seen[-1] == (30, 30)
    assert all(a[0] <= b[0] for a, b in pairwise(seen))


def test_parallel_cancel_stops_workers(tmp_path):
    def slow(t, size):
        import time

        time.sleep(0.05)
        return Image.new("RGB", size, "gray")

    progress = []
    with pytest.raises(CancelledError):
        render(
            _scene(slow, seconds=20.0),
            tmp_path / "out.mp4",
            workers=2,
            chunk_frames=20,
            progress=lambda d, t: progress.append(d),
            cancel=lambda: bool(progress and progress[-1] > 0),
            **LOSSLESS,
        )
    assert not (tmp_path / "out.mp4").exists()
    assert not multiprocessing.active_children()


@pytest.mark.parametrize(
    ("options", "error", "match"),
    [
        ({"workers": 0}, ValueError, "workers must be a positive integer"),
        ({"chunk_frames": 0}, ValueError, "chunk_frames"),
        ({"workers": 2, "backend": "moderngl"}, ValueError, "pillow' or 'skia"),
    ],
)
def test_parallel_settings_are_validated(tmp_path, options, error, match):
    with pytest.raises(error, match=match):
        render(_scene(), tmp_path / "out.mp4", **{**LOSSLESS, **options})
