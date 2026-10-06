"""Build local wheel and sdist using the active interpreter's setuptools."""

import os
from pathlib import Path

from setuptools.build_meta import build_sdist, build_wheel

root = Path(__file__).resolve().parents[1]
os.chdir(root)
(root / "dist").mkdir(exist_ok=True)
print(build_sdist(str(root / "dist")))
print(build_wheel(str(root / "dist")))
