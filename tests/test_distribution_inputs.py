"""Required demonstration inputs must survive a clean source distribution."""

import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "name",
    [
        "facelesschamp-kit/src/facelesschamp_kit/sample_assets/voiceover.wav",
        "examples/programming/hello_world/audio.mp3",
    ],
)
def test_required_narration_is_not_ignored(name):
    root = Path(__file__).resolve().parents[1]
    if not (root / ".git").exists() or not shutil.which("git"):
        pytest.skip("Source-checkout ignore policy requires Git")
    assert (root / name).is_file()
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "--", name], cwd=root, capture_output=True, text=True, check=False
    )
    assert result.returncode == 1, result.stdout or result.stderr


def test_reference_narration_checksum():
    example = Path(__file__).resolve().parents[1] / "examples/programming/hello_world/audio.mp3"
    assert hashlib.sha256(example.read_bytes()).hexdigest() == (
        "cd5764b59b939230a4112116f793013e476029d1511c873bf452ebdff9533002"
    )
