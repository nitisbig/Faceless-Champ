"""Offline discovery from installed public APIs and curated directing guidance."""

import ast
import hashlib
import importlib
import inspect
import json
import re
import sys
from collections import Counter
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import asdict
from functools import lru_cache
from importlib.resources import files
from pathlib import Path

from facelesschamp_kit.recipes import recipe_specs

from .errors import AgentError

GUIDANCE = {
    "gpu": (
        "gpu moderngl cinematic bloom glow blur particles shaders procedural transitions lighting",
        "Select moderngl explicitly or auto for capability-aware fallback; use antialias=1 in GPU profiles.",
        "Hardware availability requires doctor --gpu. Built-ins have CPU equivalents; software EGL is not GPU evidence.",
        "moderngl.md",
        ("gpu (optional; install facelesschamp-agent[gpu])",),
    ),
    "skia": (
        "premium graphics vector bezier gradients typography masks shadows native rendering",
        "Use backend='skia' with antialias=1; native typography and retained surfaces are explicit opt-ins.",
        "CPU raster only. Existing specialist clips remain raster adapters; native text and PathMask require Skia.",
        "skia.md",
        ("skia (optional; install facelesschamp-agent[skia])",),
    ),
    "arch": (
        "architecture engineering scientific geometry mesh point cloud sections dimensions",
        "Use named parts, focused camera motion and sections to explain geometry.",
        "Supply real geometry and fields; this renderer does not solve physics or create CAD.",
        "archchamp.md",
        ("PyVista/VTK (required)",),
    ),
    "flow": (
        "systems process causality request journey hierarchy networks circuits",
        "Use nodes and edges to explain relationships; follow a single request to explain movement.",
        "Use multiple scenes when labels become crowded.",
        "flowchamp.md",
        (),
    ),
    "coding": (
        "code syntax programming editor source",
        "Use an editor for source; use prepared playgrounds when output proves the explanation.",
        "Code does not wrap or execute implicitly.",
        "coding.md",
        ("coding (syntax highlighting)",),
    ),
    "playground": (
        "code output checkpoint backend web results programming",
        "Show complete code checkpoints beside explicitly bound results.",
        "Prepare explicitly; rendering replays assets without executing checkpoints.",
        "coding-playgrounds.md",
        ("playground (preparation)",),
    ),
    "chess": (
        "chess board legal moves analysis game",
        "Use legal timed game data and preserve board orientation.",
        "No engine evaluation or inferred analysis.",
        "chesschamp.md",
        ("chess",),
    ),
    "os_ui": (
        "desktop finder settings virtual files tutorial",
        "Use authored semantic actions to explain desktop workflows.",
        "The virtual desktop does not operate the user's computer.",
        "os-ui.md",
        (),
    ),
    "web": (
        "html webpage browser capture walkthrough selectors",
        "Prepare local browser captures and focus on relevant selectors.",
        "Capture is explicit and needs Playwright; playback is offline.",
        "html-to-video.md",
        ("web (capture)",),
    ),
    "charts": (
        "data comparison magnitude trends distribution proportion statistics",
        "Choose chart structure to match the data relationship and identify units and provenance.",
        "Do not invent measured values; label illustrative data.",
        "charts.md",
        (),
    ),
    "maps": (
        "geography country earth globe map location",
        "Use geography when location or spatial scale explains the claim.",
        "Preserve geographic context and distinguish schematic imagery.",
        "maps.md",
        ("maps",),
    ),
    "default": (
        "composition layout timing animation text image audio",
        "Measure layout, keep one focal subject, and animate a meaningful change.",
        "Use kit recipes for common explanations; inspect motion as well as stills.",
        "api.md",
        (),
    ),
}
CHILDREN = {
    "Heading": ["text"],
    "TextPanel": ["background", "text", "title (when supplied)"],
    "MetricCard": ["background", "value", "label"],
    "ImageCard": ["background", "image", "label (when supplied)"],
    "Comparison": ["0", "1"],
    "StepList": ["0..N"],
    "FlowDiagram": ["node-N", "label-N", "edge-N"],
    "FlowCanvas": ["diagram", "glow (with design)"],
    "FlowCard": ["surface", "label", "icon", "detail (when supplied)", "address (when supplied)"],
    "FlowPopup": ["surface", "icon", "kind", "value"],
    "FlowBackdrop": ["background"],
    "ArchCanvas": ["model"],
    "CodeEditor": ["editor"],
    "CodingPlayground": ["editor", "canvas", "output (when enabled)"],
    "ChessBoard": ["board"],
    "OSWalkthrough": ["ui"],
    "FinderWindow": ["ui"],
    "SettingsWindow": ["ui"],
    "WebWalkthrough": ["page", "chrome/title (when enabled)"],
    "WebElement": ["element"],
    "WhiteboardDrawing": ["stroke-N"],
    "Stack": ["0..N"],
    "Split": ["0..N"],
}
_SEARCH_WEIGHTS = (
    ("name", 12),
    ("category", 8),
    ("family", 7),
    ("tags", 4),
    ("use_when", 3),
    ("id", 2),
    ("excerpt", 1),
)


