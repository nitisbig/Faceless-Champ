"""Bounded, read-only project discovery for narration-aware scene planning.

``max_chars`` bounds readable narration/supplement excerpts, not the authoritative
cue clock. Cue timestamps and text remain complete so a small prompt cannot drop
the end of a video. Hard inventory, byte, and cue limits bound that clock too.
Project source files are treated as untrusted text and are never imported.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from collections.abc import Iterable
from itertools import pairwise
from pathlib import Path
from typing import Any

from .errors import AgentError

SCHEMA_VERSION = "1.0"
MAX_FILES = 2048
MAX_ENTRIES = 10000
MAX_DEPTH = 24
MAX_TEXT_FILE_BYTES = 2 * 1024 * 1024
MAX_TEXT_BYTES = 8 * 1024 * 1024
MAX_CUES = 20000
MAX_ASSET_SAMPLE_BYTES = 64 * 1024
MAX_CHARS = 1_000_000

_EXCLUDED = {
    "__pycache__",
    "node_modules",
    "vendor",
    "vendors",
    "venv",
    "env",
    "site-packages",
    "output",
    "outputs",
    "build",
    "dist",
    "renders",
    "rendered",
    "exports",
    "coverage",
    "htmlcov",
}
_NARRATION = {"voiceover.md": 0, "voicover.md": 1, "narration.md": 2}
_DATA = {".json", ".toml", ".yaml", ".yml", ".csv", ".tsv", ".xml"}
_TEXT = {".md", ".txt", ".rst", ".vtt"}
_CODE = {".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".ipynb"}
_MEDIA = {
    ".mp4",
    ".mov",
    ".mkv",
    ".webm",
    ".avi",
    ".m4v",
    ".gif",
    ".mp3",
    ".wav",
    ".flac",
    ".ogg",
    ".m4a",
    ".aac",
    ".opus",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".avif",
    ".bmp",
    ".tiff",
    ".exr",
}
_FONTS = {".ttf", ".otf", ".woff", ".woff2"}
_TIMING = re.compile(r"(\d{2,}):([0-5]\d):([0-5]\d)[,.](\d{3})")


def _error(code: str, message: str, *, path: str | Path | None = None, fix: str = "") -> AgentError:
    scope = {"path": str(path)} if path is not None else {}
    return AgentError(
        code,
        message,
        suggested_fix=fix or "Correct the referenced project input and rerun context discovery",
        **scope,
    )


def _allowed(relative: Path) -> bool:
    return all(not part.startswith(".") and part.lower() not in _EXCLUDED for part in relative.parts)


def _contained(root: Path, path: Path) -> Path:
    try:
        real = path.resolve(strict=True)
        real.relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise _error(
            "CONTEXT_PATH",
            "Input must resolve to an existing file or directory inside the project root",
            path=path,
            fix="Use a project-relative input; remove broken links and links outside the project",
        ) from exc
    return real


def _inventory(root: Path, paths: Iterable[str | Path] | str | Path | None, warnings: list[str]) -> list[Path]:
    if paths is None:
        selected = [root]
    elif isinstance(paths, (str, Path)):
        selected = [Path(paths)]
    else:
        try:
            selected = []
            for path in paths:
                selected.append(Path(path))
                if len(selected) > MAX_FILES:
                    raise _error("CONTEXT_LIMIT", f"Select no more than {MAX_FILES} input paths")
        except (TypeError, ValueError) as exc:
            raise _error("CONTEXT_PATH", "paths must contain file or directory paths") from exc
    files: dict[str, Path] = {}
    visited: set[Path] = set()
    entries = 0

    def visit(path: Path, depth: int) -> None:
        nonlocal entries
        entries += 1
        if entries > MAX_ENTRIES or depth > MAX_DEPTH:
            raise _error(
                "CONTEXT_LIMIT",
                "Project inventory exceeds the bounded discovery limit",
                path=path,
                fix="Pass paths=[...] with narration and selected asset/data directories, or use a smaller project root",
            )
        real = _contained(root, path)
        relative = path.relative_to(root)
        if not _allowed(relative) or not _allowed(real.relative_to(root)):
            raise _error("CONTEXT_PATH", "Hidden, vendor, and generated input trees are excluded", path=relative)
        if real.is_dir():
            if real in visited:
                return
            visited.add(real)
            try:
                children = []
                with os.scandir(path) as iterator:
                    for entry in iterator:
                        if entry.name.startswith(".") or entry.name.lower() in _EXCLUDED:
                            continue
                        children.append(Path(entry.path))
                        if len(children) + entries > MAX_ENTRIES:
                            raise _error("CONTEXT_LIMIT", "Directory exceeds the inventory limit", path=relative)
                for child in sorted(children):
                    visit(child, depth + 1)
            except OSError as exc:
                raise _error("CONTEXT_READ", f"Cannot inventory directory: {exc.strerror}", path=relative) from exc
        elif real.is_file():
            files[relative.as_posix()] = path
            if len(files) > MAX_FILES:
                raise _error(
                    "CONTEXT_LIMIT",
                    f"Project contains more than {MAX_FILES} input files",
                    path=relative,
                    fix="Pass paths=[...] to select the relevant narration, design, data, and asset inputs",
                )
        else:
            warnings.append(f"Skipped non-regular input: {relative.as_posix()}")

    for selected_path in selected:
        path = selected_path if selected_path.is_absolute() else root / selected_path
        # Resolve containment first, but preserve the authored relative name for references.
        _contained(root, path)
        path = Path(os.path.abspath(path))
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise _error("CONTEXT_PATH", "Input path is outside the project root", path=selected_path) from exc
        visit(path, 0)
    return [files[name] for name in sorted(files)]


def _kind(path: Path) -> str:
    suffix, name = path.suffix.lower(), path.name.lower()
    if suffix == ".srt":
        return "word-subtitles" if name == "cue-per-word.srt" else "subtitles"
    if name in _NARRATION:
        return "narration"
    if suffix in _DATA:
        return "data"
    if suffix in _TEXT:
        return "text"
    if suffix in _CODE:
        return "code"
    if suffix in _FONTS:
        return "font"
    if suffix in {".svg", ".ico"}:
        return "icon"
    if suffix in _MEDIA:
        return "media"
    return "asset"


def _timestamp(value: str) -> float:
    match = _TIMING.fullmatch(value.strip())
    if not match:
        raise ValueError(f"Invalid timestamp {value!r}; expected HH:MM:SS,mmm")
    hours, minutes, seconds, milliseconds = map(int, match.groups())
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000


def _parse_srt(text: str, source: str) -> list[dict[str, Any]]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        raise _error("CONTEXT_SRT", "Subtitle file is empty", path=source)
    cues: list[dict[str, Any]] = []
    indices: set[int] = set()
    for block_number, block in enumerate(re.split(r"\n(?:[ \t]*\n)+", normalized), 1):
        try:
            lines = block.splitlines()
            index = int(lines[0].strip())
            if index < 1 or index in indices:
                raise ValueError("Cue indices must be positive and unique")
            start_text, end_text = re.split(r"\s*-->\s*", lines[1])
            start, end = _timestamp(start_text), _timestamp(end_text)
            content = "\n".join(lines[2:]).strip()
            if not math.isfinite(start) or not math.isfinite(end) or end <= start or not content:
                raise ValueError("Each cue needs text and an end time after its start")
            if cues and start < cues[-1]["start"]:
                raise ValueError("Cue start times must be in source order")
        except (IndexError, ValueError, OverflowError) as exc:
            raise _error(
                "CONTEXT_SRT",
                f"Malformed SRT block {block_number}: {exc}",
                path=source,
                fix="Fix the indicated SRT block; retain original source timestamps and intentional overlaps",
            ) from exc
        indices.add(index)
        cues.append(
            {"id": f"{source}#{index}", "index": index, "start": start, "end": end, "text": content, "source": source}
        )
        if len(cues) > MAX_CUES:
            raise _error(
                "CONTEXT_LIMIT",
                f"Subtitle file exceeds {MAX_CUES} cues",
                path=source,
                fix="Split the project into chapters; do not truncate or retime the source clock",
            )
    return cues


def _read_bytes(path: Path, limit: int) -> bytes:
    try:
        with path.open("rb") as stream:
            content = stream.read(limit + 1)
    except OSError as exc:
        raise _error("CONTEXT_READ", f"Cannot read input: {exc.strerror}", path=path) from exc
    if len(content) > limit:
        raise _error("CONTEXT_LIMIT", "Input grew beyond its bounded byte limit while reading", path=path)
    return content


def _asset_checksum(path: Path, size: int) -> tuple[str, str]:
    """Hash small assets fully; fingerprint large media with bounded head/tail reads."""
    if size <= MAX_ASSET_SAMPLE_BYTES:
        return hashlib.sha256(_read_bytes(path, MAX_ASSET_SAMPLE_BYTES)).hexdigest(), "sha256"
    try:
        with path.open("rb") as stream:
            start = stream.read(MAX_ASSET_SAMPLE_BYTES // 2)
            stream.seek(max(0, size - MAX_ASSET_SAMPLE_BYTES // 2))
            end = stream.read(MAX_ASSET_SAMPLE_BYTES // 2)
    except OSError as exc:
        raise _error("CONTEXT_READ", f"Cannot fingerprint asset: {exc.strerror}", path=path) from exc
    digest = hashlib.sha256(str(size).encode() + b"\0" + start + end).hexdigest()
    return digest, "sha256-head-tail"


def _source_order(source: dict[str, Any]) -> tuple[int, int, str]:
    path = Path(source["path"])
    name = path.name.lower()
    priority = 0 if name == "cue-per-word.srt" else 1 if name == "normal-subtitle.srt" else 2
    return priority, len(path.parts), source["path"]


def read_project_context(
    root: str | Path = ".",
    *,
    paths: Iterable[str | Path] | str | Path | None = None,
    max_chars: int = 24000,
) -> dict[str, Any]:
    """Discover project narration, complete source timing, and reusable local assets.

    Word cues take timing precedence over sentence subtitles. ``voiceover.md``,
    ``voicover.md``, and ``narration.md`` take readable-text precedence, in that
    order. Hidden/vendor/build/output trees are never read, even through links.
    ``paths`` optionally narrows discovery to project-contained files/directories.

    The fingerprint changes with discovered paths, file metadata, and checksums;
    large binary assets use explicitly labelled head/tail checksums plus metadata.
    No cache is trusted here: each call inventories the current inputs so new
    fonts, icons, and future asset types are detected automatically.
    """
    if isinstance(max_chars, bool) or not isinstance(max_chars, int) or not 0 <= max_chars <= MAX_CHARS:
        raise _error("CONTEXT_LIMIT", f"max_chars must be an integer from 0 through {MAX_CHARS}")
    try:
        project_root = Path(root).resolve(strict=True)
    except (TypeError, ValueError, OSError, RuntimeError) as exc:
        raise _error("CONTEXT_ROOT", "Project root must be an existing directory", path=str(root)) from exc
    if not project_root.is_dir():
        raise _error("CONTEXT_ROOT", "Project root must be a directory", path=project_root)
    warnings: list[str] = []
    inventory = _inventory(project_root, paths, warnings)
    sources, assets, signatures = [], [], []
    contents: dict[str, str] = {}
    tracks: dict[str, list[dict[str, Any]]] = {}
    total_text_bytes = 0
    truncated = False
    # Preserve timing and narration before spending the bounded byte budget on supplements.
    inventory.sort(
        key=lambda path: (
            _kind(path) not in {"word-subtitles", "subtitles", "narration"},
            path.relative_to(project_root).as_posix(),
        )
    )
    for path in inventory:
        relative = path.relative_to(project_root).as_posix()
        real = _contained(project_root, path)
        if not _allowed(real.relative_to(project_root)):
            raise _error("CONTEXT_PATH", "Input link points into an excluded tree", path=relative)
        try:
            stat = path.stat()
        except OSError as exc:
            raise _error("CONTEXT_READ", f"Cannot stat input: {exc.strerror}", path=relative) from exc
        kind = _kind(path)
        source = {"path": relative, "kind": kind, "size": stat.st_size}
        if kind in {"word-subtitles", "subtitles", "narration", "data", "text", "code"}:
            if stat.st_size > MAX_TEXT_FILE_BYTES or total_text_bytes + stat.st_size > MAX_TEXT_BYTES:
                if kind in {"word-subtitles", "subtitles", "narration"}:
                    raise _error(
                        "CONTEXT_LIMIT",
                        "Narration/subtitles exceed the safe text byte budget",
                        path=relative,
                        fix="Split narration into chapter projects or select the intended source files with paths=[...]",
                    )
                checksum, algorithm = _asset_checksum(path, stat.st_size)
                source.update(checksum=checksum, checksum_algorithm=algorithm, text_truncated=True)
                warnings.append(f"Text byte budget exceeded; source reference retained: {relative}")
                truncated = True
            else:
                raw = _read_bytes(path, min(MAX_TEXT_FILE_BYTES, MAX_TEXT_BYTES - total_text_bytes))
                total_text_bytes += len(raw)
                try:
                    content = raw.decode("utf-8-sig")
                except UnicodeDecodeError as exc:
                    raise _error(
                        "CONTEXT_ENCODING",
                        f"Input is not UTF-8 near byte {exc.start}",
                        path=relative,
                        fix="Save narration and supplement text as UTF-8, or exclude it with paths=[...]",
                    ) from exc
                source.update(checksum=hashlib.sha256(raw).hexdigest(), checksum_algorithm="sha256")
                contents[relative] = content
                if kind in {"word-subtitles", "subtitles"}:
                    track = _parse_srt(content, relative)
                    tracks[relative] = track
                    source.update(cue_count=len(track), duration=max(cue["end"] for cue in track))
            sources.append(source)
        else:
            checksum, algorithm = _asset_checksum(path, stat.st_size)
            source.update(checksum=checksum, checksum_algorithm=algorithm)
            assets.append(source)
        signatures.append(
            {
                **source,
                "mtime_ns": stat.st_mtime_ns,
                "ctime_ns": stat.st_ctime_ns,
                "target": real.relative_to(project_root).as_posix(),
            }
        )
    sources.sort(key=lambda source: source["path"])
    assets.sort(key=lambda source: source["path"])
    subtitle_sources = sorted((source for source in sources if source["path"] in tracks), key=_source_order)
    timing_source = subtitle_sources[0]["path"] if subtitle_sources else None
    cues = tracks[timing_source] if timing_source else []
    if len(subtitle_sources) > 1:
        warnings.append(f"Timing authority: {timing_source}; other subtitle clocks were retained as source references")
    if any(cue["start"] < previous["end"] for previous, cue in pairwise(cues)):
        warnings.append("Source subtitle overlaps preserved without retiming")
    narration_sources = sorted(
        (source for source in sources if source["kind"] == "narration"),
        key=lambda source: (
            _NARRATION[Path(source["path"]).name.lower()],
            len(Path(source["path"]).parts),
            source["path"],
        ),
    )
    narration_source = narration_sources[0]["path"] if narration_sources else None
    sentence_sources = [source for source in subtitle_sources if source["kind"] == "subtitles"]
    fallback = tracks[sentence_sources[0]["path"]] if sentence_sources else cues
    narration = contents[narration_source] if narration_source else " ".join(cue["text"] for cue in fallback)
    narration_text = narration[:max_chars]
    remaining = max_chars - len(narration_text)
    if len(narration_text) < len(narration):
        warnings.append(
            "Narration excerpt truncated by max_chars; full source references and authoritative cues retained"
        )
        truncated = True
    for source in sorted(sources, key=lambda item: (item["kind"] != "narration", item["path"])):
        content = contents.get(source["path"])
        if content is None or source["path"] in tracks:
            continue
        if source["path"] == narration_source:
            source.update(text_ref="narration_text", text_truncated=len(narration_text) < len(content))
            continue
        source["text"] = content[:remaining]
        remaining -= len(source["text"])
        source["text_truncated"] = len(source["text"]) < len(content)
        if source["text_truncated"]:
            truncated = True
    if truncated and not any("max_chars" in warning for warning in warnings):
        warnings.append("Supplement excerpts truncated by max_chars; source references and checksums retained")
    if not cues:
        warnings.append("No SRT timing source found; supply cue-per-word.srt or normal-subtitle.srt for timed beats")
    fingerprint = hashlib.sha256(
        json.dumps(
            {"schema_version": SCHEMA_VERSION, "files": sorted(signatures, key=lambda item: item["path"])},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode()
    ).hexdigest()
    return {
        "schema_version": SCHEMA_VERSION,
        "fingerprint": fingerprint,
        "timing_source": timing_source,
        "duration": max((cue["end"] for cue in cues), default=0.0),
        "sources": sources,
        "narration_source": narration_source,
        "narration_text": narration_text,
        "cues": cues,
        "assets": assets,
        "warnings": warnings,
        "truncated": truncated,
        "limits": {
            "max_chars": max_chars,
            "max_files": MAX_FILES,
            "max_cues": MAX_CUES,
            "cue_clock_exempt_from_text_budget": True,
        },
    }
