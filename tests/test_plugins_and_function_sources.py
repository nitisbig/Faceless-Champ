"""FunctionSource frames and the entry-point plugin registry."""

import json
import subprocess
import sys
from types import SimpleNamespace

import pytest
from PIL import Image

from faceless_champ import (
    Canvas,
    Capability,
    FunctionSource,
    Plugin,
    Scene,
    Text,
    Theme,
    Viewport,
    create_renderer,
    raster_source,
)
from faceless_champ import plugins as registry
from faceless_champ.easing import easing
from faceless_champ.theme import THEMES


@pytest.fixture(autouse=True)
def clean_registry(monkeypatch):
    monkeypatch.setattr(registry, "_registered", {})
    monkeypatch.setattr(registry, "_report", {})
    monkeypatch.setattr(registry, "_discovered", False)
    monkeypatch.setattr(registry, "_entry_points", list)
    monkeypatch.delenv(registry.ENV_VAR, raising=False)


# -- FunctionSource -------------------------------------------------------------


def _solid(t, size):
    return Image.new("RGB", size, (round(255 * min(t, 1)), 0, 0))


@pytest.mark.parametrize("backend", ["pillow", "skia"])
def test_function_source_renders_on_the_scene_clock(backend):
    pytest.importorskip("skia") if backend == "skia" else None
    source = FunctionSource(_solid, size=(32, 18), duration=1, fps=10)
    scene = Scene(Canvas(64, 36)).wait(0.5).add(Viewport(source, width=64, height=36, position=(32, 18))).wait(1.5)
    with create_renderer(backend, antialias=1) as renderer:
        renderer.validate(scene)
        assert renderer.frame(scene, 0.5, (64, 36)).getpixel((32, 18))[:3] == (0, 0, 0)
        assert renderer.frame(scene, 1.0, (64, 36)).getpixel((32, 18))[0] == pytest.approx(128, abs=2)
        assert renderer.frame(scene, 1.9, (64, 36)).getpixel((32, 18))[:3] == (255, 0, 0)  # clamped at duration


def test_numpy_frames_setup_state_keys_and_fingerprints():
    np = pytest.importorskip("numpy")
    closed = []

    class State:
        def __init__(self, size):
            self.grid = np.linspace(0, 1, size[0])[None, :, None] * np.ones((size[1], 1, 3))

        def close(self):
            closed.append(True)

    @raster_source(size=(20, 10), duration=2, fps=4, setup=State)
    def gradient(t, size, state):
        return state.grid * (t / 2)

    session = gradient.open((20, 10))
    frame = session.frame(1.1)
    assert frame.mode == "RGBA" and frame.size == (20, 10)
    assert frame.getpixel((19, 0))[0] == pytest.approx(round(255 * 0.5), abs=1)  # quantized to t=1.0
    session.close()
    assert closed == [True]
    assert gradient.frame_key(1.1) == gradient.frame_key(1.0) == 4
    assert FunctionSource(_solid).fingerprint == FunctionSource(_solid).fingerprint
    assert FunctionSource(_solid, key="v2").fingerprint != FunctionSource(_solid).fingerprint
    resized = FunctionSource(lambda t, size: Image.new("RGBA", (4, 4), "blue"), size=(8, 8)).open((8, 8)).frame(0)
    assert resized.size == (8, 8)
    with pytest.raises(ValueError, match="returned None"):
        FunctionSource(lambda t, size: None).open((4, 4)).frame(0)
    with pytest.raises(TypeError, match="HxW"):
        FunctionSource(lambda t, size: np.zeros((2, 2, 5))).open((2, 2)).frame(0)
    with pytest.raises(ValueError, match="size"):
        FunctionSource(_solid, size=(0, 10))
    view = gradient.viewport(width=40, height=20, position=(20, 10))
    assert isinstance(view, Viewport) and view.width == 40


# -- plugins --------------------------------------------------------------------

AURORA = Theme("aurora", THEMES["ocean"].colors)


def _plugin(**overrides):
    values = {
        "name": "demo",
        "version": "1.0",
        "themes": {"aurora": AURORA},
        "easings": {"twitch": lambda t: t**0.5},
        "components": {"Sparkle": Text},
        "sources": {"solid": lambda **options: FunctionSource(_solid, **options)},
        "capabilities": (Capability("Sparkle", "A twinkling accent", "demo.Sparkle", tags=("accent",)),),
    }
    values.update(overrides)
    return Plugin(**values)


def test_register_and_lookups_feed_theme_easing_and_sources():
    registry.register(_plugin())
    assert Theme.named("aurora") is AURORA
    assert easing("twitch")(0.25) == 0.5
    assert registry.component("Sparkle") is Text
    assert isinstance(registry.source("solid", size=(8, 8)), FunctionSource)
    records = {r["name"]: r for r in registry.capabilities()}
    assert records["Sparkle"]["use_when"] == "A twinkling accent"
    assert {"aurora", "twitch", "solid"} <= set(records)
    assert registry.names("themes") == ["aurora"]
    with pytest.raises(ValueError, match="aurora"):
        Theme.named("missing")
    with pytest.raises(registry.PluginError, match="No plugin component"):
        registry.component("Nope")


def test_conflicts_and_invalid_plugins_are_rejected():
    registry.register(_plugin())
    with pytest.raises(registry.PluginError, match="already registered"):
        registry.register(_plugin())
    with pytest.raises(registry.PluginError, match="already provided"):
        registry.register(_plugin(name="other", sources={}, easings={}, components={}))
    with pytest.raises(registry.PluginError, match="built-in"):
        registry.register(_plugin(name="bad", themes={"midnight": AURORA}, easings={}, components={}, sources={}))
    with pytest.raises(registry.PluginError, match="callable"):
        Plugin(name="x", easings={"y": 3})
    with pytest.raises(registry.PluginError, match="Theme"):
        Plugin(name="x", themes={"y": "dark"})


def test_entry_points_and_env_plugins_load_lazily_and_failures_are_reported(monkeypatch):
    good = SimpleNamespace(name="good", value="pkg:plugin", load=lambda: _plugin)
    broken = SimpleNamespace(name="broken", value="pkg:boom", load=lambda: 1 / 0)
    monkeypatch.setattr(registry, "_entry_points", lambda: [good, broken])
    module = type(sys)("fc_test_local_plugin")
    module.plugin = Plugin(name="local", easings={"local-ease": lambda t: t})
    monkeypatch.setitem(sys.modules, "fc_test_local_plugin", module)
    monkeypatch.setenv(registry.ENV_VAR, "fc_test_local_plugin:plugin, missing_module_xyz")
    assert set(registry.plugins()) == {"demo", "local"}
    report = {item["name"]: item for item in registry.plugin_report()}
    assert report["demo"]["status"] == "loaded" and report["demo"]["origin"].startswith("entry-point:good")
    failed = [item for item in report.values() if item["status"] == "failed"]
    assert len(failed) == 2 and any("ZeroDivisionError" in item["error"] for item in failed)
    assert easing("local-ease")(0.3) == 0.3


def test_plugins_cli_lists_nothing_without_plugins():
    result = subprocess.run(
        [sys.executable, "-m", "faceless_champ", "plugins"], capture_output=True, text=True, check=True
    )
    assert json.loads(result.stdout) == {"plugins": [], "capabilities": []}
