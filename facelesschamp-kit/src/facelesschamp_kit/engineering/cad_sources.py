"""Bounded engineering preset and registered STEP source authoring."""

from faceless_champ.integrations.build123d import TessellationOptions, parts_from_cad, read_step
from faceless_champ.integrations.pyvista.model import ArchDataError


def _validate_source(source):
    """Validate a bounded structured source, without importing native engines."""
    from .models import validate_preset

    if not isinstance(source, dict) or set(source) - {"preset", "params", "asset", "tessellation", "source_units"}:
        raise ArchDataError("cad", "expected preset/params or a registered STEP asset")
    if ("preset" in source) == ("asset" in source):
        raise ArchDataError("cad", "use exactly one preset or asset")
    if "asset" in source:
        if not isinstance(source["asset"], str) or not source["asset"].strip() or "params" in source:
            raise ArchDataError("cad.asset", "expected a registered asset ID without parameters")
        if source.get("source_units", "mm") != "mm":
            raise ArchDataError("source_units", "STEP import normalizes coordinates to mm")
    else:
        validate_preset(source["preset"], source.get("params", {}))
        if source.get("source_units", "mm") != "mm":
            raise ArchDataError("source_units", "built-in presets use mm")
    try:
        TessellationOptions(**source.get("tessellation", {}))
    except TypeError as exc:
        raise ArchDataError("tessellation", str(exc)) from exc


def _parts_from_source(source, units, resolver):
    from .models import CAD_PRESETS, validate_preset

    _validate_source(source)
    provenance = {}
    if "asset" in source:
        if resolver is None:
            raise ArchDataError("cad.asset", "provide cad_resolver for registered STEP assets")
        path = resolver(source["asset"])
        shape = read_step(path)
        provenance = shape._faceless_provenance
    else:
        shape = CAD_PRESETS[source["preset"]](**validate_preset(source["preset"], source.get("params", {})))
    return parts_from_cad(
        shape, options=TessellationOptions(**source.get("tessellation", {})), target_units=units, provenance=provenance
    )
