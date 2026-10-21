"""Descriptor isolation, source clocks and owned resource lifecycle contracts."""

from dataclasses import dataclass
from importlib.util import find_spec

import pytest
from PIL import Image

from faceless_champ import Canvas, Group, Scene, Viewport, create_renderer
from faceless_champ._rendering.evaluate import evaluate_frame
from faceless_champ._rendering.resources import SourceSessions

EVENTS = []


@dataclass
class Source:
    color: str = "red"
    intrinsic_size: tuple = (20, 10)
    duration: float | None = 1
    requirements: tuple = ()
    fail: str = ""

    @property
    def fingerprint(self):
        return f"test:{self.color}:{self.fail}"

    def frame_key(self, time):
        return int(time * 10)

    def open(self, size):
        EVENTS.append(("open", size))
        color, fail = self.color, self.fail

        class Session:
            def frame(self, time):
                EVENTS.append(("frame", time))
                if fail == "frame":
                    raise RuntimeError("source failure")
                return Image.new("RGB" if fail == "mode" else "RGBA", size, color if time < 1 else "blue")

            def close(self):
                EVENTS.append(("close", size))

        return Session()


@pytest.mark.parametrize("backend", ["pillow", "skia", "moderngl"])
def test_source_sampling_isolation_keys_and_fixed_density(backend):
    if backend != "pillow" and find_spec(backend) is None:
        pytest.skip(f"{backend} extra is absent")
    EVENTS.clear()
    source = Source()
    view = Viewport(source, width=20, height=10, source_start=0.2, position=(30, 20))
    group = Group(view)
    scene = Scene(Canvas(60, 40)).wait(2).add(group)
    scene.play(group.animate.scale_to(1.2), run_time=2)
    source.color = "green"
    assert scene.time == 4
    frame = evaluate_frame(scene, 2.35)
    assert frame.geometry[1].source_time == pytest.approx(0.55)
    assert not EVENTS
    with create_renderer(backend, antialias=1) as renderer:
        renderer.validate(scene)
        assert not EVENTS
        for t, expected in ((2.35, (255, 0, 0)), (3.9, (0, 0, 255)), (2.35, (255, 0, 0))):
            result = renderer.frame(scene, t, (60, 40))
            assert result.getpixel((30, 20))[:3] == expected
    assert [e for e in EVENTS if e[0] == "open"] == [("open", (20, 10))]
    assert [e for e in EVENTS if e[0] == "close"] == [("close", (20, 10))]
    assert ("frame", pytest.approx(0.55)) in EVENTS
    assert ("frame", 1) in EVENTS


def test_byte_budget_equivalent_keys_caller_mutation_and_session_eviction():
    EVENTS.clear()
    owner = SourceSessions(cache_bytes=20 * 10 * 4, session_limit=1)
    source = Source()
    first = owner.frame(source, (20, 10), 0.21)
    first.putpixel((0, 0), (0, 0, 0, 0))
    assert owner.frame(source, (20, 10), 0.29).getpixel((0, 0)) == (255, 0, 0, 255)
    assert [e[1] for e in EVENTS if e[0] == "frame"] == [0.21]
    owner.frame(source, (40, 20), 0.3)
    assert len(owner.sessions) == 1 and owner.frames.bytes <= 800
    assert ("close", (20, 10)) in EVENTS
    owner.close()
    owner.close()
    assert not owner.sessions and not owner.frames.items and owner.frames.bytes == 0
    assert EVENTS.count(("close", (40, 20))) == 1


@pytest.mark.parametrize("failure,error", [("frame", RuntimeError), ("mode", ValueError)])
def test_failed_frame_closes_owned_session(failure, error):
    EVENTS.clear()
    owner = SourceSessions()
    with pytest.raises(error):
        owner.frame(Source(fail=failure), (20, 10), 0.5)
    assert not owner.sessions and not owner.frames.items
    assert EVENTS[-1] == ("close", (20, 10))


def test_failed_source_close_releases_other_sources_and_renderer_resources():
    from faceless_champ import PillowRenderer

    closed = []

    class Session:
        def __init__(self, name, fail=False):
            self.name, self.fail = name, fail

        def close(self):
            closed.append(self.name)
            if self.fail:
                raise RuntimeError("close failure")

    renderer = PillowRenderer(1)
    renderer._sources.sessions[1] = (Source(), Session("bad", True))
    renderer._sources.sessions[2] = (Source(), Session("good"))
    renderer._sources.sessions[3] = (Source(), Session("legacy"))
    renderer._images[1] = Image.new("RGBA", (1, 1))
    with pytest.raises(RuntimeError, match="close failure"):
        renderer.close()
    assert closed == ["bad", "good", "legacy"]
    assert not renderer._sources.sessions and not renderer._images
    renderer.close()


@pytest.mark.parametrize("kwargs", [{"width": 10}, {"height": 10}, {"source_start": -1}, {"source_start": 2}])
def test_invalid_viewport_options(kwargs):
    with pytest.raises(ValueError):
        Viewport(Source(), **kwargs)


@pytest.mark.parametrize(
    "kwargs", [{"intrinsic_size": (0, 10)}, {"duration": float("inf")}, {"duration": 0}, {"requirements": []}]
)
def test_invalid_source_descriptors(kwargs):
    with pytest.raises(ValueError):
        Viewport(Source(**kwargs))


def test_intrinsic_static_source_and_terminal_clock():
    source = Source(duration=None)
    view = Viewport(source)
    assert (view.width, view.height) == source.intrinsic_size
    assert view.source_time(100) == 100
    assert Viewport(Source(), source_start=1).source_time(100) == 1


@pytest.mark.parametrize("duration", ["1", True])
def test_invalid_duration_types_fail_before_sampling(duration):
    with pytest.raises(TypeError, match="duration"):
        Viewport(Source(duration=duration))


def test_legacy_adapter_keeps_domain_frame_identity():
    from facelesschamp_kit.diagrams import FlowChamp, FlowGraph, FlowNode

    from faceless_champ.sources import source_from_component

    legacy = FlowChamp(FlowGraph((FlowNode("one"),)), width=80, height=40)
    source = source_from_component(legacy)
    # A frame cache may outlive a descriptor/session. Do not reuse Python id()
    # values as fallback content identities after garbage collection.
    assert source.fingerprint != source_from_component(legacy).fingerprint
    assert source.frame_key(0.2) == legacy.frame_key(0.2)
    with create_renderer("pillow", antialias=1) as renderer:
        expected = renderer._sprite(legacy, legacy.state(), 1, 0.2)
    session = source.open((80, 40))
    try:
        assert session.frame(0.2).tobytes() == expected.tobytes()
    finally:
        session.close()
