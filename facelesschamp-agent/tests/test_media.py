import math
import struct
import wave
from pathlib import Path

import pytest

from facelesschamp_agent import AgentError
from facelesschamp_agent.media import alignment, run_tool, verify_media


def write_audio(path, duration=6, *, silent_after=None):
    rate = 8000
    with wave.open(str(path), "wb") as wav:
        wav.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        samples = [
            int(
                9000
                * math.sin(2 * math.pi * (150 * i / rate + 37 * (i / rate) ** 2))
                * (0.4 + 0.6 * abs(math.sin(i / rate * 3.17)))
            )
            if silent_after is None or i / rate < silent_after
            else 0
            for i in range(round(rate * duration))
        ]
        wav.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def test_full_export_decode_and_review_remain_separate(project):
    result = project.render()
    assert result["verification"]["status"] == "passed"
    status = project.status()
    assert status.full_export_media_verification == "passed"
    assert status.visual_review == status.editorial_review == "pending"
    assert status.draft
    path = Path(result["artifacts"][0]["path"])
    path.write_bytes(path.read_bytes()[:300])
    with pytest.raises(AgentError, match="ARTIFACT_CHANGED"):
        project.verify(path)
    assert project.status().full_export_media_verification == "pending"


def test_audio_tail_preparation_preserves_source_and_cues(project):
    audio = project.root / "voice.wav"
    write_audio(audio, 5)
    before = audio.read_bytes()
    cues = project.root / "cues.srt"
    cues.write_text("7\n00:00:00,000 --> 00:00:01,001\nFirst\n\n19\n00:00:01,000 --> 00:00:06,000\nLast\n")
    plan = project.plan
    plan.brief.narration.audio = "voice.wav"
    plan.brief.narration.subtitles = "cues.srt"
    plan.brief.narration.overlap_tolerance = 0.001
    project.plan_path.write_text(plan.model_dump_json())
    with pytest.raises(ValueError, match="NARRATION_PREPARE"):
        project.validate()
    result = project.prepare()
    assert result["narration"]["derived"]
    assert audio.read_bytes() == before
    compiled, _, _ = project._build()
    assert [c["index"] for c in compiled.report["narration"]["cues"]] == [7, 19]
    assert compiled.report["narration"]["cues"][0]["end"] == 1.001
    rendered = project.render()
    assert rendered["verification"]["narration_alignment"]["status"] == "passed"
    assert not project.status().draft


def test_audio_only_alignment_and_source_invalidation(project):
    audio = project.root / "voice.wav"
    write_audio(audio)
    plan = project.plan
    plan.brief.narration.audio = "voice.wav"
    project.plan_path.write_text(plan.model_dump_json())
    result = project.render()
    assert result["verification"]["narration_alignment"]["status"] == "passed"
    previous = project.status().fingerprint
    write_audio(audio, 5.9)
    assert project.status().fingerprint != previous
    assert project.status().full_export_media_verification == "pending"


def test_wrong_metadata_is_failed(project, tmp_path):
    result = project.preview(start=0, end=1)
    path = result["artifacts"][0]["path"]
    check = verify_media(
        path, width=123, height=456, fps=60, duration=1, require_audio=True, frame_directory=tmp_path / "frames"
    )
    assert check["status"] == "failed"
    assert not check["checks"]["dimensions"]


@pytest.mark.parametrize("damage", ["muted", "truncated", "partial_window"])
def test_missing_narration_fails_alignment_despite_matching_first_window(tmp_path, damage):
    reference = tmp_path / "reference.wav"
    actual = tmp_path / "actual.wav"
    output = tmp_path / "output.mp4"
    write_audio(reference, 12)
    write_audio(
        actual,
        {"muted": 12, "truncated": 3, "partial_window": 11}[damage],
        silent_after=3 if damage == "muted" else None,
    )
    run_tool(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=64x64:r=5:d=12",
            "-i",
            str(actual),
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-c:a",
            "aac",
            str(output),
        ]
    )
    check = verify_media(
        output,
        width=64,
        height=64,
        fps=5,
        duration=12,
        require_audio=True,
        frame_directory=tmp_path / "frames",
        reference=reference,
    )
    assert check["status"] == "passed"
    result = check["narration_alignment"]
    assert result["status"] == "failed"
    assert len(result["windows"]) == 3
    assert result["windows"][0]["correlation"] >= 0.8
    assert result["windows"][-1]["correlation"] < 0.8


@pytest.mark.parametrize("silent_after,status", [(3, "passed"), (0, "unverified")])
def test_reference_silence_does_not_count_as_missing_narration(tmp_path, silent_after, status):
    reference = tmp_path / "reference.wav"
    write_audio(reference, 12, silent_after=silent_after)
    result = alignment(reference, reference, source_start=0, duration=12)
    assert result["status"] == status
    if status == "passed":
        assert len(result["windows"]) == 1