def _default_repr(value):
    """Keep useful defaults without process-specific object addresses in catalog identities."""
    if inspect.isroutine(value) or inspect.isclass(value):
        name = getattr(value, "__qualname__", getattr(value, "__name__", None))
        if name:
            module = getattr(value, "__module__", None)
            return f"{module}.{name}" if module else name
    rendered = repr(value)
    if isinstance(value, str):
        return rendered
    return re.sub(r"(<[^<>]*?) at 0x[0-9a-fA-F]+(?=>)", r"\1", rendered)


def _parameters(obj):
    try:
        signature = inspect.signature(obj)
    except (TypeError, ValueError):
        return []
    return [
        {
            "name": p.name,
            "kind": p.kind.name,
            "required": p.default is inspect.Parameter.empty and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD),
            "default": None if p.default is inspect.Parameter.empty else _default_repr(p.default),
            "annotation": None if p.annotation is inspect.Parameter.empty else str(p.annotation),
        }
        for p in signature.parameters.values()
    ]


@lru_cache(maxsize=512)
def _source_tree(path, modified, size):
    """Cache parsing, but invalidate it when an installed source changes."""
    del modified, size
    try:
        return ast.parse(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, SyntaxError):
        return None


def _tree(path):
    stat = path.stat()
    return _source_tree(str(path), stat.st_mtime_ns, stat.st_size)


def _literal(node, namespace=None):
    """Evaluate data declarations only; never run package or project code."""
    if isinstance(node, ast.Name):
        return (namespace or {}).get(node.id)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _literal(node.left, namespace), _literal(node.right, namespace)
        if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
            return [*left, *right]
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        return None


def _public_names(tree):
    namespace = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    namespace[target.id] = _literal(node.value, namespace)
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            name = node.target.id
            value = _literal(node.value, namespace)
            if isinstance(namespace.get(name), (list, tuple)) and isinstance(value, (list, tuple)):
                namespace[name] = [*namespace[name], *value]
    declared = namespace.get("__all__")
    if isinstance(declared, (list, tuple)):
        return tuple(name for name in declared if isinstance(name, str) and not name.startswith("_"))
    return tuple(
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_")
    )


def _public_modules(package):
    """Inspect Python packages, excluding resource/sample directories and private modules."""
    for root_text in package.__path__:
        root = Path(root_text)
        for path in sorted(root.rglob("*.py")):
            relative = path.relative_to(root)
            if any(part.startswith("_") for part in relative.parts[:-1]):
                continue
            if path.stem.startswith("_") and path.name != "__init__.py":
                continue
            if any(
                not (root.joinpath(*relative.parts[:i]) / "__init__.py").is_file()
                for i in range(1, len(relative.parts))
            ):
                continue
            parts = list(relative.with_suffix("").parts)
            if parts[-1] == "__init__":
                parts.pop()
            module_name = ".".join([package.__name__, *parts])
            tree = _tree(path)
            if tree is not None:
                yield module_name, path, tree


def _root_import_closure(roots, modules):
    """Choose runtime metadata from a deterministic public-root import graph.

    Unrelated CLI/project imports must not turn optional source entries into
    runtime entries or create extra aliases for imported preset registries.
    Only unconditional top-level imports are followed; no module is executed.
    """
    pending, result = list(roots), set()
    while pending:
        module_name = pending.pop()
        if module_name in result or module_name not in modules:
            continue
        result.add(module_name)
        path, tree = modules[module_name]
        package_name = module_name if path.name == "__init__.py" else module_name.rpartition(".")[0]
        for node in tree.body:
            imported = []
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = importlib.util.resolve_name("." * node.level + (node.module or ""), package_name)
                imported = [base, *(f"{base}.{alias.name}" for alias in node.names)]
            for name in imported:
                parts = name.split(".")
                pending.extend(".".join(parts[:index]) for index in range(1, len(parts) + 1))
    return result


