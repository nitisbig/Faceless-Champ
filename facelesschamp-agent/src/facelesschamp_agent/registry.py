"""Offline discovery from installed public APIs and curated directing guidance."""

import importlib
import inspect
from dataclasses import asdict
from importlib.resources import files

from facelesschamp_kit.recipes import recipe_specs

from .errors import AgentError

GUIDANCE = {
    "arch": ("architecture engineering scientific geometry mesh point cloud sections dimensions",
             "Use named parts, focused camera motion and sections to explain geometry.",
             "Supply real geometry and fields; this renderer does not solve physics or create CAD.",
             "archchamp.md", ("PyVista/VTK (required)",)),
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
    "FlowCanvas": ["diagram"],
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
            "default": None if p.default is inspect.Parameter.empty else repr(p.default),
            "annotation": None if p.annotation is inspect.Parameter.empty else str(p.annotation),
        }
        for p in signature.parameters.values()
    ]


class CapabilityRegistry:
    def __init__(self):
        self._entries = {}
        groups = [
            ("faceless_champ", None),
            ("faceless_champ.web", None),
            ("faceless_champ.arch", None),
            ("faceless_champ.os_ui", None),
            ("facelesschamp_kit", None),
            ("facelesschamp_kit.blocks", None),
            ("facelesschamp_kit.layouts", ("Stack", "Split")),
            (
                "facelesschamp_kit.templates",
                ("WhiteboardScene", "whiteboard_basic", "silent", "narrated", "chesschamp", "coding_playground"),
            ),
            ("facelesschamp_kit.recipes", None),
        ]
        for module_name, names in groups:
            module = importlib.import_module(module_name)
            names = names or getattr(module, "__all__", ())
            for name in names:
                obj = getattr(module, name)
                origin = getattr(obj, "__module__", module_name)
                family = next((key for key in GUIDANCE if key != "default" and key in origin), "default")
                if name in {"CodingPlayground", "coding_playground"}:
                    family = "playground"
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
                key = f"{module_name}.{name}"
                excerpt = inspect.getdoc(obj) or use
                self._entries[key] = {
                    "id": key,
                    "name": name,
                    "import_path": key,
                    "kind": "api",
                    "family": family,
                    "parameters": _parameters(obj),
                    "named_targets": CHILDREN.get(name, []) if module_name.startswith("facelesschamp_kit") else [],
                    "dependencies": list(extras),
                    "preparation": "explicit" if family in {"web", "playground"} else "none",
                    "tags": tags.split(),
                    "use_when": use,
                    "avoid": avoid,
                    "documentation": doc_path,
                    "excerpt": excerpt[:3500],
                    "example": f"from {module_name} import {name}",
                    "example_kind": "import; see bundled guide for complete authoring",
                }
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
                "thumbnail": f"previews/{spec.id}.png",
                "motion_preview": f"previews/{spec.id}.mp4",
                "parameters": list(spec.fields),
                "example": asdict(spec)["example"],
                "example_kind": "apply_recipe content",
            }

    def search(self, query="", *, kind=None):
        terms = query.lower().split()
        records = [r for r in self._entries.values() if kind is None or r["kind"] == kind]

        def score(record):
            text = " ".join(str(record.get(k, "")) for k in ("id", "name", "tags", "use_when", "family")).lower()
            return sum(1 for term in terms if term in text)

        return sorted((r.copy() for r in records if not terms or score(r)), key=lambda r: (-score(r), r["id"]))

    def describe(self, name):
        matches = [r for r in self._entries.values() if name in {r["id"], r["name"]}]
        if len(matches) != 1:
            raise AgentError("CAPABILITY_ID", "Use a unique fully qualified ID", candidates=[r["id"] for r in matches])
        result = matches[0].copy()
        resource = files("facelesschamp_agent").joinpath("resources", result["documentation"])
        if resource.is_file():
            result["guide"] = resource.read_text()
        for key in ("thumbnail", "motion_preview"):
            if key in result:
                result[key] = str(files("facelesschamp_agent").joinpath("resources", result[key]))
        return result

    def check(self):
        for entry in self._entries.values():
            module, symbol = entry["import_path"].rsplit(".", 1)
            getattr(importlib.import_module(module), symbol)
        return {"ok": True, "count": len(self._entries)}
