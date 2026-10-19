"""Production services shared by external agents, the CLI, and Python callers."""

import hashlib
import importlib
import json
import math
import shutil
import tempfile
import uuid
from dataclasses import replace
from pathlib import Path

from faceless_champ import (
    Scene,
    StoryboardSample,
    SubtitleTrack,
    create_renderer,
    render,
    render_storyboard,
    rendering_identity,
    save_frame,
)
from faceless_champ.audio import probe
from facelesschamp_kit import Project, Video
from facelesschamp_kit.assets import digest
from facelesschamp_kit.themes import THEMES

from .errors import AgentError
from .media import run_tool, verify_media
from .models import QualityReport, ReviewSubmission, VideoPlan

EXPORT_QUALITIES = {"low": "ql", "high": "qh", "4k": "qk"}


def _hash(record):
    return hashlib.sha256(json.dumps(record, sort_keys=True, default=str).encode()).hexdigest()


def _write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}-{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(value, indent=2, default=str) + "\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _file_identity(path):
    path = Path(path)
    if path.is_dir():
        return {str(p.relative_to(path)): digest(p) for p in sorted(path.rglob("*")) if p.is_file()}
    return digest(path) if path.is_file() else None


def _package_identity(directory):
    """Include packaged fonts/icons/media so their updates invalidate review evidence."""
    directory = Path(directory)
    return _hash(
        {
            str(path.relative_to(directory)): digest(path)
            for path in sorted(directory.rglob("*"))
            if path.is_file()
            and not any(part.startswith((".", "__")) for part in path.relative_to(directory).parts[:-1])
            and path.suffix not in {".pyc", ".pyo"}
        }
    )


class AgentProject:
    def __init__(self, root="."):
        root = Path(root).resolve()
        self.root = root.parent if root.is_file() else root
        self.kit = Project(self.root)
        self.plan_path = self.root / "agent-plan.json"
        if not self.plan_path.is_file():
            raise AgentError(
                "PLAN_MISSING", "No agent-plan.json found", suggested_fix="Run fc-agent init or add a VideoPlan"
            )
        self.state = self.root / ".fc-agent"

    @property
    def plan(self):
        return VideoPlan.model_validate_json(self.plan_path.read_text())

    def _inputs(self, plan):
        paths = [a.path for a in plan.brief.assets]
        paths += [p for p in (plan.brief.narration.audio, plan.brief.narration.subtitles, plan.design.font) if p]
        paths += [s.content["prepared"] for s in plan.scenes if s.recipe == "code-result"]
        if plan.design.template == "coding-tutorial":
            paths.append("templates/coding-tutorial/style.json")
        return {p: _file_identity(self.root / p) for p in paths}

    def _design(self, plan):
        if plan.design.template != "coding-tutorial":
            return plan.design
        from .templates import load_coding_tutorial

        palette = {**load_coding_tutorial(self.root).style.palette, **plan.design.palette}
        return plan.design.model_copy(update={"palette": palette})

    def _fingerprint(self, compiled, plan):
        # Review submissions are workflow evidence, not video source. Excluding
        # their valid typed records prevents a submission hashing itself when a
        # caller saves it in the project root instead of .fc-agent/submissions.
        build = dict(compiled.report)
        sources = dict(build.get("sources", {}))
        for name in list(sources):
            if name.endswith(".json") and name != "agent-plan.json":
                try:
                    ReviewSubmission.model_validate_json((self.root / name).read_text())
                except (ValueError, OSError):
                    continue
                sources.pop(name)
        build["sources"] = sources
        build.pop("fingerprint", None)
        implementations = {}
        for package in ("faceless_champ", "facelesschamp_kit", "facelesschamp_agent"):
            directory = Path(importlib.import_module(package).__file__).parent
            implementations[package] = _package_identity(directory)
        return _hash(
            {
                "plan": plan.model_dump(mode="json"),
                "build": build,
                "inputs": self._inputs(plan),
                "agent_version": "0.1.0rc2",
                "implementations": implementations,
            }
        )

    def _narration(self, *, prepare=False):
        spec = self.plan.brief.narration
        if spec.audio is None:
            return None, None, None
        audio = (self.root / spec.audio).resolve()
        subtitles = (self.root / spec.subtitles).resolve() if spec.subtitles else None
        if not audio.is_file() or (subtitles and not subtitles.is_file()):
            raise AgentError("NARRATION_MISSING", "Supply the audio/subtitle files declared in the plan")
        duration = float(probe(audio)["format"]["duration"])
        track = SubtitleTrack.from_srt(subtitles, overlap_tolerance=spec.overlap_tolerance) if subtitles else None
        if track is None or track.duration <= duration + 0.001:
            return audio, subtitles, {"source": str(audio), "derived": False}
        identity = _hash({"audio": digest(audio), "subtitles": digest(subtitles), "end": track.duration})
        target = self.state / "derived" / identity / "narration.wav"
        record_path = target.with_suffix(".json")
        valid = target.is_file() and record_path.is_file()
        if valid:
            record = json.loads(record_path.read_text())
            valid = record.get("checksum") == digest(target)
        if not valid:
            if not prepare:
                raise AgentError(
                    "NARRATION_PREPARE",
                    "Subtitle tail needs a derived padded audio copy",
                    suggested_fix="Run fc-agent prepare; source audio and cue times stay unchanged",
                )
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(f"{uuid.uuid4().hex}.wav")
            try:
                run_tool(
                    [
                        "ffmpeg",
                        "-v",
                        "error",
                        "-i",
                        str(audio),
                        "-af",
                        "apad",
                        "-t",
                        str(track.duration),
                        "-c:a",
                        "pcm_s16le",
                        str(temporary),
                    ]
                )
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
            record = {
                "source": str(audio),
                "source_checksum": digest(audio),
                "derived": True,
                "path": str(target),
                "checksum": digest(target),
                "silence_tail": track.duration - duration,
                "subtitle_checksum": digest(subtitles),
                "cue_times_preserved": True,
            }
            _write_json(record_path, record)
        return target, subtitles, record

    def new_video(self, context):
        """Apply the plan's design, assets and master narration to a fresh kit Video.

        Call from ordinary ``build(ctx)`` Python. This never executes preparation.
        """
        plan = self.plan
        design = self._design(plan)
        base_theme = THEMES[design.theme]
        typography = {}
        if design.font:
            # A plan's font may be static. Variable-font weights belong to the
            # selected packaged font, so do not carry them into a replacement.
            typography = {
                "font": str(self.root / design.font),
                "font_weight": None,
                "heading_weight": None,
            }
        context.theme = replace(
            base_theme,
            **design.palette,
            **typography,
            body_size=design.body_size,
            heading_size=design.heading_size,
            minimum_font_size=design.minimum_font_size,
            spacing=design.spacing,
            motion_duration=design.motion_duration,
            text_engine=design.text_engine,
            surface_mode=design.surface_mode,
        )
        context.canvas = replace(context.canvas, bg=context.theme.background)
        context.captions = design.captions
        for asset in plan.brief.assets:
            if asset.kind in {"image", "audio", "subtitle", "font", "mesh"}:
                entry = {"type": asset.kind, "path": asset.path, "source": asset.source}
                existing = context.assets.entries.get(asset.id)
                if existing and (existing.get("path") != asset.path or existing.get("type") != asset.kind):
                    raise AgentError("ASSET_CONFLICT", "Plan and manifest disagree", asset=asset.id)
                context.assets.entries.setdefault(asset.id, entry)
        video = Video(context)
        audio, subtitles, _ = self._narration()
        if audio:
            video.narration(
                audio=audio,
                subtitles=subtitles,
                captions=design.captions,
                overlap_tolerance=plan.brief.narration.overlap_tolerance,
            )
        return video

    def _build(self):
        plan = self.plan
        compiled = self.kit.build(plan.video_id)
        for profile in ("preview", "final"):
            self.kit.settings(compiled, profile)
        reports = {s["id"]: s for s in compiled.report.get("segments", [])}
        if set(reports) != {s.id for s in plan.scenes}:
            raise AgentError(
                "PLAN_SEGMENTS",
                "Plan scene IDs must match kit segment IDs",
                actual=sorted(reports),
                suggested_fix="Update the plan or Python scene IDs together",
            )
        for scene in plan.scenes:
            actual = reports[scene.id]
            if (
                abs(actual["start"] - scene.start) > 1e-6
                or abs(actual["authored_end"] - scene.start - scene.duration) > 1e-6
            ):
                raise AgentError("PLAN_TIMING", "Plan and authored scene timing differ", scene=scene.id)
            targets = {p["id"] for p in actual["placements"]}
            targets |= {f"{p['id']}/{child}" for p in actual["placements"] for child in p["children"]}
            for event in scene.key_events:
                if event.target and event.target not in targets:
                    raise AgentError(
                        "PLAN_TARGET",
                        "Key event references an unknown placement or child",
                        scene=scene.id,
                        element=event.target,
                        candidates=sorted(targets),
                    )
        if abs(compiled.duration - plan.brief.duration) > 1e-6:
            raise AgentError(
                "PLAN_DURATION", "Brief duration differs from complete composition", actual=compiled.duration
            )
        expected_size = (1920, 1080) if plan.brief.format == "landscape" else (1080, 1920)
        if (compiled.composition.canvas.width, compiled.composition.canvas.height) != expected_size:
            raise AgentError("PLAN_FORMAT", "Kit canvas and planned format differ")
        theme = compiled.report["theme"]
        design = self._design(plan)
        for name in ("body_size", "minimum_font_size", "heading_size", "spacing", "motion_duration"):
            if theme[name] != getattr(design, name):
                raise AgentError(
                    "PLAN_DESIGN", "Compiled design differs from plan; use AgentProject.new_video(ctx)", property=name
                )
        if theme["name"] != design.theme or any(theme[k] != v for k, v in design.palette.items()):
            raise AgentError("PLAN_DESIGN", "Compiled palette/theme differs from plan")
        narration = compiled.report.get("narration")
        if bool(narration) != bool(plan.brief.narration.audio):
            raise AgentError("PLAN_NARRATION", "Planned and attached master narration differ")
        if narration:
            audio, subtitles, _ = self._narration()
            if narration["audio_checksum"] != digest(audio) or narration["subtitle_checksum"] != (
                digest(subtitles) if subtitles else None
            ):
                raise AgentError("PLAN_NARRATION", "Attached narration does not match the planned source")
        inputs = self._inputs(plan)
        missing = []
        for asset in plan.brief.assets:
            if inputs[asset.path] is None and asset.required:
                if asset.kind != "image":
                    raise AgentError("ASSET_MISSING", "Required input is missing", asset=asset.id, path=asset.path)
                missing.append(asset.id)
        placeholders = [a["id"] for a in compiled.report.get("assets", []) if a.get("placeholder")]
        if set(missing) - set(placeholders):
            raise AgentError(
                "ASSET_PLACEHOLDER",
                "Missing required artwork must appear as a labeled placeholder",
                assets=sorted(set(missing) - set(placeholders)),
                suggested_fix="Use ImageCard(..., mode='auto') or supply the artwork",
            )
        return compiled, plan, self._fingerprint(compiled, plan)

    def _record(self, operation, fingerprint, *, artifacts=(), **data):
        identifier = uuid.uuid4().hex
        result = {"id": identifier, "operation": operation, "fingerprint": fingerprint, **data, "artifacts": []}
        for raw in artifacts:
            artifact = dict(raw)
            path = Path(artifact["path"]).resolve()
            artifact.update(id=artifact.get("id", uuid.uuid4().hex), path=str(path), checksum=digest(path))
            result["artifacts"].append(artifact)
        _write_json(self.state / "records" / f"{identifier}.json", result)
        return result

    def _records(self, fingerprint=None):
        records = []
        directory = self.state / "records"
        for path in sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime_ns):
            record = json.loads(path.read_text())
            if fingerprint is None or record["fingerprint"] == fingerprint:
                records.append(record)
        return records

    @staticmethod
    def _intact(artifact):
        path = Path(artifact["path"])
        return path.is_file() and digest(path) == artifact["checksum"]

    def validate(self):
        compiled, plan, fingerprint = self._build()
        profiles = {}
        for profile in ("preview", "final"):
            settings = self.kit.settings(compiled, profile)
            with create_renderer(settings.backend, antialias=settings.antialias, gpu=settings.gpu) as renderer:
                renderer.validate(compiled.composition)
                profiles[profile] = rendering_identity(settings.backend, renderer=renderer)
        return self._record(
            "validate",
            fingerprint,
            status="passed",
            duration=compiled.duration,
            diagnostics=compiled.report["diagnostics"],
            scene_count=len(plan.scenes),
            profile_rendering=profiles,
        )

    def _final_rendering(self, compiled):
        settings = self.kit.settings(compiled, "final")
        if settings.backend not in {"auto", "moderngl"}:
            return rendering_identity(settings.backend)
        with create_renderer(settings.backend, antialias=settings.antialias, gpu=settings.gpu) as renderer:
            renderer.validate(compiled.composition)
            return rendering_identity(settings.backend, renderer=renderer)

    @staticmethod
    def _same_rendering(actual, expected):
        if actual.get("backend", "pillow") != expected["backend"]:
            return False
        if expected["backend"] == "moderngl":
            keys = ("shader_hash", "color_pipeline", "driver", "renderer")
            return all(actual.get(key) == expected.get(key) for key in keys)
        return True

    def audit_layout(self, *, detailed=False):
        """Audit public layout geometry at boundaries, actions and motion samples."""
        from .layout import audit_layout

        compiled, plan, fingerprint = self._build()
        result = audit_layout(compiled, plan)
        record = self._record("audit-layout", fingerprint, **result)
        if detailed:
            return record
        return {
            **{key: value for key, value in record.items() if key != "sample_times"},
            "sample_count": len(record["sample_times"]),
            "report_path": str(self.state / "records" / f"{record['id']}.json"),
        }

    def entrypoint(self):
        """Write the portable, preview-first render.py without replacing user code."""
        import shlex

        from .delivery import write_render_entrypoint

        path = write_render_entrypoint(self.root)
        return {"path": str(path), "command": shlex.join(["python", str(path)])}

    def prepare(self):
        _, _, narration = self._narration(prepare=True)
        self.kit.prepare(self.plan.video_id)
        compiled, _, fingerprint = self._build()
        return self._record(
            "prepare",
            fingerprint,
            status="passed",
            narration=narration,
            prepared_assets=compiled.report.get("prepared_assets", []),
        )

    def sample_times(self):
        plan = self.plan
        times = set()
        for scene in plan.scenes:
            duration = scene.duration
            for time in (0, min(0.6, duration * 0.15), duration / 2, max(0, duration - 1 / 30)):
                times.add(scene.start + time)
            for event in scene.key_events:
                for time in (event.at - 1 / 30, event.at, event.at + event.duration / 2, event.at + event.duration):
                    times.add(scene.start + max(0, min(duration - 1 / 30, time)))
        return sorted(t for t in times if 0 <= t < plan.brief.duration)

    def _output(self, output, operation, suffix):
        if output is not None:
            return Path(output).resolve()
        return self.root / "output" / "agent" / f"{operation}-{uuid.uuid4().hex[:12]}{suffix}"

    def frame(self, time, output=None):
        compiled, _, fingerprint = self._build()
        path = self._output(output, "frame", ".png")
        settings = self.kit.settings(compiled, "preview")
        size = settings.dimensions(compiled.composition.canvas)
        with create_renderer(settings.backend, antialias=settings.antialias, gpu=settings.gpu) as renderer:
            save_frame(compiled.composition, time, path, size=size, renderer=renderer)
        return self._record(
            "frame",
            fingerprint,
            artifacts=[{"path": str(path), "kind": "frame", "source_time": time}],
            layout=compiled.layout_at(time),
            rendering=rendering_identity(settings.backend, renderer=renderer),
        )

    def storyboard(self, output=None):
        compiled, plan, fingerprint = self._build()
        directory = self._output(output, "storyboard", "")
        times = self.sample_times()
        samples = [
            StoryboardSample(t, " / ".join(s.id for s in plan.scenes if s.start <= t < s.start + s.duration))
            for t in times
        ]
        settings = self.kit.settings(compiled, "preview")
        with create_renderer(settings.backend, antialias=settings.antialias, gpu=settings.gpu) as renderer:
            sheet = render_storyboard(compiled.composition, samples, directory, renderer=renderer)
        frames = sorted((p for p in directory.glob("*.png") if p != sheet), key=lambda p: int(p.stem.split("-", 1)[0]))
        artifacts = [
            {"path": str(p), "kind": "frame", "source_time": time} for p, time in zip(frames, times, strict=True)
        ]
        artifacts.append({"path": str(sheet), "kind": "storyboard", "sample_times": times})
        layouts = [compiled.layout_at(t) for t in times]
        findings = []
        for layout in layouts:
            rows = layout["placements"]
            for i, left in enumerate(rows):
                a = left["bounds"]
                for right in rows[i + 1 :]:
                    b = right["bounds"]
                    if max(a["left"], b["left"]) < min(a["right"], b["right"]) and max(a["top"], b["top"]) < min(
                        a["bottom"], b["bottom"]
                    ):
                        findings.append(
                            {
                                "code": "LAYOUT_INTERSECTION",
                                "source_time": layout["source_time"],
                                "elements": [left["id"], right["id"]],
                                "severity": "info",
                                "message": "Conservative bounds intersect; inspect whether overlap is intentional",
                            }
                        )
        return self._record(
            "storyboard",
            fingerprint,
            artifacts=artifacts,
            layouts=layouts,
            diagnostics=findings,
            rendering=rendering_identity(settings.backend, renderer=renderer),
        )

    def _render(self, start, end, profile, output, *, operation, fps=None, quality=None, progress=None):
        if fps is not None and (
            isinstance(fps, bool) or not isinstance(fps, (int, float)) or not math.isfinite(fps) or fps <= 0
        ):
            raise AgentError("EXPORT_FPS", "FPS must be finite and positive")
        if quality is not None and (not isinstance(quality, str) or quality not in EXPORT_QUALITIES):
            raise AgentError("EXPORT_QUALITY", "Choose low, high or 4k")
        if progress is not None and not callable(progress):
            raise AgentError("EXPORT_PROGRESS", "Progress must be callable")
        compiled, plan, fingerprint = self._build()
        if not 0 <= start < end <= compiled.duration:
            raise AgentError("RANGE", "Expected 0 <= start < end <= duration")
        settings = self.kit.settings(compiled, profile)
        if fps is not None:
            settings = replace(settings, fps=fps)
        if quality is not None:
            settings = replace(settings, quality=EXPORT_QUALITIES[quality], width=None, height=None)
        settings.dimensions(compiled.composition.canvas)
        path = self._output(output, operation, ".mp4")
        with create_renderer(settings.backend, antialias=settings.antialias, gpu=settings.gpu) as renderer:
            render(
                compiled.composition,
                path,
                settings=settings,
                start_time=start,
                end_time=end,
                progress=progress,
                renderer=renderer,
            )
        width, height = settings.dimensions(compiled.composition.canvas)
        return self._record(
            operation,
            fingerprint,
            artifacts=[{"path": str(path), "kind": "video", "source_range": [start, end]}],
            expected={
                "width": width,
                "height": height,
                "fps": settings.fps,
                "duration": end - start,
                "require_audio": bool(plan.brief.narration.audio),
            },
            profile=profile,
            rendering=rendering_identity(settings.backend, renderer=renderer),
            source_range=[start, end],
            status="exported",
        )

    def preview(self, output=None, *, start=None, end=None, scene=None, fps=None, quality=None, progress=None):
        plan = self.plan
        if scene is not None:
            if start is not None or end is not None:
                raise AgentError("RANGE", "Choose a scene or an explicit range")
            match = next((s for s in plan.scenes if s.id == scene), None)
            if match is None:
                raise AgentError("SCENE_ID", "Unknown scene", scene=scene)
            start, end = match.start, match.start + match.duration
        if (start is None) != (end is None):
            raise AgentError("RANGE", "Specify both start and end")
        if start is not None:
            return self._render(
                start, end, "preview", output, operation="preview", fps=fps, quality=quality, progress=progress
            )
        if output is not None:
            return self._render(
                0,
                min(10, plan.brief.duration),
                "preview",
                output,
                operation="preview",
                fps=fps,
                quality=quality,
                progress=progress,
            )
        centers = {s.start for s in plan.scenes}
        centers |= {s.start + e.at for s in plan.scenes for e in s.key_events}
        ranges = []
        for center in sorted(centers):
            low, high = max(0, center - 0.5), min(plan.brief.duration, center + 1.5)
            if ranges and low <= ranges[-1][1]:
                ranges[-1][1] = max(ranges[-1][1], high)
            else:
                ranges.append([low, high])
        records = [
            self._render(a, b, "preview", None, operation="preview", fps=fps, quality=quality, progress=progress)
            for a, b in ranges
        ]
        return {"operation": "preview-set", "records": records}

    def render(self, output=None, *, fps=None, quality=None, progress=None):
        result = self._render(
            0,
            self.plan.brief.duration,
            "final",
            output,
            operation="render",
            fps=fps,
            quality=quality,
            progress=progress,
        )
        result["verification"] = self.verify(result["artifacts"][0]["path"])
        return result

    def verify(self, output=None):
        compiled, _plan, fingerprint = self._build()
        records = self._records(fingerprint)
        path = str(Path(output).resolve()) if output else None
        candidates = [
            r
            for r in records
            if r["operation"] in {"render", "preview"} and (path is None or r["artifacts"][0]["path"] == path)
        ]
        if not candidates:
            raise AgentError(
                "ARTIFACT_UNKNOWN",
                "No current render record matches this output",
                suggested_fix="Render the current project with fc-agent first",
            )
        source = candidates[-1]
        artifact = source["artifacts"][0]
        if not self._intact(artifact):
            raise AgentError("ARTIFACT_CHANGED", "Rendered output was changed or removed", path=artifact["path"])
        reference, _, _ = self._narration()
        audio = compiled.composition.audio if isinstance(compiled.composition, Scene) else []
        unchanged = (
            bool(reference)
            and len(audio) == 1
            and audio[0].start == 0
            and audio[0].trim_start == 0
            and audio[0].volume == 1
            and not audio[0].fade_in
            and not audio[0].fade_out
        )
        directory = self._output(None, "decoded", "")
        start, end = source["source_range"]
        samples = [t - start for t in self.sample_times() if start <= t < end]
        result = verify_media(
            artifact["path"],
            **source["expected"],
            frame_directory=directory,
            reference=reference if unchanged else None,
            source_start=start,
            samples=samples,
            alignment_reason=None if unchanged else "Audio arrangement is not an unchanged master",
        )
        artifacts = [{**f, "kind": "decoded_frame"} for f in result.pop("frames")]
        artifacts.append(artifact)
        return self._record(
            "verify",
            fingerprint,
            artifacts=artifacts,
            source_record=source["id"],
            verified_operation=source["operation"],
            rendering=source.get("rendering", rendering_identity("pillow")),
            **result,
        )

    def review(self, submission):
        submission = (
            submission if isinstance(submission, ReviewSubmission) else ReviewSubmission.model_validate(submission)
        )
        compiled, plan, fingerprint = self._build()
        if submission.fingerprint != fingerprint:
            raise AgentError("REVIEW_STALE", "Review does not match the current build")
        records = self._records(fingerprint)
        artifacts = {a["id"]: a for r in records for a in r["artifacts"]}
        wanted = set(submission.evidence_artifacts) | {f.evidence_artifact for f in submission.findings}
        final_rendering = self._final_rendering(compiled)
        evidence_backends = {
            a["id"]: r.get("rendering", {"backend": "pillow"}) for r in records for a in r["artifacts"]
        }
        for identifier in wanted:
            if identifier not in artifacts or not self._intact(artifacts[identifier]):
                raise AgentError("REVIEW_EVIDENCE", "Evidence is unknown, stale, or changed", artifact=identifier)
            if not self._same_rendering(evidence_backends.get(identifier, {}), final_rendering):
                raise AgentError(
                    "REVIEW_BACKEND", "Review evidence must use the final output backend", artifact=identifier
                )
        scenes = {s.id: s for s in plan.scenes}
        if set(submission.reviewed_scenes) - scenes.keys():
            raise AgentError("REVIEW_SCENE", "Unknown reviewed scene")

        def covers(artifact, scene):
            if "source_range" in artifact:
                low, high = artifact["source_range"]
                return max(low, scene.start) < min(high, scene.start + scene.duration)
            times = artifact.get("sample_times", [artifact.get("source_time", -1)])
            return any(scene.start <= time < scene.start + scene.duration for time in times)

        if submission.status != "unverified":
            for scene_id in submission.reviewed_scenes:
                if not any(covers(artifacts[a], scenes[scene_id]) for a in submission.evidence_artifacts):
                    raise AgentError(
                        "REVIEW_COVERAGE", "No supplied evidence covers the reviewed scene", scene=scene_id
                    )
        for finding in submission.findings:
            scene = scenes.get(finding.scene_id)
            if scene is None or not scene.start <= finding.source_time < scene.start + scene.duration:
                raise AgentError("REVIEW_TIME", "Finding lies outside its scene", scene=finding.scene_id)
            if finding.scene_id not in submission.reviewed_scenes or not covers(
                artifacts[finding.evidence_artifact], scene
            ):
                raise AgentError(
                    "REVIEW_COVERAGE", "Finding evidence does not cover its reviewed scene", scene=scene.id
                )
            if finding.element:
                segment = next(s for s in compiled.report["segments"] if s["id"] == scene.id)
                targets = {p["id"] for p in segment["placements"]}
                targets |= {f"{p['id']}/{c}" for p in segment["placements"] for c in p["children"]}
                if finding.element not in targets:
                    raise AgentError("REVIEW_TARGET", "Finding references an unknown element", element=finding.element)
        # Recording findings remains possible after the budget is exhausted.
        # The external authoring skill stops repairs; evidence is never discarded.
        return self._record("review", fingerprint, submission=submission.model_dump(mode="json"))

    def status(self):
        compiled, plan, fingerprint = self._build()
        report = QualityReport(fingerprint=fingerprint)
        report.structural_validation = "passed"
        report.narration_alignment = "pending" if plan.brief.narration.audio else "not_applicable"
        if not plan.brief.narration.audio:
            report.draft_reasons.append("No supplied narration: silent draft")
        missing = [a["id"] for a in compiled.report.get("assets", []) if a.get("placeholder")]
        if missing:
            report.draft_reasons.append("Placeholder artwork: " + ", ".join(sorted(set(missing))))
        report.draft = bool(report.draft_reasons)
        current = self._records(fingerprint)
        final_rendering = self._final_rendering(compiled)
        artifacts = {a["id"]: a for r in current for a in r["artifacts"] if self._intact(a)}
        artifact_rendering = {
            a["id"]: r.get("rendering", {"backend": "pillow"}) for r in current for a in r["artifacts"]
        }
        report.artifacts = list(artifacts.values())
        reviewed = {"visual": {}, "editorial": {}}
        latest_full = next((r["id"] for r in reversed(current) if r["operation"] == "render"), None)
        for record in current:
            if record["operation"] == "audit-layout":
                report.layout_validation = record["status"]
            if record["operation"] == "verify" and all(self._intact(a) for a in record["artifacts"]):
                if not self._same_rendering(record.get("rendering", {"backend": "pillow"}), final_rendering):
                    continue
                field = (
                    "full_export_media_verification"
                    if record["verified_operation"] == "render"
                    else "preview_media_verification"
                )
                if record["verified_operation"] != "render" or record["source_record"] == latest_full:
                    setattr(report, field, record["status"])
                if record["verified_operation"] == "render" or report.narration_alignment == "pending":
                    report.narration_alignment = record["narration_alignment"]["status"]
            if record["operation"] == "review":
                review = ReviewSubmission.model_validate(record["submission"])
                evidence = set(review.evidence_artifacts) | {f.evidence_artifact for f in review.findings}
                if all(
                    a in artifacts and self._same_rendering(artifact_rendering[a], final_rendering) for a in evidence
                ):
                    for scene in review.reviewed_scenes:
                        reviewed[review.kind][scene] = review
        for kind, rows in reviewed.items():
            states = [rows[s.id].status if s.id in rows else "pending" for s in plan.scenes]
            state = (
                "failed"
                if "failed" in states
                else "passed"
                if all(s == "passed" for s in states)
                else "unverified"
                if "unverified" in states
                else "pending"
            )
            setattr(report, f"{kind}_review", state)
            seen = set()
            for review in rows.values():
                key = _hash(review.model_dump(mode="json"))
                if key not in seen:
                    report.findings.extend(review.findings)
                    seen.add(key)
        attempts = {}
        for record in self._records():
            if record["operation"] == "audit-layout" and record["status"] == "failed":
                for scene in {f["scene_id"] for f in record["findings"]}:
                    if scene in {s.id for s in plan.scenes}:
                        attempts.setdefault(scene, set()).add(record["fingerprint"])
            if record["operation"] == "review" and record["submission"]["status"] == "failed":
                review = record["submission"]
                for scene in {f["scene_id"] for f in review["findings"]} or set(review["reviewed_scenes"]):
                    if scene in {s.id for s in plan.scenes}:
                        attempts.setdefault(scene, set()).add(record["fingerprint"])
        report.repair_passes = {s: max(0, len(values) - 1) for s, values in attempts.items()}
        if report.layout_validation != "passed":
            report.next_actions.append("Run audit-layout and repair unintended boundary, overflow or overlap findings")
        if not any(
            r["operation"] == "storyboard" and all(a["id"] in artifacts for a in r["artifacts"]) for r in current
        ):
            report.next_actions.append("Generate a storyboard")
        if report.preview_media_verification != "passed":
            report.next_actions.append("Render and verify motion previews")
        for kind in ("visual", "editorial"):
            if getattr(report, f"{kind}_review") not in {"passed", "unverified"}:
                report.next_actions.append(f"Record {kind} review, or explicitly mark it unverified when unavailable")
        if plan.brief.delivery == "full" and report.full_export_media_verification != "passed":
            report.next_actions.append("Render and verify the complete video")
        if report.narration_alignment in {"pending", "failed"}:
            report.next_actions.append("Verify narration alignment")
        if any(count >= plan.brief.repair_limit for count in report.repair_passes.values()):
            report.next_actions.append("Repair budget reached: report remaining findings")
        return report


