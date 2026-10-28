"""Agent-facing docs must stay executable: imports resolve and examples render cleanly."""

import importlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHEATSHEET = ROOT / "CHEATSHEET.md"
GUIDES = [ROOT / "llms.txt", ROOT / "facelesschamp-kit" / "llms.txt", ROOT / "facelesschamp-agent" / "llms.txt"]


def _blocks():
    text = CHEATSHEET.read_text()
    blocks = []
    for match in re.finditer(r"(<!-- skip -->\s*)?```python\n(.*?)```", text, re.DOTALL):
        if not match.group(1):
            title = text[: match.start()].rsplit("\n## ", 1)[-1].splitlines()[0]
            blocks.append(pytest.param(match.group(2), id=title[:40]))
    return blocks


@pytest.mark.parametrize("code", _blocks())
def test_cheatsheet_examples_render_and_pass_design_audit(code, tmp_path, monkeypatch):
    pytest.importorskip("facelesschamp_kit")
    from faceless_champ import PillowRenderer, design_audit

    monkeypatch.chdir(tmp_path)
    namespace = {"__name__": "cheatsheet"}
    exec(compile(code, "CHEATSHEET.md", "exec"), namespace)  # noqa: S102 - tested docs
    scene = namespace["scene"]
    with PillowRenderer(1) as renderer:
        renderer.validate(scene)
        for fraction in (0.35, 0.8):
            renderer.frame(scene, scene.duration * fraction, (480, 270))
    report = design_audit(scene, samples=6)
    assert not report.findings, str(report)


def _imports():
    pairs = []
    for guide in GUIDES:
        if not guide.is_file():
            continue
        text = " ".join(guide.read_text().split())
        for names, module in re.findall(r"Import ((?:[A-Za-z_]\w*,? (?:and )?)+)from ([a-z_][\w.]*\w)", text):
            for name in re.findall(r"[A-Za-z_]\w*", names):
                if name != "and":
                    pairs.append(pytest.param(module, name, id=f"{guide.parent.name}:{module}.{name}"))
    return pairs


@pytest.mark.parametrize(("module", "name"), _imports())
def test_documented_imports_resolve(module, name):
    try:
        imported = importlib.import_module(module)
    except ImportError as exc:  # optional extras (web, maps...) may be absent
        pytest.skip(f"optional dependency for {module}: {exc}")
    try:
        getattr(imported, name)
    except ImportError as exc:
        pytest.skip(f"optional dependency for {module}.{name}: {exc}")
    except AttributeError as exc:
        pytest.fail(f"{module}.{name} is documented but not importable: {exc}")


def test_agents_md_points_to_existing_files():
    text = (ROOT / "AGENTS.md").read_text()
    for target in re.findall(r"\]\(([^)#]+)", text):
        if not target.startswith("http"):
            assert (ROOT / target).exists(), target


def _guide_blocks():
    text = (ROOT / "docs" / "plugins.md").read_text()
    return [
        pytest.param(code, id=f"plugins-{index}")
        for index, code in enumerate(re.findall(r"```python\n(.*?)```", text, re.DOTALL))
    ]


@pytest.mark.parametrize("code", _guide_blocks())
def test_plugin_guide_examples_run(code, monkeypatch):
    from faceless_champ import FunctionSource, PillowRenderer, Theme
    from faceless_champ import plugins as registry

    monkeypatch.setattr(registry, "_registered", {})
    monkeypatch.setattr(registry, "_report", {})
    monkeypatch.setattr(registry, "_discovered", True)
    namespace = {"__name__": "plugin_guide"}
    try:
        exec(compile(code, "docs/plugins.md", "exec"), namespace)  # noqa: S102 - tested docs
    except ImportError as exc:
        pytest.skip(f"optional dependency: {exc}")
    if "scene" in namespace:
        scene = namespace["scene"]
        with PillowRenderer(1) as renderer:
            renderer.validate(scene)
            try:
                renderer.frame(scene, scene.duration * 0.6, (320, 180))
            except ImportError as exc:
                pytest.skip(f"optional dependency: {exc}")
    if "plugin" in namespace:
        registry.register(namespace["plugin"])
        assert Theme.named("studio").radius == 12
        source = registry.source("stripes", size=(64, 36), duration=1)
        assert isinstance(source, FunctionSource) and source.open((64, 36)).frame(0.5).size == (64, 36)
