"""Static public discovery metadata. No optional engine is imported or probed."""

import importlib
from importlib.metadata import PackageNotFoundError, metadata


def public_capabilities():
    """Describe installed public surfaces; availability never implies device support."""
    result = {"schema_version": 1, "packages": {}, "backends": ["pillow", "skia", "moderngl", "auto"]}
    for name, distribution in (("faceless_champ", "faceless-champ"), ("facelesschamp_kit", "facelesschamp-kit")):
        package = importlib.import_module(name)
        try:
            extras = sorted(metadata(distribution).get_all("Provides-Extra") or [])
        except PackageNotFoundError:
            extras = []
        result["packages"][name] = {
            "distribution": distribution,
            "version": package.__version__,
            "exports": sorted(package.__all__),
            "extras": extras,
        }
    return result
