"""Major M3 contracts: shared execution, capability selection and bounded cleanup."""

import subprocess
import sys
import threading
from concurrent.futures import CancelledError
from types import SimpleNamespace

import pytest

from faceless_champ import Canvas, CircleMask, Group, Rectangle, Scene, Text, create_renderer, render
from faceless_champ._rendering.process import ProcessIO


@pytest.fixture(params=["pillow", "skia", "moderngl"])
def backend(request):
    if request.param != "pillow":
        pytest.importorskip(request.param)
    with create_renderer(request.param, antialias=1) as renderer:
        yield renderer


def test_shared_visibility_opacity_masks_seek_and_track_evaluation(backend, monkeypatch):
    from faceless_champ._rendering.plan import NodeSpec

    red, blue = [Rectangle(width=50, height=40, fill=c, stroke=None, position=(40, 30)) for c in ("red", "blue")]
    group = Group(red, blue, opacity=0.5, mask=CircleMask(15))
    hidden = Rectangle(width=80, height=60, fill="lime", opacity=0, position=(40, 30))
    node = Scene(Canvas(80, 60, "#00000000")).add(group, hidden).wait(0.5).remove(group).wait(0.5)
    backend.validate(node)
    calls, original = [], NodeSpec.state_at

    def counted(self, time):
        calls.append((self.id, time))
        return original(self, time)

    monkeypatch.setattr(NodeSpec, "state_at", counted)
    first = backend.frame(node, 0.2, (80, 60))
    assert first.getpixel((40, 30))[3] == 192
    assert first.getpixel((0, 0)) == (0, 0, 0, 0)
    first_bytes = first.tobytes()
    first.paste("white", (0, 0, 80, 60))
    assert backend.frame(node, 0.2, (80, 60)).tobytes() == first_bytes
    assert len(calls) == len(node.entries)  # Once per scene/time, even across cache signatures and paint.
    assert backend.frame(node, 0.8, (80, 60)).getbbox() is None
    assert backend.frame(node, 0.2, (80, 60)).tobytes() == first_bytes
    backend.close()
    backend.close()
    with pytest.raises(RuntimeError, match="closed"):
        backend.frame(node, 0.2, (80, 60))


def test_auto_resolution_is_once_and_unsupported_fallback_is_never_allocated(monkeypatch):
    import faceless_champ.renderer as factory
    from faceless_champ.backends._auto import AutoRenderer

    created, closed = [], []
    node = Scene().add(Text("Native", text_engine="skia")).wait(1)

    def make(name, **kwargs):
        created.append(name)
        return SimpleNamespace(
            identity={"backend": name, "device": "software" if name == "moderngl" else "cpu"},
            validate=lambda node: None,
            close=lambda: closed.append(name),
        )

    monkeypatch.setattr(factory, "create_renderer", make)
    with AutoRenderer() as renderer:
        renderer.validate(node)
        renderer.validate(node)
        assert renderer.identity["backend"] == "skia"
        assert created == ["moderngl", "skia"]
        assert closed == ["moderngl"]
    assert closed == ["moderngl", "skia"]

    def missing(name, **kwargs):
        created.append(name)
        raise ImportError("missing native engine")

    created.clear()
    monkeypatch.setattr(factory, "create_renderer", missing)
    with AutoRenderer() as renderer, pytest.raises(RuntimeError, match="native_text"):
        renderer.validate(node)
    assert created == ["moderngl", "skia"]


def test_raster_service_bounds_decoded_and_retained_images_without_changing_pixels():
    from PIL import Image as PILImage

    from faceless_champ import Image
    from faceless_champ._rendering.raster import RasterPainter

    with RasterPainter(raster_cache_mb=0) as painter:
        for color in ("red", "blue", "red"):
            c = Image.from_source(PILImage.new("RGBA", (20, 10), color), width=20, height=10)
            result = painter.sprite(c, c.state(), 1, 0)
            assert result.getpixel((10, 5)) == PILImage.new("RGBA", (1, 1), color).getpixel((0, 0))
            assert not painter._images and not painter._sprites


def test_skia_partial_initialization_closes_owned_raster(monkeypatch):
    pytest.importorskip("skia")
    from faceless_champ.backends import skia

    closed = []
    monkeypatch.setattr(skia, "PillowRasterAdapter", lambda *a: SimpleNamespace(close=lambda: closed.append("raster")))

    def fail():
        raise RuntimeError("text initialization failed")

    monkeypatch.setattr(skia, "TextSession", fail)
    with pytest.raises(RuntimeError, match="text initialization failed"):
        skia.SkiaRenderer()
    assert closed == ["raster"]


