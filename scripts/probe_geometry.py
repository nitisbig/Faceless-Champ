"""Explicit native CAD/mesh and headless renderer feasibility probe."""

import argparse
import json
import platform
from pathlib import Path


def probe(*, cad=False, geometry=False, backend=None):
    from faceless_champ.integrations.dependencies import geometry_capabilities

    result = geometry_capabilities(cad=cad, geometry=geometry)
    result["platform"] = platform.platform()
    result["python"] = platform.python_version()
    if backend and result["ok"]:
        import numpy as np
        import pyvista as pv

        from faceless_champ import Canvas, Scene, Text, create_renderer, rendering_identity
        from facelesschamp_kit.engineering.clip import ArchChamp
        from faceless_champ.integrations.pyvista.model import ArchMesh
        from facelesschamp_kit.engineering.script import ArchScript
        from faceless_champ.integrations.build123d import mesh_from_cad

        if cad:
            import build123d as bd

            mesh = mesh_from_cad(bd.Box(10, 15, 20))
        else:
            mesh = ArchMesh.from_data(pv.Cube())
        view = ArchChamp(
            mesh, ArchScript().section("model", (0, 0, 0), cap=True), width=200, height=160, position=(105, 90)
        )
        node = Scene(Canvas(320, 180, "black")).add(view, Text("CAD", position=(270, 90), font_size=28)).wait(1)
        with create_renderer(backend, antialias=1) as renderer:
            first = np.asarray(renderer.frame(node, 0.75, (320, 180)))
            renderer.frame(node, 0.1, (320, 180))
            repeated = np.asarray(renderer.frame(node, 0.75, (320, 180)))
            result["renderer"] = {
                **rendering_identity(backend, renderer=renderer),
                "visible": bool(first[:, :200, :3].any()),
                "overlay_visible": bool(first[:, 230:, :3].any()),
                "repeatable": bool(np.array_equal(first, repeated)),
            }
        result["ok"] = result["ok"] and all(result["renderer"][k] for k in ("visible", "overlay_visible", "repeatable"))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cad", action="store_true")
    parser.add_argument("--geometry", action="store_true")
    parser.add_argument("--backend", choices=["pillow", "skia", "moderngl"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = probe(cad=args.cad, geometry=args.geometry, backend=args.backend)
    except Exception as exc:  # noqa: BLE001 - explicit diagnostic probes return structured failures
        result = {"ok": False, "error": str(exc)}
    encoded = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n")
    print(encoded)
    raise SystemExit(0 if result["ok"] else 1)
