"""Check inline API documentation without rendering or publishing demo artifacts."""

import ast
import json
import re
import tomllib
from pathlib import Path
from urllib.parse import unquote, urlsplit

REPO = Path(__file__).resolve().parents[2]
DIST = REPO / "website/dist"


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def main():
    content = json.loads((DIST / "content.json").read_text())
    lessons = {lesson["id"]: lesson for lesson in content["lessons"]}
    assert len(lessons) == len(content["lessons"])
    snippets, links = 0, 0
    for key, guide in content["guides"].items():
        page = (DIST / guide["file"]).read_text()
        assert f'data-guide="{key}"' in page
        manifest = REPO / ("pyproject.toml" if key == "core" else "facelesschamp-kit/pyproject.toml")
        assert guide["version"] == tomllib.loads(manifest.read_text())["project"]["version"]
        assert lessons[guide["home"]]["guide"] == key
    for lesson in lessons.values():
        assert lesson["preview"] is None, "Retired previews must not be advertised"
        sections = [slug(section["title"]) for section in lesson["sections"]]
        assert len(sections) == len(set(sections))
        for section in lesson["sections"]:
            for block in section["blocks"]:
                if block["type"] == "code":
                    assert not block.get("downloadable"), "Legacy downloads must not be published"
                    if block["language"] == "python":
                        compile(ast.parse(block["code"]), lesson["id"], "exec")
                        snippets += 1
                if block["type"] != "link":
                    continue
                parts = urlsplit(block["href"])
                if parts.scheme:
                    continue
                guide = lesson["guide"]
                if parts.path:
                    assert (DIST / unquote(parts.path)).is_file(), block["href"]
                    guide = next((name for name, item in content["guides"].items() if item["file"] == parts.path), None)
                if parts.fragment:
                    chapter, _, subsection = parts.fragment.partition("/")
                    assert chapter in lessons and lessons[chapter]["guide"] == guide, block["href"]
                    if subsection:
                        assert subsection in {slug(item["title"]) for item in lessons[chapter]["sections"]}
                links += 1
    assert not (DIST / "examples").exists()
    print(
        json.dumps(
            {
                "chapters": len(lessons),
                "python_snippets": snippets,
                "links_checked": links,
                "legacy_downloads": 0,
                "media_rendered": False,
                "full_export_verified": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
