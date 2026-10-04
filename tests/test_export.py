import array
import math
import subprocess
import sys

import pytest

from faceless_champ import Canvas, Scene, Sequence, render
from faceless_champ.audio import probe


def rms(samples):
    return math.sqrt(sum(x * x for x in samples) / len(samples))


def decode_audio(path):
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", "48000", "pipe:1"],
        capture_output=True,
        check=True,
    )
    samples = array.array("f")
    samples.frombytes(result.stdout)
    return samples


def test_real_export_audio_timing_mixing_fades_and_overwrite(tmp_path, tone):
    scene = Scene(Canvas(160, 90, "navy")).wait(2)
    scene.add_audio(tone, start=0.4, trim_start=0.2, trim_end=1.4, volume=0.4, fade_in=0.2, fade_out=0.2)
    scene.add_audio(tone, start=0.4, trim_start=0.2, trim_end=1.4, volume=0.4, fade_in=0.2, fade_out=0.2)
    output = render(scene, tmp_path / "video.mp4", width=160, height=90, fps=20, preset="ultrafast")
    info = probe(output)
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    audio = next(s for s in info["streams"] if s["codec_type"] == "audio")
    assert (video["width"], video["height"], video["codec_name"], video["r_frame_rate"]) == (160, 90, "h264", "20/1")
    assert audio["codec_name"] == "aac"
    assert abs(float(info["format"]["duration"]) - 2) <= 1 / 20
    samples = decode_audio(output)
    window = lambda start, end: rms(samples[int(start * 48000) : int(end * 48000)])
    assert window(0.1, 0.3) < 0.001
    assert window(0.8, 1) > 0.08
    assert window(0.41, 0.44) < window(0.8, 1) * 0.4
    assert window(1.55, 1.59) < window(0.8, 1) * 0.4
    assert window(1.8, 1.95) < 0.001
    original = output.read_bytes()
    with pytest.raises(FileExistsError):
        render(scene, output, width=160, height=90)
    assert output.read_bytes() == original
    render(scene, output, width=160, height=90, fps=5, preset="ultrafast", overwrite=True)


def test_crossfade_audio_envelope(tmp_path, tone):
    first = Scene(Canvas(160, 90, "red")).wait(1.5)
    first.add_audio(tone, start=0, trim_end=1.5, volume=0.6)
    second = Scene(Canvas(160, 90, "blue")).wait(1.5)
    output = render(
        Sequence(first, second, crossfade=0.5), tmp_path / "fade.mp4", width=160, height=90, fps=10, preset="ultrafast"
    )
    samples = decode_audio(output)
    window = lambda start, end: rms(samples[int(start * 48000) : int(end * 48000)])
    assert window(1.3, 1.4) < window(0.5, 0.6) * 0.5
    assert window(1.7, 1.8) < 0.001


def test_render_frame_progress_and_invalid_callback(tmp_path):
    reports = []
    output = render(
        Scene(Canvas(160, 90)).wait(1),
        tmp_path / "progress.mp4",
        width=160,
        height=90,
        fps=2,
        preset="ultrafast",
        progress=lambda completed, total: reports.append((completed, total)),
    )
    assert output.is_file()
    assert reports == [(0, 2), (1, 2), (2, 2)]
    with pytest.raises(TypeError, match="progress must be callable"):
        render(Scene().wait(1), tmp_path / "invalid.mp4", progress=True)
    assert not (tmp_path / "invalid.mp4").exists()


def test_encoder_failure_cleans_up(tmp_path, monkeypatch):
    from faceless_champ import export

    original = export.subprocess.Popen

    def broken(command, **kwargs):
        return original(
            [sys.executable, "-c", 'import sys; sys.stderr.write("deliberate encoder failure"); sys.exit(1)'], **kwargs
        )

    monkeypatch.setattr(export.subprocess, "Popen", broken)
    with pytest.raises(RuntimeError, match="deliberate encoder failure"):
        render(Scene(Canvas(160, 90)).wait(0.1), tmp_path / "bad.mp4", width=160, height=90)
    assert not list(tmp_path.iterdir())


def test_cli_success_and_errors(tmp_path):
    source = tmp_path / "demo.py"
    source.write_text(
        "from faceless_champ import Scene, Canvas\nclass Demo(Scene):\n def construct(self): self.wait(.1)\n"
    )
    base = [sys.executable, "-m", "faceless_champ", "render", str(source)]
    for name in ["Missing", "Canvas"]:
        result = subprocess.run(
            base + [name, "-o", str(tmp_path / "bad.mp4")], capture_output=True, text=True, check=False
        )
        assert result.returncode == 1
        assert "faceless-champ:" in result.stderr
    result = subprocess.run(
        base + ["Demo", "-o", str(tmp_path / "good.mp4"), "--width", "160", "--height", "90", "--fps", "10"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    result = subprocess.run(
        base + ["Demo", "-o", str(tmp_path / "good.mp4"), "--width", "160", "--height", "90"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1 and "exists" in result.stderr


def test_missing_ffmpeg(monkeypatch, tmp_path):
    from faceless_champ import audio

    monkeypatch.setattr(audio.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="ffmpeg is required"):
        render(Scene().wait(1), tmp_path / "video.mp4")


@pytest.mark.parametrize("extension", ["mp3", "m4a"])
def test_compressed_audio_import(tmp_path, tone, extension):
    source = tmp_path / f"source.{extension}"
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(tone), str(source)], check=True)
    scene = Scene(Canvas(160, 90)).wait(0.8)
    scene.add_audio(source, start=0.1, trim_start=0.3, trim_end=0.8, volume=0.5)
    path = render(scene, tmp_path / "compressed.mp4", width=160, height=90, fps=10, preset="ultrafast")
    samples = decode_audio(path)
    assert rms(samples[12000:24000]) > 0.04
    assert rms(samples[34000:37000]) < 0.001


def test_nested_incoming_crossfade_audio_and_grid_end(tmp_path, tone):
    from faceless_champ import Grid

    silent = Scene(Canvas(160, 90, "red")).wait(1)
    sounding = Scene(Canvas(160, 90, "blue"))
    sounding.add_audio(tone, start=0, trim_end=1, volume=0.5)
    hold = Scene(Canvas(160, 90)).wait(2)
    grid = Grid(sounding, hold, rows=1, columns=2, canvas=Canvas(160, 90))
    video = Sequence(silent, grid, crossfade=0.4)
    path = render(video, tmp_path / "nested.mp4", width=160, height=90, fps=10, preset="ultrafast")
    samples = decode_audio(path)

    def window(start, end):
        return rms(samples[int(start * 48000) : int(end * 48000)])

    assert window(0.1, 0.4) < 0.001
    assert 0.001 < window(0.63, 0.68) < window(1.1, 1.2) * 0.3
    assert window(1.1, 1.2) > 0.05
    assert window(1.8, 2.1) < 0.001
    assert abs(float(probe(path)["format"]["duration"]) - 2.6) < 0.1
