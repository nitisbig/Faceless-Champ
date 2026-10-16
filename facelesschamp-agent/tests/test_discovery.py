import json
import os
import subprocess
import sys

import pytest

from facelesschamp_agent import AgentError, CapabilityRegistry


def test_recipe_preview_metadata_only_advertises_existing_resources(tmp_path, monkeypatch):
    from facelesschamp_kit.recipes import recipe_specs

    import facelesschamp_agent.registry as registry_module

    monkeypatch.setattr(registry_module, "files", lambda package: tmp_path)
    registry = CapabilityRegistry()
    for spec in recipe_specs():
        record = registry.describe(f"recipe:{spec.id}")
        assert "thumbnail" not in record and "motion_preview" not in record
    spec = recipe_specs()[0]
    poster = tmp_path / "resources/previews" / f"{spec.id}.png"
    poster.parent.mkdir(parents=True)
    poster.touch()
    record = CapabilityRegistry().describe(f"recipe:{spec.id}")
    assert record["thumbnail"] == str(poster)
    assert "motion_preview" not in record


def test_catalog_is_identical_in_fresh_api_and_cli_processes():
    environment = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
    suffix = (
        "; import json; registry = CapabilityRegistry(); "
        "print(json.dumps({'manifest': registry.manifest(), 'entries': registry.search()}))"
    )
    api = subprocess.run(
        [sys.executable, "-c", "from facelesschamp_agent import CapabilityRegistry" + suffix],
        capture_output=True,
        text=True,
        env=environment,
        check=True,
    )
    cli = subprocess.run(
        [
            sys.executable,
            "-c",
            "from facelesschamp_agent.cli import main; "
            "from facelesschamp_agent.registry import CapabilityRegistry" + suffix,
        ],
        capture_output=True,
        text=True,
        env=environment,
        check=True,
    )
    api_records, cli_records = json.loads(api.stdout), json.loads(cli.stdout)
    assert api_records["manifest"] == cli_records["manifest"]
    assert api_records["entries"] == cli_records["entries"]


def test_compact_bounded_search_preserves_matches_and_reduces_payload():
    registry = CapabilityRegistry()
    full = registry.search("animation", limit=12)
    compact = registry.search("animation", limit=12, compact=True)
    assert len(full) == 12
    assert [entry["id"] for entry in full] == [entry["id"] for entry in compact]
    assert len(json.dumps(compact)) < len(json.dumps(full)) * 0.5
    assert all("parameters" not in entry and "excerpt" not in entry for entry in compact)
    assert registry.describe(compact[0]["id"])["parameters"] == full[0]["parameters"]
    assert registry.search(limit=0) == []


@pytest.mark.parametrize("limit", [-1, True, 1.5, "2"])
def test_search_rejects_invalid_limits(limit):
    with pytest.raises(AgentError, match="CAPABILITY_LIMIT"):
        CapabilityRegistry().search(limit=limit)


def test_recommendations_are_bounded_ranked_and_explain_selection():
    registry = CapabilityRegistry()
    entries = registry.recommend("router icon", limit=3, kind="asset")
    assert len(entries) == 3
    assert entries[0]["id"].endswith("networking/router_icon.png")
    assert [entry["score"] for entry in entries] == sorted((entry["score"] for entry in entries), reverse=True)
    assert all(entry["reasons"] and entry["preparation"] == "none" for entry in entries)
    assert all("dependencies" in entry and entry["evidence"] == "installed-resource" for entry in entries)
    assert registry.recommend("zyxwvunotarealcapability", limit=2) == []
    with pytest.raises(AgentError, match="CAPABILITY_LIMIT"):
        registry.recommend("flow", limit=None)


def test_new_public_root_exports_are_live_without_registry_allowlist(monkeypatch):
    import faceless_champ

    def FutureAmbient(strength=0.25):
        """Future premium ambient lighting available from the installed API."""

    monkeypatch.setattr(faceless_champ, "FutureAmbient", FutureAmbient, raising=False)
    monkeypatch.setattr(faceless_champ, "__all__", [*faceless_champ.__all__, "FutureAmbient"])
    registry = CapabilityRegistry()
    result = registry.describe("faceless_champ.FutureAmbient")
    assert result["parameters"][0]["name"] == "strength"
    assert result["parameters"][0]["default"] == "0.25"
    assert result["excerpt"] == FutureAmbient.__doc__
    assert result["source"]["kind"] == "installed-api"
    assert registry.check()["ok"]


def test_future_callable_and_object_defaults_keep_catalog_identity_stable(monkeypatch):
    import faceless_champ

    def implementation():
        def easing(progress):
            return progress

        sentinel = object()

        def FutureMotion(rate_func=easing, strategy=sentinel, label="<literal at 0x123>"):
            """A future public animation with runtime default objects."""

        return FutureMotion

    monkeypatch.setattr(faceless_champ, "__all__", [*faceless_champ.__all__, "FutureMotion"])
    first_motion = implementation()
    second_motion = implementation()
    assert first_motion.__defaults__[0] is not second_motion.__defaults__[0]
    assert repr(first_motion.__defaults__[1]) != repr(second_motion.__defaults__[1])
    monkeypatch.setattr(faceless_champ, "FutureMotion", first_motion, raising=False)
    first = CapabilityRegistry()
    monkeypatch.setattr(faceless_champ, "FutureMotion", second_motion)
    second = CapabilityRegistry()
    parameters = first.describe("faceless_champ.FutureMotion")["parameters"]
    assert parameters[0]["default"].endswith(".implementation.<locals>.easing")
    assert parameters[1]["default"] == "<object object>"
    assert parameters[2]["default"] == repr("<literal at 0x123>")
    assert first.manifest()["fingerprint"] == second.manifest()["fingerprint"]


