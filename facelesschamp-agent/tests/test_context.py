import json

import pytest

from facelesschamp_agent.context import read_project_context
from facelesschamp_agent.errors import AgentError


def write(tmp_path, path, text):
    target = tmp_path / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def test_word_clock_authority_preserves_indices_and_overlaps(tmp_path):
    write(tmp_path, "normal-subtitle.srt", "9\n00:00:00,000 --> 00:00:09,000\nSentence timing.\n")
    write(
        tmp_path,
        "cue-per-word.srt",
        "41\n00:00:00,123 --> 00:00:00,501\nFirst\n\n47\n00:00:00,500 --> 00:00:01,234\nword.\n",
    )
    write(tmp_path, "voiceover.md", "Authoritative readable narration")
    result = read_project_context(tmp_path)
    assert result["timing_source"] == "cue-per-word.srt"
    assert result["duration"] == 1.234
    assert [(cue["index"], cue["start"], cue["end"]) for cue in result["cues"]] == [
        (41, 0.123, 0.501),
        (47, 0.500, 1.234),
    ]
    assert result["cues"][1]["id"] == "cue-per-word.srt#47"
    assert result["narration_text"] == "Authoritative readable narration"
    assert any("overlaps preserved" in warning for warning in result["warnings"])
    json.dumps(result, allow_nan=False)


def test_readable_narration_aliases_and_subtitle_fallback(tmp_path):
    write(tmp_path, "voicover.md", "Typo filename is supported.")
    write(tmp_path, "narration.md", "Lower precedence.")
    assert read_project_context(tmp_path)["narration_source"] == "voicover.md"
    write(tmp_path, "voiceover.md", "Preferred narration.")
    assert read_project_context(tmp_path)["narration_source"] == "voiceover.md"
    for path in tmp_path.glob("*.md"):
        path.unlink()
    write(tmp_path, "normal-subtitle.srt", "7\n00:00:02,000 --> 00:00:04,500\nSentence one.\n")
    result = read_project_context(tmp_path)
    assert result["narration_text"] == "Sentence one."
    assert result["duration"] == 4.5


def test_inventory_discovers_supplements_and_future_assets_without_execution(tmp_path):
    write(tmp_path, "story/design.json", '{"accent":"#F18033"}')
    write(tmp_path, "scene.py", "raise RuntimeError('project code must never execute')")
    (tmp_path / "assets").mkdir()
    for name in ("custom.woff2", "glyph.svg", "new-engine-format.future", "narration.mp3"):
        (tmp_path / "assets" / name).write_bytes(b"asset bytes")
    write(tmp_path, "output/private.md", "Do not inspect")
    write(tmp_path, ".hidden/private.md", "Do not inspect")
    write(tmp_path, "vendor/private.md", "Do not inspect")
    first = read_project_context(tmp_path)
    assert {source["path"] for source in first["sources"]} == {"story/design.json", "scene.py"}
    assert {source["kind"] for source in first["assets"]} == {"font", "icon", "asset", "media"}
    assert read_project_context(tmp_path)["fingerprint"] == first["fingerprint"]
    (tmp_path / "assets" / "future-animation.foo").write_bytes(b"new")
    second = read_project_context(tmp_path)
    assert second["fingerprint"] != first["fingerprint"]
    assert len(second["assets"]) == 5
    write(tmp_path, "story/design.json", '{"accent":"#009988"}')
    assert read_project_context(tmp_path)["fingerprint"] != second["fingerprint"]


def test_prompt_budget_keeps_complete_cue_clock_and_source_refs(tmp_path):
    write(tmp_path, "voiceover.md", "Narration longer than the readable context budget.")
    write(tmp_path, "design.md", "A considered visual direction.")
    write(tmp_path, "cue-per-word.srt", "8\n00:00:04,000 --> 00:00:05,000\nComplete cue.\n")
    result = read_project_context(tmp_path, max_chars=8)
    assert result["narration_text"] == "Narratio"
    assert result["truncated"]
    assert result["cues"][0]["text"] == "Complete cue."
    assert result["cues"][0]["end"] == 5
    assert {source["path"] for source in result["sources"]} == {
        "voiceover.md",
        "design.md",
        "cue-per-word.srt",
    }
    assert sum(len(source.get("text", "")) for source in result["sources"]) + len(result["narration_text"]) <= 8
    zero = read_project_context(tmp_path, max_chars=0)
    assert zero["narration_text"] == ""
    assert zero["cues"] == result["cues"]
    assert zero["fingerprint"] == result["fingerprint"]


