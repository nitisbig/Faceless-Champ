"""Project services shared by Python and CLI users."""

import hashlib
import importlib
import json
import os
import platform
import subprocess
import sys
import threading
import tomllib
from contextlib import contextmanager
from dataclasses import asdict
from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from faceless_champ import (
    Canvas,
    ExportSettings,
    Grid,
    Layer,
    PillowRenderer,
    Scene,
    Sequence,
    StoryboardSample,
    render,
    render_storyboard,
    save_frame,
)
from faceless_champ.audio import probe

from .assets import digest
from .compiler import CompiledVideo
from .context import BuildContext
from .diagnostics import KitError, fields
from .themes import THEMES
from .video import Video


def package_version(name):
    try:
        return version(name)
    except PackageNotFoundError:
        return "source"


_IMPORT_LOCK = threading.RLock()


@contextmanager
def project_imports(root):
    with _IMPORT_LOCK, _isolated_imports(root):
        yield


@contextmanager
def _isolated_imports(root):
    # Project packages such as 'videos' must not leak across sequential builds.
    names = {p.stem for p in root.iterdir() if p.suffix == ".py" or p.is_dir()}
    saved = {k: v for k, v in sys.modules.items() if k.split(".")[0] in names}
    for key in saved:
        del sys.modules[key]
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(root))
    importlib.invalidate_caches()
    try:
        yield
    finally:
        for key in list(sys.modules):
            if key.split(".")[0] in names:
                del sys.modules[key]
        sys.modules.update(saved)
        sys.path.remove(str(root))
        sys.dont_write_bytecode = previous


