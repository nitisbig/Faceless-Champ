import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(root):
    spec = importlib.util.spec_from_file_location("tidy_repo", ROOT / "scripts" / "tidy_repo.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = root
    return module


def test_archive_moves_unreferenced_history_and_rewrites_prose_links(tmp_path, capsys):
    (tmp_path / "docs/v2").mkdir(parents=True)
    (tmp_path / "docs/decisions").mkdir()
    (tmp_path / "docs/v2/m1-implementation.md").write_text("# M1\n")
    (tmp_path / "docs/v2/api-design.md").write_text("# API design\n")
    (tmp_path / "docs/decisions/skia-backend.md").write_text("# Decision\n")
    (tmp_path / "README.md").write_text("See [docs/v2/m1-implementation.md](docs/v2/m1-implementation.md).\n")
    (tmp_path / "docs/skia.md").write_text("See [the decision](decisions/skia-backend.md#why).\n")
    (tmp_path / "tool.py").write_text('SOURCE = "docs/v2/api-design.md"\n')
    tidy = _load(tmp_path)

    moves, kept = tidy.plan()
    assert {m["from"] for m in moves} == {"docs/v2/m1-implementation.md", "docs/decisions"}
    assert kept == [{"path": "docs/v2/api-design.md", "referenced_by": ["tool.py"]}]
    assert (tmp_path / "docs/v2/m1-implementation.md").exists()  # dry run changes nothing

    assert tidy.main(["--apply"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert sorted(report["rewritten"]) == ["README.md", "docs/skia.md"]
    assert (tmp_path / "docs/archive/v2/m1-implementation.md").is_file()
    assert (tmp_path / "docs/archive/decisions/skia-backend.md").is_file()
    assert (tmp_path / "docs/v2/api-design.md").is_file()
    assert (tmp_path / "docs/archive/README.md").is_file()
    readme = (tmp_path / "README.md").read_text()
    assert readme == "See [docs/archive/v2/m1-implementation.md](docs/archive/v2/m1-implementation.md).\n"
    assert "(archive/decisions/skia-backend.md#why)" in (tmp_path / "docs/skia.md").read_text()
