import json

import pytest

from facelesschamp_agent.errors import AgentError
from facelesschamp_agent.models import DesignSpec


def configure(project, preview, final):
    config = project.root / "facelesschamp.toml"
    config.write_text(
        config.read_text()
        .replace("[profiles.preview]", f'[profiles.preview]\nbackend="{preview}"\nwidth=320\nheight=180')
        .replace("[profiles.final]", f'[profiles.final]\nbackend="{final}"')
    )


def test_agent_native_design_and_frame_preview_provenance(project):
    pytest.importorskip("skia")
    configure(project, "skia", "skia")
    plan = json.loads(project.plan_path.read_text())
    plan["design"].update(text_engine="skia", surface_mode="vector")
    project.plan_path.write_text(json.dumps(plan))
    assert DesignSpec.model_json_schema()["properties"]["text_engine"]["enum"] == ["pillow", "skia"]
    project.validate()
    frame = project.frame(1)
    preview = project.preview(start=0, end=0.2)
    assert frame["rendering"]["backend"] == preview["rendering"]["backend"] == "skia"
    assert "skia-python" in preview["rendering"]["versions"]


def test_cross_backend_review_is_rejected_and_configuration_invalidates_evidence(project):
    pytest.importorskip("skia")
    configure(project, "pillow", "skia")
    record = project.frame(1)
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
    config = project.root / "facelesschamp.toml"
    config.write_text(config.read_text().replace('backend="pillow"', 'backend="skia"'))
    assert project.validate()["fingerprint"] != record["fingerprint"]
