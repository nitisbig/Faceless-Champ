"""Immutable, verified PNG-sequence descriptors with Pillow-only playback."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageOps


def _digest(record):
    return hashlib.sha256(
        json.dumps(record, sort_keys=True, allow_nan=False, separators=(",", ":")).encode()
    ).hexdigest()


def _file_digest(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024**2), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True, init=False)
class PreparedFrameSource:
    """A self-contained, immutable RGBA PNG sequence implementing RasterSource.

    Construction verifies the manifest and files once. Published directories must
    remain immutable; preparation refreshes publish a new directory. Sessions
    decode on demand and leave retention to the renderer's byte-bounded cache.
    """

    directory: Path
    intrinsic_size: tuple[int, int]
    duration: float
    fingerprint: str
    fps: Fraction
    _frames: tuple[tuple[str, str], ...]
    _provenance: str
    requirements = ()

    def __init__(self, directory):
        directory = Path(directory).resolve()
        try:
            record = json.loads((directory / "manifest.json").read_text())
            fingerprint = record.pop("fingerprint")
            if (
                type(record["schema_version"]) is not int
                or record["schema_version"] != 1
                or record["kind"] != "rgba-png-sequence"
            ):
                raise ValueError("Unsupported prepared-frame format")
            if fingerprint != _digest(record):
                raise ValueError("Prepared manifest fingerprint mismatch")
            size = tuple(record["size"])
            if len(size) != 2 or any(type(v) is not int or v < 1 for v in size):
                raise ValueError("Invalid prepared-frame dimensions")
            fps = Fraction(record["fps"])
            if fps <= 0:
                raise ValueError("Invalid prepared-frame rate")
            frames = record["frames"]
            if (
                not isinstance(frames, list)
                or not frames
                or type(record["frame_count"]) is not int
                or record["frame_count"] != len(frames)
            ):
                raise ValueError("Invalid prepared-frame inventory")
            duration = float(len(frames) / fps)
            if not math.isfinite(duration) or duration <= 0:
                raise ValueError("Invalid prepared-frame duration")
            from PIL import Image

            for index, frame in enumerate(frames):
                if frame["path"] != f"frames/{index:08d}.png":
                    raise ValueError("Expected contiguous, contained PNG frame paths")
                path = (directory / frame["path"]).resolve()
                if not path.is_relative_to(directory) or _file_digest(path) != frame["sha256"]:
                    raise ValueError(f"Missing, escaping or corrupt frame {index}")
                with Image.open(path) as image:
                    if image.format != "PNG" or image.mode != "RGBA" or image.size != size:
                        raise ValueError(f"Invalid RGBA PNG frame {index}")
                    image.verify()
            provenance = json.dumps(record.get("provenance", {}), sort_keys=True, allow_nan=False)
        except (OSError, ValueError, TypeError, KeyError, ZeroDivisionError, OverflowError) as exc:
            raise ValueError(f"Invalid prepared frames at {directory}: {exc}") from exc
        for name, value in {
            "directory": directory,
            "intrinsic_size": size,
            "duration": duration,
            "fingerprint": fingerprint,
            "fps": fps,
            "_frames": tuple((frame["path"], frame["sha256"]) for frame in frames),
            "_provenance": provenance,
        }.items():
            object.__setattr__(self, name, value)

    @property
    def provenance(self):
        return json.loads(self._provenance)

    @property
    def frame_count(self):
        return len(self._frames)

    def _index(self, source_time):
        if isinstance(source_time, bool) or not isinstance(source_time, (int, float)) or not math.isfinite(source_time):
            raise ValueError("Source time must be finite seconds")
        if source_time >= self.duration:
            return len(self._frames) - 1
        return min(len(self._frames) - 1, math.floor(max(0, source_time) * self.fps + 1e-9))

    def frame_key(self, source_time):
        return self._frames[self._index(source_time)][1]

    def open(self, size):
        if not isinstance(size, tuple) or len(size) != 2 or any(type(v) is not int or v < 1 for v in size):
            raise ValueError("Sampling size must be two positive integers")
        return _FrameSession(self, size)

    def __deepcopy__(self, memo):
        return self


class _FrameSession:
    def __init__(self, source, size):
        self.source, self.size, self.closed = source, size, False

    def frame(self, source_time):
        if self.closed:
            raise RuntimeError("Prepared frame session is closed")
        path = self.source.directory / self.source._frames[self.source._index(source_time)][0]
        with Image.open(path) as image:
            fitted = ImageOps.contain(image, self.size, Image.Resampling.LANCZOS)
            result = Image.new("RGBA", self.size)
            result.alpha_composite(fitted, ((self.size[0] - fitted.width) // 2, (self.size[1] - fitted.height) // 2))
            return result

    def close(self):
        self.closed = True


def _write_manifest(directory, *, size, fps, provenance):
    """Publish metadata inside a private staging directory, then verify it."""
    directory = Path(directory)
    paths = sorted((directory / "frames").glob("*.png"))
    record = {
        "schema_version": 1,
        "kind": "rgba-png-sequence",
        "size": list(size),
        "fps": str(Fraction(fps)),
        "frame_count": len(paths),
        "frames": [{"path": str(path.relative_to(directory)), "sha256": _file_digest(path)} for path in paths],
        "provenance": provenance,
    }
    record["fingerprint"] = _digest(record)
    (directory / "manifest.json").write_text(json.dumps(record, sort_keys=True, allow_nan=False))
    return PreparedFrameSource(directory)