class Project:
    def __init__(self, root="."):
        path = Path(root).resolve()
        self.config_path = path if path.is_file() else path / "facelesschamp.toml"
        self.root = self.config_path.parent
        if not self.config_path.is_file():
            raise KitError("CONFIG", "No facelesschamp.toml found; use --project PATH or fc-kit init")
        self.config = tomllib.loads(self.config_path.read_text())
        fields(self.config, {"schema_version", "project", "videos", "profiles"}, "config")
        if self.config.get("schema_version") != 1:
            raise KitError("CONFIG_VERSION", "Expected schema_version = 1")
        fields(self.config.get("project", {}), {"name", "seed", "safe_margin", "caption_space"}, "project")
        if not isinstance(self.config.get("videos"), dict) or not self.config["videos"]:
            raise KitError("CONFIG", "Define at least one video factory")
        for name, settings in self.config["videos"].items():
            fields(settings, {"factory", "format", "theme", "captions"}, f"videos.{name}")
            if not isinstance(settings.get("factory"), str) or settings["factory"].count(":") != 1:
                raise KitError("CONFIG", "factory must be module:function", video=name)
            if settings.get("format", "shorts") not in {"shorts", "landscape"}:
                raise KitError("CONFIG", "format must be shorts or landscape", video=name)
            if settings.get("theme", "midnight") not in THEMES:
                raise KitError(
                    "CONFIG", "Config theme must be midnight or light; custom themes can be assigned in build(ctx)"
                )
            if not isinstance(settings.get("captions", False), bool):
                raise KitError("CONFIG", "captions must be a boolean")
        for name, settings in self.config.get("profiles", {}).items():
            fields(settings, {"width", "height", "fps", "crf", "preset", "antialias", "quality"}, f"profiles.{name}")

    def build(self, video_id="main", *, strict_assets=False):
        try:
            settings = self.config["videos"][video_id]
        except KeyError:
            raise KitError("VIDEO_ID", f"Unknown video {video_id!r}") from None
        theme = THEMES[settings.get("theme", "midnight")]
        size = (1080, 1920) if settings.get("format", "shorts") == "shorts" else (1920, 1080)
        opts = self.config.get("project", {})
        ctx = BuildContext(
            self.root,
            Canvas(*size, theme.background),
            theme,
            seed=opts.get("seed", 0),
            safe_margin=opts.get("safe_margin", 64),
            caption_space=opts.get("caption_space", 220),
            captions=settings.get("captions", False),
        )
        with project_imports(self.root):
            try:
                module, name = settings["factory"].split(":")
                factory = getattr(importlib.import_module(module), name)
                definition = factory(ctx)
                if isinstance(definition, Video):
                    result = definition.compile()
                elif isinstance(definition, (Scene, Sequence, Grid, Layer)):
                    result = CompiledVideo(
                        definition,
                        {
                            "schema_version": 1,
                            "authoring": "core",
                            "duration": definition.duration,
                            "segments": [],
                            "diagnostics": [
                                {"code": "CORE_METADATA", "message": "Only assets resolved through context are tracked"}
                            ],
                        },
                        ctx,
                    )
                else:
                    raise KitError("FACTORY_RESULT", "Factory must return Video or a core composition")
            except KitError:
                raise
            except (ImportError, AttributeError, TypeError, ValueError, OSError) as exc:
                raise KitError("FACTORY", str(exc), video=video_id) from exc
        result.report.update(
            {
                "video": video_id,
                "canvas": asdict(result.composition.canvas),
                "theme": asdict(ctx.theme),
                "seed": ctx.seed,
                "assets": list(ctx.assets.resolved.values()),
                "versions": {
                    "kit": package_version("facelesschamp-kit"),
                    "core": package_version("faceless-champ"),
                    "python": platform.python_version(),
                },
            }
        )
        sources = {}
        for directory, dirs, names in os.walk(self.root):
            dirs[:] = sorted(
                d for d in dirs if not d.startswith(".") and d not in {"output", "__pycache__", "build", "dist"}
            )
            for name in sorted(names):
                p = Path(directory) / name
                if p.suffix in {".py", ".toml", ".json", ".csv", ".srt", ".lock"}:
                    sources[str(p.relative_to(self.root))] = digest(p)
        result.report["sources"] = sources
        result.report["fingerprint"] = hashlib.sha256(json.dumps(result.report, sort_keys=True).encode()).hexdigest()
        if strict_assets and any(a["placeholder"] for a in result.report["assets"]):
            raise KitError("ASSET_PLACEHOLDER", "Supply missing media or explicitly allow placeholders", video=video_id)
        PillowRenderer(1).validate(result.composition)
        if result.duration <= 0:
            raise KitError("EMPTY_VIDEO", "Video duration must be positive", video=video_id)
        return result

    def settings(self, compiled, profile):
        if profile not in {"preview", "final"} and profile not in self.config.get("profiles", {}):
            raise KitError("PROFILE", f"Unknown profile {profile!r}")
        c = compiled.composition.canvas
        ratio = 540 / min(c.width, c.height) if profile == "preview" else 1
        values = {
            "width": round(c.width * ratio / 2) * 2,
            "height": round(c.height * ratio / 2) * 2,
            "fps": 15 if profile == "preview" else 30,
            "antialias": 1 if profile == "preview" else 2,
            "preset": "veryfast" if profile == "preview" else "medium",
        }
        values.update(self.config.get("profiles", {}).get(profile, {}))
        settings = ExportSettings(**values)
        settings.dimensions(c)
        return settings

    def validate(self, video_id="main", *, strict_assets=False):
        compiled = self.build(video_id, strict_assets=strict_assets)
        for profile in {"preview", "final", *self.config.get("profiles", {})}:
            self.settings(compiled, profile)
        return compiled.report

    def frame(self, video_id, time, output, *, overwrite=False):
        compiled = self.build(video_id)
        size = self.settings(compiled, "preview").dimensions(compiled.composition.canvas)
        path = save_frame(compiled.composition, time, output, size=size, overwrite=overwrite)
        self._report(compiled, "frame", path, {"source_time": time})
        return path

    def storyboard(self, video_id, output, *, overwrite=False):
        compiled = self.build(video_id)
        segments = compiled.report["segments"]
        samples = [StoryboardSample((s["start"] + s["end"]) / 2, s["id"]) for s in segments]
        samples = samples or [StoryboardSample(compiled.duration / 2, video_id)]
        path = render_storyboard(compiled.composition, samples, output, overwrite=overwrite)
        self._report(compiled, "storyboard", path, {})
        return path

    def export(
        self,
        video_id,
        output,
        *,
        preview=False,
        profile=None,
        segment=None,
        start=None,
        end=None,
        overwrite=False,
        allow_placeholders=False,
    ):
        profile = profile or ("preview" if preview else "final")
        compiled = self.build(video_id, strict_assets=profile == "final" and not allow_placeholders)
        if segment is not None:
            if start is not None or end is not None:
                raise KitError("RANGE", "Use a segment or a start/end range")
            match = next((s for s in compiled.report["segments"] if s["id"] == segment), None)
            if match is None:
                raise KitError("SEGMENT_ID", f"Unknown segment {segment!r}")
            start, end = match["start"], match["end"]
        elif (start is None) != (end is None):
            raise KitError("RANGE", "Specify both start and end")
        elif start is None:
            start, end = 0, min(10, compiled.duration) if preview else compiled.duration
        settings = self.settings(compiled, profile)
        path = render(
            compiled.composition, output, settings=settings, start_time=start, end_time=end, overwrite=overwrite
        )
        self._report(
            compiled,
            "preview" if preview else "render",
            path,
            {
                "profile": profile,
                "export_settings": asdict(settings),
                "source_range": [start, end],
                "output_metadata": probe(path),
            },
        )
        return path

    def _report(self, compiled, operation, output, extra):
        report = compiled.report | {
            "tools": tool_versions(),
            "operation": operation,
            "output": str(Path(output).resolve()),
            **extra,
        }
        report["build_fingerprint"] = hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest()
        directory = self.root / ".fc-kit/reports"
        directory.mkdir(parents=True, exist_ok=True)
        name = hashlib.sha256(str(output).encode()).hexdigest()[:10]
        path = directory / f"{operation}-{name}.json"
        path.write_text(json.dumps(report, indent=2) + "\n")


@lru_cache(maxsize=1)
def tool_versions():
    versions = {}
    for tool in ("ffmpeg", "ffprobe"):
        try:
            result = subprocess.run([tool, "-version"], capture_output=True, text=True, check=False)
            versions[tool] = result.stdout.splitlines()[0] if result.returncode == 0 else "unavailable"
        except OSError:
            versions[tool] = "unavailable"
    return versions
