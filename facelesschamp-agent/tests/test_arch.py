import pyvista as pv

from facelesschamp_agent import CapabilityRegistry, VideoPlan


def test_arch_discovery_and_bundled_contract():
    registry = CapabilityRegistry()
    entry = registry.describe("facelesschamp_kit.blocks.ArchCanvas")
    assert entry["named_targets"] == ["model"]
    assert entry["family"] == "arch" and "guide" in entry
    assert registry.describe("recipe:arch-design")["fields"] == ["design"] or registry.describe("recipe:arch-design")[
        "fields"
    ] == ("design",)
    assert registry.search("point cloud")


def test_mesh_plan_and_evidence_fingerprint(project):
    data = pv.Cube()
    data.save(project.root / "assets/body.vtp")
    raw = project.plan.model_dump(mode="json")
    raw["brief"]["assets"] = [{"id": "body", "path": "assets/body.vtp", "kind": "mesh"}]
    raw["scenes"][0].update(
        recipe="arch-design",
        content={"design": {"parts": [{"id": "body", "mesh": {"asset": "body"}}]}},
        required_assets=["body"],
        key_events=[],
    )
    project.plan_path.write_text(VideoPlan.model_validate(raw).model_dump_json())
    first = project.validate()["fingerprint"]
    data.points[:] *= 1.5
    data.save(project.root / "assets/body.vtp")
    assert project.validate()["fingerprint"] != first
