"""Standalone worker: needs only stdlib and Manim in the selected interpreter.

Do not import this file from a facade. No Core/Kit installation is required in
the worker environment. Requests and results are files, never log-line parsing.
"""

import configparser
import importlib.metadata
import json
import os
import platform
import random
import re
import runpy
import shutil
import subprocess
import sys
import traceback
from pathlib import Path


def tool(name):
    path = shutil.which(name)
    if path is None:
        return None
    result = subprocess.run([path, "--version"], capture_output=True, timeout=10, check=False)
    return {"path": path, "version": (result.stdout + result.stderr).decode(errors="replace")[:2000]}


def configure(manim, options):
    from manim._config.utils import ManimConfig

    parser = configparser.ConfigParser(interpolation=None)
    parser.read(Path(manim.__file__).parent / "_config/default.cfg")
    manim.config.update(ManimConfig().digest_parser(parser))
    values = {
        "quality": options["quality"],
        "renderer": "cairo",
        "preview": False,
        "live_preview": False,
        "show_in_file_browser": False,
        "enable_gui": False,
        "disable_caching": True,
        "format": "mov",
        "video_codec": "qtrle",
        "pixel_format": "argb",
        "video_encoder_options": {"threads": "1"},
        "max_inflight_encoders": 1,
        "encoder_queue_size": 1,
        "progress_bar": "none",
        "seed": options["seed"],
        "background_color": options["background"] or "#000000",
        "background_opacity": 0.0 if options["background"] is None else 1.0,
    }
    manim.config.update(values)
    if options["width"] is not None:
        manim.config.pixel_width = options["width"]
        manim.config.pixel_height = options["height"]
    if options["fps"] is not None:
        manim.config.frame_rate = options["fps"]
    manim.config.frame_width = manim.config.frame_height * manim.config.pixel_width / manim.config.pixel_height
    return {
        "size": [manim.config.pixel_width, manim.config.pixel_height],
        "fps": float(manim.config.frame_rate),
        "background": options["background"],
        "seed": options["seed"],
    }


def execute(mode, request):
    version = importlib.metadata.version("manim")
    if not re.fullmatch(r"0\.22\.\d+", version):
        return {"error": "MANIM_VERSION", "message": f"Expected Manim Community >=0.22,<0.23; found {version}"}
    import manim
    import numpy

    resolved = configure(manim, request["options"])
    if mode == "probe":
        import cairo
        import manimpango

        return {
            "resolved": resolved,
            "runtime": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "packages": dict(sorted((d.metadata["Name"], d.version) for d in importlib.metadata.distributions())),
                "cairo": cairo.cairo_version_string(),
                "pango": getattr(manimpango, "pango_version", lambda: "unknown")(),
                "latex": tool("latex"),
                "dvisvgm": tool("dvisvgm"),
            },
        }
    root = Path(request["source_root"])
    source = root / request["spec"]["source"]
    random.seed(request["options"]["seed"])
    numpy.random.seed(request["options"]["seed"])
    sys.path.insert(0, str(root))
    os.chdir(root)
    namespace = runpy.run_path(str(source), run_name="__faceless_manim_scene__")
    cls = namespace.get(request["spec"]["scene_name"])
    if not isinstance(cls, type) or not issubclass(cls, manim.Scene):
        return {"error": "MANIM_SCENE", "message": "scene_name must identify a Manim Scene subclass"}
    # Module-level config changes cannot override the transport/render contract.
    configure(manim, request["options"])
    with manim.tempconfig(
        {
            "media_dir": request["media_dir"],
            "input_file": str(source),
            "output_file": "scene",
        }
    ):
        scene = cls()
        scene.faceless_parameters = request["spec"]["parameters"]
        scene.render()
        return {"path": str(scene.renderer.file_writer.final_file_path), "resolved": resolved}


def main():
    mode, input_path, output_path = sys.argv[1:]
    try:
        result = execute(mode, json.loads(Path(input_path).read_text()))
    except importlib.metadata.PackageNotFoundError:
        result = {"error": "MANIM_DEPENDENCY", "message": "Install faceless-champ[manim] or select a Manim environment"}
    except FileNotFoundError as exc:
        traceback.print_exc()
        executable = Path(exc.filename or "").name
        result = {
            "error": "MANIM_DEPENDENCY" if executable in {"latex", "dvisvgm"} else "MANIM_RENDER",
            "message": f"Scene requires {executable}; install LaTeX/dvisvgm in the selected environment"
            if executable in {"latex", "dvisvgm"}
            else str(exc),
        }
    except Exception as exc:  # noqa: BLE001 -- cross-process diagnostic boundary
        traceback.print_exc()
        result = {
            "error": "MANIM_RENDER" if mode == "render" else "MANIM_DEPENDENCY",
            "message": str(exc) or type(exc).__name__,
        }
    Path(output_path).write_text(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
