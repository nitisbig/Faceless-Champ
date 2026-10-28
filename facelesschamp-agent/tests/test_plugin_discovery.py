import pytest
from faceless_champ import Capability, Plugin
from faceless_champ import plugins as registry

from facelesschamp_agent import CapabilityRegistry


@pytest.fixture
def demo_plugin(monkeypatch):
    monkeypatch.setattr(registry, "_registered", {})
    monkeypatch.setattr(registry, "_report", {})
    monkeypatch.setattr(registry, "_discovered", True)
    registry.register(
        Plugin(
            name="orbits",
            capabilities=(
                Capability(
                    "OrbitDiagram", "Animated planetary orbit diagram", "fc_orbits.OrbitDiagram", tags=("space",)
                ),
            ),
        )
    )


def test_plugin_capabilities_are_discoverable_and_checked(demo_plugin):
    catalog = CapabilityRegistry()
    top = catalog.recommend("planetary orbit", limit=3)
    assert top[0]["id"] == "plugin:orbits:OrbitDiagram" and top[0]["evidence"] == "plugin"
    assert catalog.describe("plugin:orbits:OrbitDiagram")["import_path"] == "fc_orbits.OrbitDiagram"
    assert catalog.check()["ok"]
    registry.unregister("orbits")
    with pytest.raises(Exception, match="Plugin is no longer registered"):
        catalog.check()