def test_gl_partial_initialization_and_close_failure_release_context(monkeypatch):
    gl = pytest.importorskip("moderngl")
    from faceless_champ.backends import moderngl
    from faceless_champ.backends._gl import device

    closed = []
    monkeypatch.setattr(
        gl, "create_standalone_context", lambda **k: SimpleNamespace(release=lambda: closed.append("ctx"))
    )

    def fail(*a):
        raise RuntimeError("shader initialization failed")

    monkeypatch.setattr(device, "GLDevice", fail)
    with pytest.raises(RuntimeError, match="shader initialization failed"):
        moderngl.ModernGLRenderer()
    assert closed == ["ctx"]

    renderer = moderngl.ModernGLRenderer.__new__(moderngl.ModernGLRenderer)
    renderer._closed, renderer._thread = False, threading.get_ident()
    renderer.frames = SimpleNamespace(clear=lambda: closed.append("frames"))
    renderer.ctx = SimpleNamespace(release=lambda: closed.append("ctx"))
    renderer.device = SimpleNamespace(close=lambda: closed.append("device"))
    renderer.raster = SimpleNamespace(close=fail)
    with pytest.raises(RuntimeError, match="shader initialization failed"):
        renderer.close()
    renderer.close()
    assert closed == ["ctx", "device", "ctx", "frames"]


@pytest.mark.parametrize("operation", ["write", "read", "finish"])
def test_stalled_child_io_is_bounded_reaped_and_joined(operation):
    # A real child parks without reading or writing its data pipes: no timed sleeps.
    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import sys, threading; sys.stderr.write('R'); sys.stderr.flush(); threading.Event().wait()",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert child.stderr.read(1) == b"R"
    owner = ProcessIO(child, timeout=0.03)
    action = {
        "write": lambda: child.stdin.write(b"x" * 1024**2),
        "read": lambda: child.stdout.read(1),
        "finish": child.wait,
    }[operation]
    try:
        with owner, pytest.raises(TimeoutError, match="exceeded"):
            owner.call(action)
        assert child.poll() is not None
        assert not owner._thread.is_alive()
        assert child.stdin.closed and child.stdout.closed
    finally:
        owner.close()
        child.stderr.close()


def test_arch_worker_timeout_closes_isolation_process(monkeypatch):
    from faceless_champ.integrations.pyvista import _worker as _arch_worker
    from faceless_champ.integrations.pyvista.model import ArchDataError

    original, children = subprocess.Popen, []

    def stalled(*args, **kwargs):
        child = original([sys.executable, "-c", "import sys; sys.stdin.buffer.read()"], **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(_arch_worker.subprocess, "Popen", stalled)
    worker = _arch_worker.ArchWorker(timeout=0.03)
    component = SimpleNamespace(fingerprint="test", width=4, height=4, source_start=0, font=None)
    try:
        with pytest.raises(ArchDataError, match="timed out"):
            worker.sprite(component, {}, 1, 0)
        assert children[0].poll() is not None
        assert not worker.pipe._thread.is_alive()
    finally:
        worker.close()


@pytest.mark.parametrize("failure", ["stall", "cancel"])
def test_encoder_stall_and_cancellation_preserve_existing_output_and_caller_renderer(tmp_path, monkeypatch, failure):
    from faceless_champ import export

    original, children = subprocess.Popen, []

    def stalled(*args, **kwargs):
        child = original(
            [
                sys.executable,
                "-c",
                "import sys, threading; sys.stderr.write('R'); sys.stderr.flush(); threading.Event().wait()",
            ],
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
        )
        assert child.stderr.read(1) == b"R"
        children.append(child)
        return child

    monkeypatch.setattr(export.subprocess, "Popen", stalled)
    output = tmp_path / "preserved.mp4"
    output.write_bytes(b"existing output")
    node = Scene(Canvas(160, 90)).wait(1)
    polls = []

    def cancel():
        polls.append(1)
        return len(polls) >= 4  # Trigger while the pipe call is waiting.

    try:
        with create_renderer("pillow", antialias=1) as renderer:
            with pytest.raises(TimeoutError if failure == "stall" else CancelledError):
                render(
                    node,
                    output,
                    renderer=renderer,
                    overwrite=True,
                    width=160,
                    height=90,
                    fps=1,
                    encoder_timeout=0.03 if failure == "stall" else 1,
                    cancel=cancel if failure == "cancel" else None,
                )
            assert renderer.frame(node, 0, (160, 90)).size == (160, 90)
        assert output.read_bytes() == b"existing output"
        assert list(tmp_path.iterdir()) == [output]
        assert children[0].poll() is not None
    finally:
        for child in children:
            child.stderr.close()
