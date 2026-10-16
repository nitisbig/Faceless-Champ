"""Conservative default selection and project-owned coding tutorial styles."""

import re
from importlib.resources import files
from pathlib import Path

from facelesschamp_kit import CodingTutorialStyle, CodingTutorialTemplate

from .errors import AgentError

TEMPLATE_ID = "coding-tutorial"
TEMPLATE_FOLDER = Path("templates/coding-tutorial")
_CODING = re.compile(
    r"\b(?:cod(?:e|ing)|programming|python|javascript|typescript|java|rust|c\+\+|syntax)(?!\w)", re.IGNORECASE
)
_DESIGN = re.compile(
    r"\b(?:design(?! patterns)|style|palette|theme|font|background|bg[-_ ]?color|accent|colou?r|dark|light|whiteboard|"
    r"full[- ]?screen|custom|no (?:text|titles?|captions?|headings?|overlays?))\b",
    re.IGNORECASE,
)


def default_coding_template(*, root, prompt, context, instructions, design, project_design, constraints, format):
    """Only an uncustomized coding request may acquire this default design."""
    from .scaffold import INITIAL_PLAN

    if design is not None or instructions or constraints or format != "landscape" or _DESIGN.search(prompt):
        return False
    starter = INITIAL_PLAN.design.model_dump(mode="json")
    legacy_starter = {key: value for key, value in starter.items() if key != "template"}
    if (
        project_design
        and project_design.get("template") != TEMPLATE_ID
        and project_design not in (starter, legacy_starter)
    ):
        return False
    if any(
        (Path(root) / name).exists()
        for name in (
            "design.json",
            "design.md",
            "instructions.md",
            "instructions.txt",
            "style.md",
            "style.json",
        )
    ):
        return False
    if any(
        Path(source.get("path", "")).name.lower()
        in {
            "design.json",
            "design.md",
            "instructions.md",
            "instructions.txt",
            "style.md",
        }
        for source in context.get("sources", [])
    ):
        return False
    return bool(_CODING.search(prompt + " " + context.get("narration_text", "")))


def _folder(root):
    root = Path(root).resolve()
    folder = root / TEMPLATE_FOLDER
    if not folder.resolve().is_relative_to(root):
        raise AgentError("TEMPLATE_PATH", "Template folder must remain inside the project", path=str(folder))
    return folder


def load_coding_tutorial(root="."):
    """Reload the project's editable JSON style, falling back to the bundled default."""
    folder = _folder(root)
    path = folder / "style.json"
    if path.is_symlink() or (path.exists() and not path.resolve().is_relative_to(Path(root).resolve())):
        raise AgentError("TEMPLATE_PATH", "Template style must be a project-owned file", path=str(path))
    return CodingTutorialTemplate(CodingTutorialStyle.load(path if path.exists() else None))


def install_coding_tutorial(root="."):
    """Copy the editable design pack once; never overwrite project customizations."""
    folder = _folder(root)
    folder.mkdir(parents=True, exist_ok=True)
    resource = files("facelesschamp_kit.tutorials.coding")
    for name in ("style.json", "TEMPLATE.md"):
        target = folder / name
        if target.is_symlink():
            raise AgentError("TEMPLATE_PATH", "Refusing a symbolic-link template file", path=str(target))
        if not target.exists():
            with target.open("x", encoding="utf-8") as stream:
                stream.write(resource.joinpath(name).read_text(encoding="utf-8"))
    load_coding_tutorial(root)
    return {
        "id": TEMPLATE_ID,
        "folder": str(folder),
        "style": str(folder / "style.json"),
        "guide": str(folder / "TEMPLATE.md"),
    }


def coding_template_guidance(style):
    return {
        "id": TEMPLATE_ID,
        "style": str(TEMPLATE_FOLDER / "style.json"),
        "guide": str(TEMPLATE_FOLDER / "TEMPLATE.md"),
        "style_values": style.to_dict(),
        "factory": "facelesschamp_agent.load_coding_tutorial",
        "usage": "Read TEMPLATE.md, load the project style, author lesson-specific content and exact cue timing",
        "text": "Source code, filenames, essential OS labels and output only; no headings or captions by default",
    }
