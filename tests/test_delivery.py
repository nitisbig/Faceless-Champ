"""Production finishing: BT.709 color, master codecs, .cube grades, loudness targets and delivery checks."""

import json
import subprocess
import sys

import pytest

from faceless_champ import Canvas, ExportSettings, Scene, delivery_report, render
from faceless_champ.audio import probe

SMALL = {"width": 160, "height": 90, "fps": 10, "antialias": 1}


def _encoders():
    return subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True, check=False).stdout


def _scene(audio=None, color="#ff0000", seconds=2.0):
    scene = Scene(Canvas(320, 180, color))
    if audio is not None:
        scene.add_audio(audio, start=0)
    return scene.wait(seconds)


def _first_rgb(path):
    data = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
        capture_output=True,
        check=True,
    ).stdout
    return tuple(data[:3])


def _first_luma(path):
    data = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "yuv420p", "pipe:1"],
        capture_output=True,
        check=True,
    ).stdout
    return data[0]


def _video(path):
    return next(s for s in probe(path)["streams"] if s["codec_type"] == "video")


def _cube(path, invert=True):
    rows = [f"{1 - r} {1 - g} {1 - b}" if invert else f"{r} {g} {b}" for b in (0, 1) for g in (0, 1) for r in (0, 1)]
    path.write_text("LUT_3D_SIZE 2\n" + "\n".join(rows) + "\n")
    return path


def _loud(tmp_path, gain):
    path = tmp_path / f"loud{gain}.wav"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=2:sample_rate=48000"]
        + ["-af", f"volume={gain}dB", str(path)],
        check=True,
    )
    return path


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("codec", "av1", "codec must be one of"),
        ("lut", "grade.png", ".cube"),
        ("loudness", -2.0, "LUFS"),
        ("loudness", -80.0, "loudness"),
        ("true_peak", 0.5, "dBTP"),
        ("audio_bitrate", "loud", "audio_bitrate"),
    ],
)
def test_finishing_settings_are_validated(field, value, match):
    with pytest.raises(ValueError, match=match):
        ExportSettings(**{field: value}).dimensions(Canvas(1920, 1080))


def test_missing_lut_and_wrong_suffix_fail_before_rendering(tmp_path):
    with pytest.raises(FileNotFoundError, match="LUT"):
        ExportSettings(lut=tmp_path / "missing.cube").dimensions(Canvas())
    with pytest.raises(ValueError, match=r"\.mov extension"):
        render(_scene(), tmp_path / "master.mp4", codec="prores", **SMALL)
    assert not (tmp_path / "master.mp4").exists()


def test_h264_is_converted_and_tagged_bt709(tmp_path):
    out = render(_scene(), tmp_path / "red.mp4", **SMALL)
    video = _video(out)
    assert (video["color_space"], video["color_primaries"], video["color_transfer"]) == ("bt709",) * 3
    assert video["color_range"] == "tv"
    assert abs(_first_luma(out) - 63) <= 2  # BT.709 luma of pure red; BT.601 would give 81
    red, green, blue = _first_rgb(out)
    assert red > 240 and green < 12 and blue < 12


@pytest.mark.parametrize(
    ("codec", "suffix", "encoder", "pix_fmt", "audio_codec"),
    [("hevc10", ".mp4", "libx265", "yuv420p10le", "aac"), ("prores", ".mov", "prores_ks", "yuv422p10le", "pcm_s16le")],
)
def test_master_codecs(tmp_path, tone, codec, suffix, encoder, pix_fmt, audio_codec):
    if encoder not in _encoders():
        pytest.skip(f"FFmpeg built without {encoder}")
    out = render(_scene(tone), tmp_path / f"master{suffix}", codec=codec, **SMALL)
    streams = probe(out)["streams"]
    video = next(s for s in streams if s["codec_type"] == "video")
    audio = next(s for s in streams if s["codec_type"] == "audio")
    assert (video["pix_fmt"], video["color_space"], audio["codec_name"]) == (pix_fmt, "bt709", audio_codec)
    assert _first_rgb(out)[0] > 240


