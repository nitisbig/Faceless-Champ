import os
import sys
from pathlib import Path

import pytest

if not os.environ.get("FC_INSTALLED_ONLY"):
    root = Path(__file__).resolve().parents[2]
    for path in (root / "src", root / "facelesschamp-kit/src", root / "facelesschamp-agent/src"):
        sys.path.insert(0, str(path))

from facelesschamp_agent.project import AgentProject, init_project


@pytest.fixture
def project(tmp_path):
    root = init_project(tmp_path / "video")
    config = root / "facelesschamp.toml"
    config.write_text(
        config.read_text()
        .replace("[profiles.final]", "[profiles.final]\nwidth=320\nheight=180")
        .replace("fps = 30", "fps = 10")
        .replace("antialias = 2", "antialias = 1")
    )
    return AgentProject(root)