def _static_definition(module_name, name, modules, seen=None):
    seen = set() if seen is None else seen
    if (module_name, name) in seen or module_name not in modules:
        return None
    seen.add((module_name, name))
    path, tree = modules[module_name]
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return module_name, node
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if (alias.asname or alias.name) == name:
                    package_name = module_name if path.name == "__init__.py" else module_name.rpartition(".")[0]
                    imported = importlib.util.resolve_name("." * node.level + (node.module or ""), package_name)
                    return _static_definition(imported, alias.name, modules, seen)
    return None


def _static_parameters(node):
    if isinstance(node, ast.ClassDef):
        node = next((item for item in node.body if isinstance(item, ast.FunctionDef) and item.name == "__init__"), None)
    if node is None:
        return []
    arguments = node.args
    positional = [*arguments.posonlyargs, *arguments.args]
    defaults = [None] * (len(positional) - len(arguments.defaults)) + list(arguments.defaults)
    pairs = [
        (arg, default, "POSITIONAL_ONLY" if i < len(arguments.posonlyargs) else "POSITIONAL_OR_KEYWORD")
        for i, (arg, default) in enumerate(zip(positional, defaults))
    ]
    if arguments.vararg:
        pairs.append((arguments.vararg, None, "VAR_POSITIONAL"))
    pairs.extend((arg, default, "KEYWORD_ONLY") for arg, default in zip(arguments.kwonlyargs, arguments.kw_defaults))
    if arguments.kwarg:
        pairs.append((arguments.kwarg, None, "VAR_KEYWORD"))
    return [
        {
            "name": arg.arg,
            "kind": kind,
            "required": default is None and kind not in {"VAR_POSITIONAL", "VAR_KEYWORD"},
            "default": None if default is None else ast.unparse(default),
            "annotation": None if arg.annotation is None else ast.unparse(arg.annotation),
        }
        for arg, default, kind in pairs
        if arg.arg not in {"self", "cls"}
    ]


def _category(name, origin):
    text = f"{name} {origin}".lower()
    for category, words in (
        ("design", ("design", "theme", "style", "scheme", "palette")),
        ("transition", ("transition", "fadeout", "slideout", "wipe", "zoomout", "popout")),
        ("animation", ("animation", "spring", "scheduling", "motion")),
        ("ui", ("os_ui", "coding", "playground", "web", "window")),
        ("composition", ("layout", "timeline", "canvas", "scene", "video", "group", "block")),
        ("engine", ("renderer", "export", "champ")),
    ):
        if any(word in text for word in words):
            return category
    return "utility"


def _family(name, origin):
    if name in {
        "ModernGLRenderer",
        "GPUOptions",
        "renderer_capabilities",
        "EffectStack",
        "GaussianBlur",
        "OuterGlow",
        "Bloom",
        "Distortion",
        "ChromaticAberration",
        "LightSweep",
        "ProceduralBackground",
        "ParticleField",
        "DirectionalWipe",
        "LuminanceWipe",
        "ZoomBlurTransition",
        "EffectBlock",
        "ProceduralBackdrop",
        "ParticleBackdrop",
    }:
        return "gpu"
    if name in {"SkiaRenderer", "Surface", "VectorPath", "PathData", "PathMask", "create_renderer"}:
        return "skia"
    if name in {"CodingPlayground", "coding_playground"}:
        return "playground"
    return next((key for key in GUIDANCE if key != "default" and key in origin.lower()), "default")


def _dependency_imports(tree):
    """Surface future third-party requirements without importing or probing them."""
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            imports.add(node.module.split(".")[0])
    imports -= sys.stdlib_module_names | {"faceless_champ", "facelesschamp_kit"}
    return [f"module import: {name} (availability unverified)" for name in sorted(imports)]


def _terms(text):
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    return re.findall(r"[a-z0-9]+", text.lower())


def _limit(value):
    if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
        raise AgentError("CAPABILITY_LIMIT", "limit must be a nonnegative integer")
    return value