def init_project(destination):
    """Create an editable ordinary kit project atomically; never merge existing work."""
    from .delivery import write_render_entrypoint
    from .scaffold import CONFIG, INITIAL_PLAN, SOURCE

    destination = Path(destination).resolve()
    if destination.exists():
        raise AgentError("DESTINATION", "Destination exists; select a new directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".fc-agent-init-", dir=destination.parent))
    try:
        (staging / "videos").mkdir()
        (staging / "assets").mkdir()
        (staging / "videos/__init__.py").write_text("")
        (staging / "videos/main.py").write_text(SOURCE)
        (staging / "facelesschamp.toml").write_text(CONFIG)
        _write_json(staging / "agent-plan.json", INITIAL_PLAN.model_dump(mode="json"))
        _write_json(staging / "assets/manifest.json", {})
        (staging / "narration.md").write_text("# Narration draft\n\n" + INITIAL_PLAN.scenes[0].narration + "\n")
        (staging / "asset-brief.md").write_text("# Asset brief\n\nThis starter uses only library-drawn elements.\n")
        (staging / ".gitignore").write_text(".fc-agent/\n.fc-kit/\noutput/\n__pycache__/\n")
        (staging / "pyproject.toml").write_text(
            '[project]\nname="agent-video"\nversion="0.1.0"\nrequires-python=">=3.12"\ndependencies=["facelesschamp-agent==0.1.0rc2"]\n'
        )
        write_render_entrypoint(staging)
        staging.rename(destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return destination
