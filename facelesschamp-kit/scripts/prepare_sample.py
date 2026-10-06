"""Developer-only fixture preparation; espeak-ng is not a kit runtime dependency."""

import subprocess
import tempfile
from pathlib import Path

DEST = Path(__file__).resolve().parents[1] / "src/facelesschamp_kit/sample_assets"
LINES = [
    "Build once. Reuse everywhere. A video component brings content, layout, and motion together in one reusable definition.",
    "Repeated setup makes every project harder to maintain. Shared building blocks give your videos consistent structure and style.",
    "Compose your scenes. Preview the important moments. Then export the complete video. Keep the original narration timing throughout.",
]
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    for i, line in enumerate(LINES):
        subprocess.run(["espeak-ng", "-s", "155", "-w", str(root / f"{i}.wav"), line], check=True)
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-i",
                str(root / f"{i}.wav"),
                "-af",
                "apad",
                "-t",
                "10",
                "-ar",
                "22050",
                "-ac",
                "1",
                str(root / f"part{i}.wav"),
            ],
            check=True,
        )
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            *[arg for i in range(3) for arg in ("-i", str(root / f"part{i}.wav"))],
            "-filter_complex",
            "[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]",
            "-map",
            "[out]",
            "-y",
            str(DEST / "voiceover.wav"),
        ],
        check=True,
    )
(DEST / "word-cues.srt").write_text(
    "\n\n".join(f"{i + 1}\n00:00:{i * 10:02},000 --> 00:00:{i * 10 + 9:02},000\n{line}" for i, line in enumerate(LINES))
    + "\n"
)
(DEST / "README.txt").write_text(
    "Synthetic demonstration speech, generated locally with espeak-ng. Original script in scripts/prepare_sample.py.\n"
    "Sentence-level cues at original source times 0, 10, and 20 seconds; these are not word-level alignments.\n"
    "This fixture is a rendering example, not historical or reported data. Replace it with your own audio and SRT.\n"
)