class CapabilityRegistry:
    """A live, offline catalog with bounded retrieval for scene planning.

    Only the two installed public package roots are imported. Other public
    modules are read as syntax, so discovery cannot execute checkpoints, sample
    projects, optional renderer imports, or module-level side effects. Reading
    a source signature is evidence of an available contract, not a successful
    optional-dependency check; records identify that distinction in ``source``.
    """

    def __init__(self):
        self._entries = {}
        self._packages = [importlib.import_module(name) for name in ("faceless_champ", "facelesschamp_kit")]
        self._versions = {package.__name__: vars(package).get("__version__", "unknown") for package in self._packages}
        self._modules = {
            name: (path, tree) for package in self._packages for name, path, tree in _public_modules(package)
        }
        runtime_modules = _root_import_closure((package.__name__ for package in self._packages), self._modules)
        self._module_dependencies = {name: _dependency_imports(tree) for name, (_, tree) in self._modules.items()}
        for module_name, (path, tree) in self._modules.items():
            module = sys.modules.get(module_name) if module_name in runtime_modules else None
            live = vars(module) if module is not None else {}
            names = live.get("__all__", _public_names(tree))
            for name in names:
                if isinstance(name, str) and not name.startswith("_"):
                    self._add_api(module_name, name, path, live)
            self._add_designs(module_name, path, tree, live)
        for package in self._packages:
            self._add_resources(package)
        for spec in recipe_specs():
            self._entries[f"recipe:{spec.id}"] = {
                **asdict(spec),
                "id": f"recipe:{spec.id}",
                "name": spec.id,
                "kind": "recipe",
                "import_path": "facelesschamp_kit.recipes.apply_recipe",
                "tags": spec.purpose.lower().split(),
                "use_when": spec.purpose,
                "named_targets": list(spec.targets),
                "dependencies": ["PyVista/VTK (required)"] if spec.id == "arch-design" else [],
                "preparation": "explicit" if spec.id == "code-result" else "none",
                "documentation": "recipes.md",
                "parameters": list(spec.fields),
                "example": asdict(spec)["example"],
                "example_kind": "apply_recipe content",
            }
            for key, extension in (("thumbnail", "png"), ("motion_preview", "mp4")):
                relative = f"previews/{spec.id}.{extension}"
                if files("facelesschamp_agent").joinpath("resources", relative).is_file():
                    self._entries[f"recipe:{spec.id}"][key] = relative
        self._index = {}
        for record in self._entries.values():
            fields = []
            for key, weight in _SEARCH_WEIGHTS:
                value = record.get(key, "")
                value = " ".join(value) if isinstance(value, list) else str(value)
                fields.append((key, weight, set(_terms(value)), value.lower()))
            self._index[record["id"]] = fields

    def _add_api(self, module_name, name, path, live):
        obj = live.get(name)
        definition = _static_definition(module_name, name, self._modules)
        origin, node = definition or (module_name, None)
        if obj is not None:
            origin = getattr(obj, "__module__", origin)
        family = _family(name, origin)
        tags, use, avoid, doc, extras = GUIDANCE[family]
        doc_path = f"docs/core/{doc}"
        if module_name.startswith("facelesschamp_kit"):
            candidate = f"docs/kit/{doc}"
            doc_path = (
                candidate
                if files("facelesschamp_agent").joinpath("resources", candidate).is_file()
                else "docs/kit/api.md"
            )
        if name == "Equation":
            extras = ("equations (Matplotlib MathText)",)
        excerpt = (inspect.getdoc(obj) if obj is not None else ast.get_docstring(node) if node else None) or use
        key = f"{module_name}.{name}"
        self._entries[key] = {
            "id": key,
            "name": name,
            "import_path": key,
            "kind": "api",
            "family": family,
            "category": _category(name, origin),
            "parameters": _parameters(obj) if callable(obj) else _static_parameters(node) if node else [],
            "named_targets": CHILDREN.get(name, []) if module_name.startswith("facelesschamp_kit") else [],
            "dependencies": list(extras) + self._module_dependencies.get(origin, []),
            "preparation": "explicit" if family in {"web", "playground"} else "none",
            "tags": sorted(set(tags.split() + _terms(name))),
            "use_when": use,
            "avoid": avoid,
            "documentation": doc_path,
            "excerpt": excerpt[:3500],
            "example": f"from {module_name} import {name}",
            "example_kind": "import; see bundled guide for complete authoring",
            "source": {
                "kind": "installed-api" if obj is not None else "installed-source",
                "module": module_name,
                "symbol": name,
                "path": str(path),
            },
        }

    def _add_designs(self, module_name, path, tree, live):
        """Find named preset contracts from mappings and class selectors, without invoking them."""
        selections = []
        for name, value in live.items():
            if not name.startswith("_") and isinstance(value, Mapping) and _category(name, "") == "design":
                selections.extend((name, str(key), "mapping") for key in value if isinstance(key, str))
        for node in tree.body:
            if isinstance(node, ast.Assign):
                value = node.value
                if isinstance(value, ast.Call) and value.args:
                    value = value.args[0]
                if isinstance(value, ast.Dict):
                    for target in node.targets:
                        if (
                            isinstance(target, ast.Name)
                            and not target.id.startswith("_")
                            and _category(target.id, "") == "design"
                        ):
                            selections.extend(
                                (target.id, key.value, "mapping")
                                for key in value.keys
                                if isinstance(key, ast.Constant) and isinstance(key.value, str)
                            )
            if not isinstance(node, ast.ClassDef) or node.name.startswith("_"):
                continue
            selector = next(
                (item for item in node.body if isinstance(item, ast.FunctionDef) and item.name == "named"), None
            )
            if selector is None:
                continue
            for comparison in (item for item in ast.walk(selector) if isinstance(item, ast.Compare)):
                if not isinstance(comparison.left, ast.Name) or comparison.left.id != "name":
                    continue
                for item in comparison.comparators:
                    value = _literal(item)
                    values = value if isinstance(value, (tuple, list, set)) else [value]
                    selections.extend((node.name, choice, "named") for choice in values if isinstance(choice, str))
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and item.target.id == "name":
                    value = _literal(item.value)
                    if isinstance(value, str):
                        selections.append((node.name, value, "named"))
        for symbol, preset, selector in sorted(set(selections)):
            key = f"design:{module_name}.{symbol}:{preset}"
            family = _family(symbol, module_name)
            tags, use, avoid, doc, extras = GUIDANCE[family]
            expression = f"{symbol}[{preset!r}]" if selector == "mapping" else f"{symbol}.named({preset!r})"
            self._entries[key] = {
                "id": key,
                "name": preset,
                "kind": "design",
                "category": "design",
                "family": family,
                "import_path": f"{module_name}.{symbol}",
                "selector": selector,
                "tags": sorted(set(tags.split() + _terms(f"{symbol} {preset}"))),
                "use_when": f"Use the installed {symbol} preset {preset!r}. {use}",
                "avoid": avoid,
                "dependencies": list(extras) + self._module_dependencies.get(module_name, []),
                "preparation": "none",
                "parameters": [],
                "named_targets": [],
                "documentation": f"docs/core/{doc}",
                "example": f"from {module_name} import {symbol}\nstyle = {expression}",
                "source": {"kind": "installed-source", "module": module_name, "symbol": symbol, "path": str(path)},
            }

    def _add_resources(self, package):
        for root_text in package.__path__:
            root = Path(root_text)
            for path in sorted(root.rglob("*")):
                relative = path.relative_to(root)
                if not path.is_file() or any(part.startswith((".", "__")) for part in relative.parts):
                    continue
                suffix = path.suffix.lower()
                if suffix in {".py", ".pyc", ".pyo"}:
                    continue
                category = "resource"
                if suffix in {".ttf", ".otf", ".woff", ".woff2"}:
                    category = "font"
                elif suffix in {".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif", ".avif"}:
                    category = "icon" if "icon" in relative.as_posix().lower() else "image"
                elif suffix in {".mp4", ".mov", ".webm"}:
                    category = "video"
                elif suffix in {".wav", ".mp3", ".m4a", ".ogg", ".flac"}:
                    category = "audio"
                elif suffix in {".srt", ".vtt"}:
                    category = "subtitle"
                elif suffix in {".json", ".csv", ".tsv"}:
                    category = "data"
                key = f"asset:{package.__name__}:{relative.as_posix()}"
                stat = path.stat()
                self._entries[key] = {
                    "id": key,
                    "name": path.stem,
                    "kind": "asset",
                    "category": category,
                    "asset_type": category,
                    "family": _family(path.stem, relative.as_posix()),
                    "import_path": None,
                    "package": package.__name__,
                    "relative_path": relative.as_posix(),
                    "path": str(path),
                    "tags": sorted(set(_terms(relative.as_posix()) + [category])),
                    "use_when": f"Reuse the installed local {category} {relative.as_posix()}.",
                    "dependencies": [],
                    "preparation": "none",
                    "parameters": [],
                    "named_targets": [],
                    "source": {"kind": "installed-resource", "size": stat.st_size, "modified_ns": stat.st_mtime_ns},
                    "example": f"from importlib.resources import files\nasset = files({package.__name__!r}).joinpath({relative.as_posix()!r})",
                }

    def _rank(self, query, kind):
        stop = {"a", "an", "the", "of", "to", "for", "and", "or", "with", "in", "on", "is", "it", "this", "that"}
        terms = sorted(set(_terms(query)) - stop)
        ranked = []
        for record in self._entries.values():
            if kind is not None and record["kind"] != kind:
                continue
            score, reasons = 0, []
            for key, weight, words, value in self._index[record["id"]]:
                matched = [term for term in terms if term in words or (len(term) >= 4 and term in value)]
                if matched:
                    score += weight * len(matched)
                    reasons.append(f"{key}: {', '.join(matched)}")
            if not terms or score:
                if terms and record["kind"] == "recipe":
                    score += 1
                ranked.append((score, record, reasons))
        return sorted(ranked, key=lambda item: (-item[0], not terms and item[1]["kind"] == "asset", item[1]["id"]))

    @staticmethod
    def _compact(record):
        keys = (
            "id",
            "name",
            "kind",
            "category",
            "family",
            "import_path",
            "asset_type",
            "preparation",
            "dependencies",
            "named_targets",
        )
        result = {key: deepcopy(record[key]) for key in keys if key in record}
        result["use_when"] = record.get("use_when", "")[:220]
        if "source" in record:
            result["evidence"] = record["source"]["kind"]
        return result

    def search(self, query="", *, kind=None, limit=None, compact=False):
        """Retrieve matching records; opt into compact bounded output, then describe selected IDs."""
        ranked = self._rank(query, kind)[: _limit(limit)]
        return [self._compact(record) if compact else deepcopy(record) for _, record, _ in ranked]

    def recommend(self, query, *, limit=5, kind=None):
        """Rank installed capabilities with explainable lexical evidence, not a claim of aesthetic quality."""
        if limit is None:
            raise AgentError("CAPABILITY_LIMIT", "recommend requires a bounded limit")
        return [
            {**self._compact(record), "score": score, "reasons": reasons or ["installed catalog order; no query terms"]}
            for score, record, reasons in self._rank(query, kind)[: _limit(limit)]
        ]

    def manifest(self):
        """Identify the current catalog so planners can reuse it until installed contracts change."""
        records = [self._entries[key] for key in sorted(self._entries)]
        encoded = json.dumps({"packages": self._versions, "entries": records}, sort_keys=True, default=str).encode()
        return {
            "schema_version": 1,
            "packages": self._versions.copy(),
            "count": len(records),
            "counts": dict(sorted(Counter(record["kind"] for record in records).items())),
            "fingerprint": hashlib.sha256(encoded).hexdigest(),
        }

    def describe(self, name):
        matches = [r for r in self._entries.values() if name in {r["id"], r["name"]}]
        if len(matches) != 1:
            raise AgentError("CAPABILITY_ID", "Use a unique fully qualified ID", candidates=[r["id"] for r in matches])
        result = deepcopy(matches[0])
        if "documentation" in result:
            resource = files("facelesschamp_agent").joinpath("resources", result["documentation"])
            if resource.is_file():
                result["guide"] = resource.read_text()
                result["guide_source"] = "bundled directing guidance; installed signature and excerpt are authoritative"
        for key in ("thumbnail", "motion_preview"):
            if key in result:
                result[key] = str(files("facelesschamp_agent").joinpath("resources", result[key]))
        return result

    def check(self):
        for entry in self._entries.values():
            if entry["kind"] == "asset":
                if not Path(entry["path"]).is_file():
                    raise AgentError("CAPABILITY_RESOURCE", "Installed resource is missing", capability=entry["id"])
                continue
            module_name, symbol = entry["import_path"].rsplit(".", 1)
            loaded = sys.modules.get(module_name)
            if loaded is not None and symbol in vars(loaded):
                continue
            if module_name in self._modules:
                _, tree = self._modules[module_name]
                assigned = {
                    target.id
                    for node in tree.body
                    if isinstance(node, ast.Assign)
                    for target in node.targets
                    if isinstance(target, ast.Name)
                }
                assigned.update(
                    node.target.id
                    for node in tree.body
                    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
                )
                assigned.update(
                    node.name
                    for node in tree.body
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                )
                assigned.update(
                    alias.asname or alias.name.split(".")[0]
                    for node in tree.body
                    if isinstance(node, (ast.Import, ast.ImportFrom))
                    for alias in node.names
                )
                if symbol in assigned:
                    continue
            raise AgentError("CAPABILITY_ID", "Installed public contract is missing", capability=entry["id"])
        return {"ok": True, "count": len(self._entries)}
