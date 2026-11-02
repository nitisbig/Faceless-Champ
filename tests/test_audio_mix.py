"""Mix roles: ducking under narration, playback rate, SFX placement, the voice chain and the audio audit."""

import array
import json
import math
import subprocess
from itertools import pairwise

import pytest

from faceless_champ import Canvas, Scene, audio_audit, render, run
from faceless_champ.audio import sound_marks

SMALL = {"width": 160, "height": 90, "fps": 10, "antialias": 1}


def _gen(path, expr, seconds=6, rate=48000):
    command = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s={rate}:d={seconds}"]
    subprocess.run([*command, str(path)], check=True)
    return path


def _pcm(path):
    data = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", "48000", "pipe:1"],
        capture_output=True,
        check=True,
    ).stdout
    samples = array.array("f")
    samples.frombytes(data)
    return samples


def _db(samples, t, length=0.1):
    window = samples[int(t * 48000) : int((t + length) * 48000)]
    return 10 * math.log10(sum(x * x for x in window) / len(window) + 1e-20)


@pytest.fixture
def voice(tmp_path):  # speech from 1-2 s and 4-5 s
    return _gen(tmp_path / "voice.wav", "0.5*sin(2*PI*1000*t)*(between(t,1,2)+between(t,4,5))")


@pytest.fixture
def music(tmp_path):
    return _gen(tmp_path / "music.wav", "0.25*sin(2*PI*300*t)")


def _mix(voice, music, *, duck=-12.0, voice_volume=0.0, music_volume=1.0):
    scene = Scene(Canvas(160, 90, "#000000"))
    scene.add_audio(voice, start=0, role="voice", volume=voice_volume)
    scene.add_audio(music, start=0, role="music", duck=duck, volume=music_volume)
    return scene.wait_until(6)


def test_music_ducks_by_the_requested_depth_while_the_voice_speaks(tmp_path, voice, music):
    # A silent voice still keys the duck, so the output is the music bed alone.
    samples = _pcm(render(_mix(voice, music), tmp_path / "duck.mp4", **SMALL))
    full = _db(samples, 0.4)
    assert _db(samples, 1.4) - full == pytest.approx(-12, abs=0.3)
    assert _db(samples, 4.4) - full == pytest.approx(-12, abs=0.3)
    assert _db(samples, 3.0) == pytest.approx(full, abs=0.2)  # the 2 s pause comes back up
    assert full - 12 < _db(samples, 2.15, 0.05) < full  # eased, not switched
    assert _db(samples, 5.6) == pytest.approx(full, abs=0.2)


def test_short_pauses_stay_ducked(tmp_path, music):
    choppy = _gen(tmp_path / "choppy.wav", "0.5*sin(2*PI*1000*t)*(between(t,1,2)+between(t,2.5,3.5))")
    samples = _pcm(render(_mix(choppy, music), tmp_path / "duck.mp4", **SMALL))
    assert _db(samples, 2.2) - _db(samples, 0.4) == pytest.approx(-12, abs=0.3)


def test_playback_rate_shortens_and_raises_pitch(tmp_path, tone):
    scene = Scene(Canvas(160, 90, "#000000")).add_audio(tone, start=0, rate=2.0)
    assert scene.audio[0].duration == pytest.approx(1.0)
    samples = _pcm(render(scene.wait_until(1.5), tmp_path / "fast.mp4", **SMALL))
    window = samples[4800:43200]  # 0.1-0.9 s
    crossings = sum(1 for a, b in pairwise(window) if a < 0 <= b)
    assert crossings / 0.8 == pytest.approx(880, rel=0.02)
    assert _db(samples, 1.2) < -60  # finished after 1 s


def _hit(tmp_path):
    # 0.3 s of silence, a 0.2 s swell to the loudest point at 0.5 s, then a decay.
    expr = "sin(2*PI*700*t)*if(lt(t,0.3),0,if(lt(t,0.5),0.05+4*(t-0.3),0.85*exp(-(t-0.5)*12)))"
    return _gen(tmp_path / "hit.wav", expr, seconds=1.2)