def test_check_does_not_accept_a_missing_declared_export(monkeypatch):
    import faceless_champ

    monkeypatch.setattr(faceless_champ, "__all__", [*faceless_champ.__all__, "MissingFutureExport"])
    with pytest.raises(AgentError, match="CAPABILITY_ID"):
        CapabilityRegistry().check()


def test_new_public_submodules_are_discovered_without_executing_optional_code(tmp_path, monkeypatch):
    import faceless_champ

    monkeypatch.setattr(faceless_champ, "__path__", [*faceless_champ.__path__, str(tmp_path)])
    source = tmp_path / "future_transition.py"
    source.write_text(
        "from unavailable_future_renderer import Renderer\n"
        'raise RuntimeError("Discovery must never execute this module")\n'
        '__all__ = ["FutureTransition"]\n'
        "class FutureTransition:\n"
        '    """Premium transition with an optional renderer."""\n'
        '    def __init__(self, duration=0.4, *, curve="smooth"):\n'
        "        pass\n"
    )
    (tmp_path / "_private.py").write_text("class PrivateVisual: pass\n")
    samples = tmp_path / "sample_assets"
    samples.mkdir()
    (samples / "unsafe.py").write_text(
        'raise RuntimeError("Project code must not execute")\nclass SampleVisual: pass\n'
    )
    registry = CapabilityRegistry()
    entry = registry.describe("faceless_champ.future_transition.FutureTransition")
    assert entry["source"]["kind"] == "installed-source"
    assert entry["category"] == "transition"
    assert [parameter["name"] for parameter in entry["parameters"]] == ["duration", "curve"]
    assert entry["parameters"][1]["kind"] == "KEYWORD_ONLY"
    assert "module import: unavailable_future_renderer (availability unverified)" in entry["dependencies"]
    ids = {record["id"] for record in registry.search()}
    assert "faceless_champ._private.PrivateVisual" not in ids
    assert "faceless_champ.sample_assets.unsafe.SampleVisual" not in ids
    assert "faceless_champ.future_transition" not in sys.modules
    assert registry.check()["ok"]
    assert "faceless_champ.future_transition" not in sys.modules


def test_new_assets_and_designs_refresh_catalog_without_code_execution(tmp_path, monkeypatch):
    import facelesschamp_kit

    monkeypatch.setattr(facelesschamp_kit, "__path__", [*facelesschamp_kit.__path__, str(tmp_path)])
    before = CapabilityRegistry().manifest()
    assets = tmp_path / "new_bundle" / "icons"
    assets.mkdir(parents=True)
    (assets / "nebula.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    (tmp_path / "new_bundle" / "Premium.otf").write_bytes(b"example future font resource")
    (tmp_path / "future_style.py").write_text(
        'raise RuntimeError("Do not import a discovered style module")\n'
        'FUTURE_DESIGNS = {"studio": object()}\n'
        "class FutureDesign:\n"
        "    @classmethod\n"
        "    def named(cls, name):\n"
        '        if name == "premium":\n'
        "            return cls()\n"
        "        raise ValueError(name)\n"
    )
    registry = CapabilityRegistry()
    icon = registry.describe("asset:facelesschamp_kit:new_bundle/icons/nebula.svg")
    assert icon["asset_type"] == "icon"
    assert registry.describe("asset:facelesschamp_kit:new_bundle/Premium.otf")["asset_type"] == "font"
    assert registry.describe("design:facelesschamp_kit.future_style.FUTURE_DESIGNS:studio")["selector"] == "mapping"
    preset = registry.describe("design:facelesschamp_kit.future_style.FutureDesign:premium")
    assert preset["selector"] == "named"
    assert "FutureDesign.named('premium')" in preset["example"]
    after = registry.manifest()
    assert before["fingerprint"] != after["fingerprint"]
    assert before["count"] < after["count"]
    assert after == CapabilityRegistry().manifest()
    assert registry.check()["ok"]


def test_cached_source_ast_invalidates_when_public_contract_changes(tmp_path, monkeypatch):
    import faceless_champ

    monkeypatch.setattr(faceless_champ, "__path__", [*faceless_champ.__path__, str(tmp_path)])
    path = tmp_path / "future_motion.py"
    path.write_text('def premium_motion(duration=1):\n    """Premium motion."""\n')
    first = CapabilityRegistry()
    assert first.describe("faceless_champ.future_motion.premium_motion")["parameters"][0]["default"] == "1"
    path.write_text('def premium_motion(duration=12, damping=0.8):\n    """Updated premium motion."""\n')
    second = CapabilityRegistry()
    entry = second.describe("faceless_champ.future_motion.premium_motion")
    assert entry["parameters"][0]["default"] == "12"
    assert len(entry["parameters"]) == 2
    assert first.manifest()["fingerprint"] != second.manifest()["fingerprint"]


def test_describe_returns_independent_records_and_guidance_provenance():
    registry = CapabilityRegistry()
    entry = registry.describe("faceless_champ.FadeIn")
    assert "installed signature and excerpt are authoritative" in entry["guide_source"]
    entry["parameters"].clear()
    assert registry.describe("faceless_champ.FadeIn")["parameters"]


def test_installed_design_font_and_icon_catalog_is_available():
    registry = CapabilityRegistry()
    assert registry.search("clean-flow", kind="design")
    assert registry.search("font", kind="asset")
    assert registry.search("icon", kind="asset")
    manifest = registry.manifest()
    assert manifest["count"] == sum(manifest["counts"].values())
    assert manifest["schema_version"] == 1
    assert len(manifest["fingerprint"]) == 64
