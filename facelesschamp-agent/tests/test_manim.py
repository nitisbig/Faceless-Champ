"""Literal engine metadata augments discovery, not the scene-routing policy."""

import json
import subprocess
import sys

from facelesschamp_agent import CapabilityRegistry


def test_math_contracts_have_phase_requirements_and_semantic_handles():
    registry = CapabilityRegistry()
    equation = registry.describe("facelesschamp_kit.EquationTransform")
    assert equation["family"] == "manim" and equation["preparation"] == "explicit"
    assert "LaTeX" in equation["preparation_requirements"]
    assert equation["playback_requirements"] == ["Pillow"]
    assert equation["output_formats"] == ["rgba-png-sequence"]
    assert "Equation/Write" in equation["avoid"]
    block = registry.describe("facelesschamp_kit.blocks.ManimCanvas")
    assert block["named_targets"] == ["animation"]
    compact = registry.search("symbolic transformation", limit=20, compact=True)
    assert any(item.get("family") == "manim" and item["playback_requirements"] == ["Pillow"] for item in compact)
    assert registry.describe("faceless_champ.Equation")["name"] == "Equation"


def test_fresh_discovery_never_imports_or_probes_manim():
    code = """
import importlib.abc, json, subprocess, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'manim','cairo','manimpango','av'}: raise AssertionError(fullname)
sys.meta_path.insert(0,Block())
subprocess.Popen=lambda *a,**k: (_ for _ in ()).throw(AssertionError('probe'))
from facelesschamp_agent import CapabilityRegistry
r=CapabilityRegistry(); print(json.dumps(r.describe('facelesschamp_kit.EquationTransform')))
"""
    result = subprocess.run([sys.executable, "-B", "-c", code], check=True, capture_output=True, text=True)
    assert json.loads(result.stdout)["preparation"] == "explicit"