def test_sound_marks_find_onset_and_peak(tmp_path):
    onset, peak = sound_marks(_hit(tmp_path))
    assert onset == pytest.approx(0.3, abs=0.01)
    assert peak == pytest.approx(0.5, abs=0.015)


@pytest.mark.parametrize(("align", "loudest"), [("onset", 1.2), ("peak", 1.0)])
def test_sfx_lands_on_its_beat(tmp_path, align, loudest):
    scene = Scene(Canvas(160, 90, "#000000")).add_sfx(_hit(tmp_path), 1.0, align=align)
    clip = scene.audio[0]
    assert clip.role == "sfx" and clip.trim_start == pytest.approx(0.3, abs=0.01)
    samples = _pcm(render(scene.wait_until(2.5), tmp_path / "sfx.mp4", **SMALL))
    level = [_db(samples, i / 200, 0.005) for i in range(400)]
    assert max(range(400), key=level.__getitem__) / 200 == pytest.approx(loudest, abs=0.02)
    first = next(i for i, v in enumerate(level) if v > -45) / 200
    assert first == pytest.approx(1.0 if align == "onset" else 0.8, abs=0.02)


def test_sfx_peak_before_zero_cuts_into_the_attack(tmp_path):
    scene = Scene(Canvas(160, 90, "#000000")).add_sfx(_hit(tmp_path), 0.05, align="peak", rate=2.0)
    clip = scene.audio[0]
    assert clip.start == 0 and clip.trim_start == pytest.approx(0.3 + 0.1, abs=0.01)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"role": "dialogue"}, "role must be one of"),
        ({"duck": 3}, "duck"),
        ({"duck": -80}, "duck"),
        ({"rate": 5}, "rate"),
        ({"rate": 0.1}, "rate"),
    ],
)
def test_mix_options_are_validated(tone, kwargs, match):
    with pytest.raises(ValueError, match=match):
        Scene().add_audio(tone, **kwargs)


def test_sfx_validation(tmp_path, tone):
    with pytest.raises(ValueError, match="align"):
        Scene().add_sfx(tone, 0, align="middle")
    silent = _gen(tmp_path / "silent.wav", "0", seconds=0.5)
    with pytest.raises(ValueError, match="silent"):
        Scene().add_sfx(silent, 0)


def test_audit_flags_music_over_voice_and_clears_once_ducked(voice, music):
    report = audio_audit(_mix(voice, music, duck=0, voice_volume=0.3))
    assert [f.code for f in report.findings] == ["MUSIC_MASKS_VOICE"]
    quiet = audio_audit(_mix(voice, music, duck=-18, voice_volume=1.0, music_volume=0.5))
    assert quiet.findings == [] and quiet.ok


def test_audit_reports_clipping_gain_and_missing_voice(tmp_path, music):
    loud = Scene(Canvas(160, 90, "#000000")).add_audio(music, start=0, volume=8, duck=-6).wait_until(6)
    codes = {f.code: f for f in audio_audit(loud, loudness=None).findings}
    assert codes["AUDIO_CLIPPING"].severity == "error" and "DUCK_WITHOUT_VOICE" in codes
    quiet = Scene(Canvas(160, 90, "#000000")).add_audio(music, start=0, volume=0.05).wait_until(6)
    assert [f.code for f in audio_audit(quiet).findings] == ["AUDIO_GAIN"]
    assert audio_audit(Scene().wait(1)).findings == []


def test_runner_audit_includes_the_mix(tmp_path, capsys, voice, music):
    code = run(lambda: _mix(voice, music, duck=0, voice_volume=0.3), argv=["--audit"], output_dir=tmp_path)
    assert code == 0
    report = json.loads(capsys.readouterr().out.strip().splitlines()[-1])["audit"]
    assert "MUSIC_MASKS_VOICE" in {f["code"] for f in report["findings"]}


# ---------------------------------------------------------------- voice chain (faceless-champ[audio])


@pytest.fixture
def take(tmp_path):
    # A quiet, uneven "take": voiced bursts with hiss-like sibilance and a rumble.
    expr = (
        "(0.04*sin(2*PI*180*t)+0.02*sin(2*PI*900*t))*(1+0.8*sin(2*PI*1.3*t))*between(mod(t,1),0,0.6)"
        "+0.03*sin(2*PI*7000*t)*between(mod(t,1),0.6,0.75)+0.02*sin(2*PI*40*t)"
    )
    return _gen(tmp_path / "take.wav", expr, seconds=8)