@pytest.mark.parametrize(
    "srt",
    [
        "",
        "bad",
        "1\n00:00:99,000 --> 00:00:01,000\nInvalid\n",
        "1\n00:00:02,000 --> 00:00:01,000\nNegative duration\n",
        "1\n00:00:00,000 --> 00:00:01,000\n",
        "1\n00:00:00,000 --> 00:00:01,000\nFirst\n\n1\n00:00:02,000 --> 00:00:03,000\nDuplicate\n",
        "1\n00:00:02,000 --> 00:00:03,000\nFirst\n\n2\n00:00:01,000 --> 00:00:02,000\nOut of order\n",
    ],
)
def test_malformed_srt_has_actionable_structured_error(tmp_path, srt):
    write(tmp_path, "cue-per-word.srt", srt)
    with pytest.raises(AgentError) as caught:
        read_project_context(tmp_path)
    diagnostic = caught.value.as_dict()
    assert diagnostic["code"] == "CONTEXT_SRT"
    assert diagnostic["path"] == "cue-per-word.srt"
    assert diagnostic["suggested_fix"]


def test_bom_crlf_and_multiline_subtitles_are_supported(tmp_path):
    (tmp_path / "normal-subtitle.srt").write_bytes(
        b"\xef\xbb\xbf12\r\n00:00:00.000 --> 00:00:01,001\r\nFirst line\r\nSecond line\r\n"
    )
    assert read_project_context(tmp_path)["cues"][0]["text"] == "First line\nSecond line"


def test_selected_paths_are_contained_and_new_files_are_discovered(tmp_path):
    write(tmp_path, "draft/voiceover.md", "A selected project")
    write(tmp_path, "unrelated.txt", "Not selected")
    first = read_project_context(tmp_path, paths=["draft"])
    assert [source["path"] for source in first["sources"]] == ["draft/voiceover.md"]
    write(tmp_path, "draft/notes.md", "Future project supplement")
    assert read_project_context(tmp_path, paths=["draft"])["fingerprint"] != first["fingerprint"]
    with pytest.raises(AgentError, match="CONTEXT_PATH"):
        read_project_context(tmp_path, paths=["../outside.txt"])


def test_external_and_excluded_symlinks_are_never_read(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    outside = write(tmp_path, "secret.md", "Outside the root")
    (project / "linked.md").symlink_to(outside)
    with pytest.raises(AgentError, match="CONTEXT_PATH"):
        read_project_context(project)
    (project / "linked.md").unlink()
    write(project, ".secret/private.md", "Excluded content")
    (project / "linked").symlink_to(project / ".secret", target_is_directory=True)
    with pytest.raises(AgentError, match="CONTEXT_PATH"):
        read_project_context(project)


def test_contained_file_symlink_works_and_cycles_terminate(tmp_path):
    write(tmp_path, "notes.txt", "Safe project text")
    (tmp_path / "linked.txt").symlink_to(tmp_path / "notes.txt")
    (tmp_path / "cycle").symlink_to(tmp_path, target_is_directory=True)
    assert len(read_project_context(tmp_path)["sources"]) == 2


def test_invalid_utf8_is_structured_and_binary_assets_are_sampled(tmp_path, monkeypatch):
    from facelesschamp_agent import context

    (tmp_path / "notes.md").write_bytes(b"bad \xff")
    with pytest.raises(AgentError, match="CONTEXT_ENCODING"):
        read_project_context(tmp_path)
    (tmp_path / "notes.md").unlink()
    monkeypatch.setattr(context, "MAX_ASSET_SAMPLE_BYTES", 8)
    (tmp_path / "large.mp4").write_bytes(b"A" * 100)
    result = read_project_context(tmp_path)
    assert result["assets"][0]["checksum_algorithm"] == "sha256-head-tail"
    assert result["assets"][0]["size"] == 100


def test_byte_and_inventory_limits_are_explicit(tmp_path, monkeypatch):
    from facelesschamp_agent import context

    monkeypatch.setattr(context, "MAX_TEXT_FILE_BYTES", 12)
    write(tmp_path, "notes.md", "Supplement beyond byte limit")
    result = read_project_context(tmp_path)
    assert result["truncated"] and result["sources"][0]["text_truncated"]
    assert result["sources"][0]["path"] == "notes.md"
    write(tmp_path, "voiceover.md", "Narration beyond byte limit")
    with pytest.raises(AgentError, match="CONTEXT_LIMIT"):
        read_project_context(tmp_path)
    (tmp_path / "voiceover.md").unlink()
    monkeypatch.setattr(context, "MAX_FILES", 1)
    write(tmp_path, "second.txt", "two")
    with pytest.raises(AgentError, match="CONTEXT_LIMIT"):
        read_project_context(tmp_path)


@pytest.mark.parametrize("budget", [-1, True, 1.1, 1_000_001, "100"])
def test_invalid_prompt_budgets_are_rejected(tmp_path, budget):
    with pytest.raises(AgentError, match="CONTEXT_LIMIT"):
        read_project_context(tmp_path, max_chars=budget)
