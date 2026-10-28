import json
import shlex
from pathlib import Path

from facelesschamp_agent.cli import main
from facelesschamp_agent.project import _package_identity


def test_layout_report_is_compact_and_evidence_becomes_stale(project):
    assert project.status().layout_validation == "pending"
    result = project.audit_layout()
    assert result["status"] == "passed", result["findings"]
    assert result["design"]["ok"] and result["design"]["findings"] == [], result["design"]
    assert "sample_times" not in result and result["sample_count"] > 10
    full = json.loads(Path(result["report_path"]).read_text())
    assert len(full["sample_times"]) == result["sample_count"]
    assert project.status().layout_validation == "passed"
    path = project.root / "videos/main.py"
    path.write_text(path.read_text() + "\n# Changed scene source\n")
    assert project.status().layout_validation == "pending"


def test_layout_repair_passes_count_changed_failed_builds_only(project, monkeypatch):
    def failed(compiled, plan):
        return {
            "status": "failed",
            "sample_times": [0],
            "findings": [{"scene_id": "process", "code": "LAYOUT_OVERLAP", "source_time": 0}],
            "limitations": [],
        }

    monkeypatch.setattr("facelesschamp_agent.layout.audit_layout", failed)
    project.audit_layout()
    project.audit_layout()
    assert project.status().repair_passes == {"process": 0}
    raw = project.plan
    raw.brief.prompt = "A revised process"
    project.plan_path.write_text(raw.model_dump_json())
    project.audit_layout()
    assert project.status().repair_passes == {"process": 1}


def test_entrypoint_command_is_runnable_with_spaces(project):
    result = project.entrypoint()
    assert shlex.split(result["command"]) == ["python", result["path"]]
    assert Path(result["path"]).is_file()


def test_cli_audit_defaults_to_compact_report(project, capsys):
    assert main(["--project", str(project.root), "audit-layout"]) == 0
    record = json.loads(capsys.readouterr().out)["result"]
    assert record["sample_count"] > 10 and "sample_times" not in record
    assert main(["--project", str(project.root), "audit-layout", "--full"]) == 0
    assert json.loads(capsys.readouterr().out)["result"]["sample_times"]


def test_packaged_font_and_new_icon_updates_invalidate_identity(tmp_path):
    (tmp_path / "__init__.py").write_text("# package")
    assets = tmp_path / "assets"
    assets.mkdir()
    font = assets / "theme.ttf"
    font.write_bytes(b"original font")
    before = _package_identity(tmp_path)
    font.write_bytes(b"new font")
    changed = _package_identity(tmp_path)
    assert changed != before
    (assets / "future-icon.svg").write_text("<svg/>")
    assert _package_identity(tmp_path) != changed
    unchanged = _package_identity(tmp_path)
    cache = tmp_path / "__pycache__"
    cache.mkdir()
    (cache / "__init__.cpython-312.pyc").write_bytes(b"cache")
    assert _package_identity(tmp_path) == unchanged