def test_voice_chain_hits_its_target_and_caches(tmp_path, monkeypatch, take):
    voice = pytest.importorskip("faceless_champ.voice")
    pytest.importorskip("pedalboard")
    pytest.importorskip("pyloudnorm")
    monkeypatch.setenv("FC_CACHE_DIR", str(tmp_path / "cache"))
    out = voice.process_voice(take)
    assert out.parent == tmp_path / "cache" / "voice" and out.suffix == ".wav"
    assert voice.loudness(out) == pytest.approx(-16, abs=0.5)
    samples = _pcm(out)
    assert 20 * math.log10(max(abs(x) for x in samples)) <= -1.5 + 0.05
    stamp = out.stat().st_mtime_ns
    assert voice.process_voice(take) == out and out.stat().st_mtime_ns == stamp
    other = voice.process_voice(take, "broadcast", loudness=-18)
    assert other != out and voice.loudness(other) == pytest.approx(-18, abs=0.5)
    explicit = voice.process_voice(take, voice.VoiceChain(), output=tmp_path / "clean.wav")
    assert explicit == tmp_path / "clean.wav" and explicit.is_file()


def test_voice_chain_removes_rumble_and_tames_sibilance(tmp_path, monkeypatch, take):
    voice = pytest.importorskip("faceless_champ.voice")
    pytest.importorskip("pedalboard")
    monkeypatch.setenv("FC_CACHE_DIR", str(tmp_path / "cache"))
    plain = voice.process_voice(take, de_ess=0)
    shaped = voice.process_voice(take)

    def band(path, low, high):
        graph = f"highpass=f={low}:poles=2,highpass=f={low}:poles=2,lowpass=f={high}:poles=2,lowpass=f={high}:poles=2"
        filtered = tmp_path / f"band-{path.stem}-{low}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-af", graph, str(filtered)], check=True)
        return _db(_pcm(filtered), 0, 7.9)

    # De-essing lowers 7 kHz relative to the voiced band compared with the same chain without it.
    assert band(shaped, 6000, 8000) - band(shaped, 150, 1000) < band(plain, 6000, 8000) - band(plain, 150, 1000) - 2
    assert band(shaped, 30, 50) < band(take, 30, 50) - 15 + (voice.loudness(shaped) - voice.loudness(take))


def test_voice_chain_options(tmp_path):
    voice = pytest.importorskip("faceless_champ.voice")
    assert voice.VoiceChain.named("warm", loudness=-18).loudness == -18
    with pytest.raises(ValueError, match="Unknown voice preset"):
        voice.VoiceChain.named("radio")
    with pytest.raises(ValueError, match="loudness"):
        voice.VoiceChain(loudness=-2)
    with pytest.raises(ValueError, match="ceiling"):
        voice.VoiceChain(ceiling=1)
    with pytest.raises(FileNotFoundError):
        voice.process_voice(tmp_path / "missing.wav")


def test_voice_chain_passes_silence_through(tmp_path, monkeypatch):
    voice = pytest.importorskip("faceless_champ.voice")
    pytest.importorskip("pedalboard")
    monkeypatch.setenv("FC_CACHE_DIR", str(tmp_path / "cache"))
    out = voice.process_voice(_gen(tmp_path / "quiet.wav", "0", seconds=1))
    assert voice.loudness(out) == float("-inf") and max(abs(x) for x in _pcm(out)) == 0


@pytest.mark.parametrize("suffix", [".flac", ".ogg"])
def test_lossless_and_ogg_sources_mix(tmp_path, suffix):
    path = _gen(tmp_path / f"hit{suffix}", "0.5*sin(2*PI*500*t)", seconds=1)
    scene = Scene(Canvas(160, 90, "#000000")).add_sfx(path, 0.2)
    samples = _pcm(render(scene.wait_until(1.5), tmp_path / "mix.mp4", **SMALL))
    assert _db(samples, 0.5) > -15 and _db(samples, 0.05) < -60