def test_cube_lut_grades_in_rgb_even_with_awkward_paths(tmp_path):
    folder = tmp_path / "my grades"
    folder.mkdir()
    lut = _cube(folder / "invert 'v1'.cube")
    out = render(_scene(), tmp_path / "graded.mp4", lut=lut, **SMALL)
    red, green, blue = _first_rgb(out)
    assert red < 12 and green > 240 and blue > 240  # red inverted to cyan


def test_loudness_target_is_reached_in_two_passes(tmp_path):
    out = render(_scene(_loud(tmp_path, -30)), tmp_path / "loud.mp4", loudness=-16, **SMALL)
    report = delivery_report(out, loudness=-16)
    assert report.loudness == pytest.approx(-16, abs=0.6)
    assert report.true_peak <= -1.0 + 0.2
    assert not [f for f in report.findings if f.code in {"LOUDNESS", "TRUE_PEAK", "CLIPPING"}]


def test_loudness_skips_silent_mixes(tmp_path):
    silent = tmp_path / "silent.wav"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "2", str(silent)],
        check=True,
    )
    out = render(_scene(silent), tmp_path / "silent.mp4", loudness=-14, **SMALL)
    assert out.is_file()


def test_delivery_report_flags_problem_files(tmp_path):
    bad = tmp_path / "bad.mp4"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=black:s=320x180:r=30:d=3"]
        + ["-f", "lavfi", "-i", "sine=frequency=440:duration=3:sample_rate=44100"]
        + ["-af", "volume=30dB", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(bad)],
        check=True,
    )
    report = delivery_report(bad)
    codes = {f.code: f for f in report.findings}
    assert {"COLOR_TAGS", "BLACK", "CLIPPING", "LOUDNESS", "SAMPLE_RATE"} <= set(codes)
    assert codes["CLIPPING"].severity == "error" and not report.ok
    assert codes["BLACK"].start == pytest.approx(0, abs=0.05) and codes["BLACK"].end > 2.5
    assert "CLIPPING" in str(report)


def test_delivery_report_passes_a_finished_render(tmp_path):
    out = render(_scene(_loud(tmp_path, -20), color="#3366cc"), tmp_path / "ok.mp4", loudness=-14, **SMALL)
    report = delivery_report(out)
    assert report.ok and report.color_space == "bt709" and report.sample_rate == 48000
    assert [f.code for f in report.findings if f.severity != "info"] == []
    with pytest.raises(FileNotFoundError):
        delivery_report(tmp_path / "nope.mp4")


def test_cli_check_and_finishing_flags(tmp_path):
    source = tmp_path / "demo.py"
    source.write_text(
        "from faceless_champ import Scene, Canvas\nclass Demo(Scene):\n def construct(self): self.wait(.5)\n"
    )
    lut = _cube(tmp_path / "identity.cube", invert=False)
    out = tmp_path / "demo.mov"
    render_args = ["Demo", "-o", str(out), "--width", "160", "--height", "90", "--fps", "10"]
    if "prores_ks" not in _encoders():
        pytest.skip("FFmpeg built without prores_ks")
    result = subprocess.run(
        [sys.executable, "-m", "faceless_champ", "render", str(source), *render_args, "--codec", "prores"]
        + ["--lut", str(lut), "--loudness", "-14"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    check = [sys.executable, "-m", "faceless_champ", "check", str(out)]
    result = subprocess.run([*check, "--json"], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["ok"] and data["video_codec"] == "prores" and data["audio_codec"] is None
    assert any(f["code"] == "NO_AUDIO" for f in data["findings"])
    result = subprocess.run([*check[:-1], str(tmp_path / "missing.mp4")], capture_output=True, text=True, check=False)
    assert result.returncode == 1 and "faceless-champ:" in result.stderr
