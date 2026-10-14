"""Derived gapless PCM narration; source audio and subtitle files stay untouched."""

import hashlib
import json
import subprocess
import wave
from pathlib import Path


def prepare_audio(project):
    project = Path(project)
    source = project / "audio.mp3"
    target = project / "output/narration.wav"
    stamp = target.with_suffix(".json")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if target.exists() and stamp.exists() and json.loads(stamp.read_text()).get("source_sha256") == digest:
        with wave.open(str(target)) as audio:
            if audio.getnframes() == 8745600 and audio.getframerate() == 48000:
                return target
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name("narration.tmp.wav")
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(source),
            "-ac",
            "1",
            "-ar",
            "48000",
            "-c:a",
            "pcm_s16le",
            str(temporary),
        ],
        check=True,
    )
    with wave.open(str(temporary)) as audio:
        frames, rate = audio.getnframes(), audio.getframerate()
    if (frames, rate) != (8745600, 48000):
        temporary.unlink(missing_ok=True)
        raise ValueError("Source narration changed; re-audit audio/cues before rebuilding")
    temporary.replace(target)
    stamp.write_text(
        json.dumps(
            {"source_sha256": digest, "samples": frames, "sample_rate": rate, "duration": frames / rate}, indent=2
        )
        + "\n"
    )
    return target
