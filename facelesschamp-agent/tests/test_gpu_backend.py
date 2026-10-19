import json

import pytest

from facelesschamp_agent import CapabilityRegistry
from facelesschamp_agent.errors import AgentError


def test_gpu_contracts_discovered_offline():
    registry = CapabilityRegistry()
    record = registry.describe("faceless_champ.ModernGLRenderer")
    assert record["family"] == "gpu"
    assert any("gpu" in item for item in record["dependencies"])
    assert registry.describe("faceless_champ.Bloom")["family"] == "gpu"


def test_auto_provenance_resolves_and_backend_review_stays_strict(project):
    config = project.root / "facelesschamp.toml"
    config.write_text(
        config.read_text()
        .replace("[profiles.preview]", '[profiles.preview]\nbackend="auto"\nwidth=160\nheight=90')
        .replace("[profiles.final]", '[profiles.final]\nbackend="auto"')
    )
    record = project.frame(1)
    assert record["rendering"]["backend"] != "auto"
    assert record["rendering"]["requested_backend"] == "auto"
    project.review(
        {
            "fingerprint": record["fingerprint"],
            "reviewer": "test",
            "kind": "visual",
            "status": "unverified",
            "evidence_artifacts": [record["artifacts"][0]["id"]],
        }
    )


def test_gpu_review_rejects_changed_shader_pipeline(project, monkeypatch):
    # Exercise provenance without needing a particular hardware GPU in the Agent suite.
    record = project.frame(1)
    expected = {
        "backend": "moderngl",
        "shader_hash": "new",
        "driver": "same",
        "renderer": "same",
        "color_pipeline": "linear-v1",
    }
    state = project.state / "records" / f"{record['id']}.json"
    data = json.loads(state.read_text())
    data["rendering"] = expected | {"shader_hash": "old"}
    state.write_text(json.dumps(data))
    monkeypatch.setattr(project, "_final_rendering", lambda compiled: expected)
    with pytest.raises(AgentError, match="REVIEW_BACKEND"):
        project.review(
            {
                "fingerprint": record["fingerprint"],
                "reviewer": "test",
                "kind": "visual",
                "status": "unverified",
                "evidence_artifacts": [record["artifacts"][0]["id"]],
            }
        )
