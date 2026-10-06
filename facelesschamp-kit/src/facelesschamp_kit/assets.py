"""Named assets; preparation is explicit and rendering never downloads files."""

import hashlib
import json
from copy import deepcopy
from importlib.resources import files
from pathlib import Path, PurePosixPath

from .diagnostics import KitError, fields


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise KitError("ASSET_MANIFEST", f"Duplicate manifest key {key!r}")
        result[key] = value
    return result


class AssetRegistry:
    def __init__(self, root, manifest=None):
        self.root = Path(root).resolve()
        path = self.root / "assets/manifest.json"
        self.entries = (
            deepcopy(manifest)
            if manifest is not None
            else (json.loads(path.read_text(), object_pairs_hook=unique_object) if path.exists() else {})
        )
        if not isinstance(self.entries, dict):
            raise KitError("ASSET_MANIFEST", "Asset manifest must map unique IDs to entries")
        self.resolved = {}

    def resolve(self, asset_id, kind=None, mode="required"):
        if mode not in {"required", "placeholder", "auto"}:
            raise KitError("ASSET_MODE", "Use required, placeholder, or auto", asset=asset_id)
        entry = self.entries.get(asset_id)
        if entry is not None:
            fields(
                entry, {"type", "path", "package", "resource", "source", "license", "attribution", "checksum"}, asset_id
            )
            if kind and entry.get("type") != kind:
                raise KitError("ASSET_TYPE", f"Expected {kind}", asset=asset_id)
        path = None
        if entry and mode != "placeholder":
            if "package" in entry:
                resource = PurePosixPath(entry.get("resource", ""))
                if resource.is_absolute() or ".." in resource.parts or not resource.parts or "path" in entry:
                    raise KitError("ASSET_PATH", "Use a relative package resource without '..'", asset=asset_id)
                try:
                    data = files(entry["package"]).joinpath(str(resource)).read_bytes()
                except (FileNotFoundError, ModuleNotFoundError):
                    data = None
                if data is not None:
                    fingerprint = hashlib.sha256(data).hexdigest()
                    path = self.root / ".fc-kit/assets" / fingerprint / resource.name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if not path.exists() or digest(path) != fingerprint:
                        path.write_bytes(data)
            elif "path" in entry:
                path = (self.root / entry["path"]).resolve()
            else:
                raise KitError("ASSET_PATH", "Specify path or package/resource", asset=asset_id)
        if path is None or not path.is_file():
            if mode == "required" or kind not in {None, "image"}:
                raise KitError(
                    "ASSET_MISSING", "Add the asset to assets/manifest.json and supply its file", asset=asset_id
                )
            path = None
        checksum = digest(path) if path else None
        if path and entry.get("checksum") and entry["checksum"] != checksum:
            raise KitError(
                "ASSET_CHECKSUM", "Asset changed; verify it and update the manifest checksum", asset=asset_id
            )
        record = {
            "id": asset_id,
            **(entry or {}),
            "resolved_path": str(path) if path else None,
            "checksum": checksum,
            "placeholder": path is None,
        }
        self.resolved[f"{asset_id}:{mode}"] = record
        return path

    def image(self, asset_id, mode="required"):
        return self.resolve(asset_id, "image", mode)

    def audio(self, asset_id):
        return self.resolve(asset_id, "audio")

    def subtitle(self, asset_id):
        return self.resolve(asset_id, "subtitle")

    def font(self, asset_id):
        return self.resolve(asset_id, "font")
