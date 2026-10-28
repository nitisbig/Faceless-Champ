"""One-line command-line runner for scene scripts.

End any scene file with::

    if __name__ == "__main__":
        run(build)          # a Scene, a Scene subclass, or a zero-argument factory

Then::

    python scene.py                     # full render -> output/<name>.mp4
    python scene.py --preview           # first 8 s, 540p, 15 fps
    python scene.py --preview 4 --start 12
    python scene.py --frame 3.5 9       # PNG stills
    python scene.py --storyboard 6      # 6 evenly spaced stills + storyboard.png
    python scene.py --range 10 20 --quality high
    python scene.py --audit             # design audit (text size, contrast, clutter)

Outputs are overwritten unless --keep is given. The final stdout line is JSON
listing the written files, so agents can parse it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

QUALITY = {"low": 540, "medium": 720, "high": 1080, "4k": 2160}


def _resolve(target):
    from .timeline import Renderable

    node = target
    if isinstance(node, type) or callable(node) and not isinstance(node, Renderable):
        node = node()
    if not isinstance(node, Renderable):
        raise TypeError("run() needs a Scene/composition, a Scene subclass, or a factory returning one")
    return node


def _size(canvas, short_side):
    ratio = short_side / min(canvas.width, canvas.height)
    return tuple(max(2, round(v * ratio / 2) * 2) for v in (canvas.width, canvas.height))


def build_parser(prog=None):
    parser = argparse.ArgumentParser(prog=prog, description="Render a Faceless Champ scene.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preview", nargs="?", type=float, const=8.0, metavar="SECONDS", help="short low-res excerpt")
    mode.add_argument("--frame", nargs="+", type=float, metavar="T", help="save PNG stills at times")
    mode.add_argument("--storyboard", nargs="?", type=int, const=6, metavar="N", help="N evenly spaced stills")
    mode.add_argument("--range", nargs=2, type=float, metavar=("START", "END"), help="render a time range")
    mode.add_argument("--audit", action="store_true", help="report design problems at sampled times")
    parser.add_argument("--start", type=float, default=0.0, help="preview start time (default 0)")
    parser.add_argument("--quality", choices=tuple(QUALITY), help="low=540p medium=720p high=1080p 4k=2160p")
    parser.add_argument("--fps", type=float, help="frames per second (preview default 15, else 30)")
    parser.add_argument("--backend", default="pillow", choices=("pillow", "skia", "moderngl", "auto"))
    parser.add_argument("--output", type=Path, help="output file (video/PNG) or directory (storyboard)")
    parser.add_argument("--name", help="base name for outputs (default: script name)")
    parser.add_argument("--keep", action="store_true", help="refuse to overwrite existing outputs")
    return parser


def run(target, *, argv=None, name: str | None = None, output_dir: str | Path = "output") -> int:
    """Parse command-line flags and render ``target``. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    script = Path(sys.argv[0]).stem if sys.argv and sys.argv[0] not in {"", "-c"} else "scene"
    name = args.name or name or script
    out_dir = Path(output_dir)
    overwrite = not args.keep
    try:
        node = _resolve(target)
        written = _execute(node, args, name, out_dir, overwrite)
    except (ValueError, TypeError, OSError, RuntimeError) as exc:
        print(f"faceless-champ: {exc}", file=sys.stderr)
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps({"ok": True, **written}))
    return 0


def _execute(node, args, name, out_dir, overwrite):
    from .export import ExportSettings, render
    from .preview import render_storyboard, save_frame
    from .progress import ExportProgress
    from .renderer import create_renderer

    canvas = node.canvas
    duration = node.duration
    preview_like = args.preview is not None or args.frame or args.storyboard
    quality = args.quality or ("low" if preview_like else "high")
    size = _size(canvas, QUALITY[quality])

    if args.audit:
        from .audit import design_audit

        report = design_audit(node)
        for finding in report.findings:
            print(f"[{finding.severity}] t={finding.time:.2f}s {finding.message}", file=sys.stderr)
        return {"audit": report.to_dict()}

    if args.frame:
        outputs = []
        with create_renderer(args.backend, antialias=2) as renderer:
            for time in args.frame:
                if not 0 <= time <= duration:
                    raise ValueError(f"frame time {time} is outside 0..{duration:.2f}s")
                path = args.output if (args.output and len(args.frame) == 1) else out_dir / f"{name}_{time:07.3f}s.png"
                path.parent.mkdir(parents=True, exist_ok=True)
                save_frame(node, time, path, size=size, renderer=renderer, overwrite=overwrite)
                outputs.append(str(path))
        return {"frames": outputs}

    if args.storyboard:
        count = max(1, args.storyboard)
        times = [duration * (i + 0.5) / count for i in range(count)]
        directory = args.output or out_dir / f"{name}_storyboard"
        with create_renderer(args.backend, antialias=1) as renderer:
            sheet = render_storyboard(node, times, directory, size=size, renderer=renderer, overwrite=overwrite)
        return {"storyboard": str(sheet), "times": [round(t, 3) for t in times]}

    if args.preview is not None:
        start = max(0.0, min(args.start, duration))
        end = min(duration, start + max(0.1, args.preview))
        default = out_dir / f"{name}_preview.mp4"
        fps = args.fps or 15
        preset = "veryfast"
    elif args.range:
        start, end = args.range
        if not 0 <= start < end <= duration + 1e-9:
            raise ValueError(f"--range must satisfy 0 <= START < END <= {duration:.2f}")
        default = out_dir / f"{name}_{start:g}-{end:g}s.mp4"
        fps = args.fps or 30
        preset = "medium"
    else:
        start, end = 0.0, duration
        default = out_dir / f"{name}.mp4"
        fps = args.fps or 30
        preset = "medium"
    output = args.output or default
    output.parent.mkdir(parents=True, exist_ok=True)
    settings = ExportSettings(width=size[0], height=size[1], fps=fps, backend=args.backend, preset=preset)
    with ExportProgress() as progress:
        render(
            node,
            output,
            settings=settings,
            start_time=start,
            end_time=end,
            overwrite=overwrite,
            progress=progress,
        )
    return {"video": str(output), "start": start, "end": end, "size": list(size), "fps": fps}


def main(argv=None) -> int:
    """``python -m faceless_champ.runner path/to/scene.py[:name] [flags]``."""
    import runpy

    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0].startswith("-"):
        print("usage: python -m faceless_champ.runner FILE.py[:NAME] [flags]; see --help of run()", file=sys.stderr)
        return 2
    target, _, attr = argv[0].partition(":")
    path = Path(target).resolve()
    sys.path.insert(0, str(path.parent))
    try:
        namespace = runpy.run_path(str(path), run_name="__faceless_champ__")
    finally:
        sys.path.pop(0)
    candidates = [attr] if attr else ["build", "scene", "main_scene", "Main"]
    for key in candidates:
        if key in namespace:
            return run(namespace[key], argv=argv[1:], name=path.stem)
    print(f"faceless-champ: no {' / '.join(candidates)} found in {path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
