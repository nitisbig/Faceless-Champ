import math
import struct
import wave

import pytest


@pytest.fixture
def tone(tmp_path):
    path = tmp_path / "tone.wav"
    with wave.open(str(path), "wb") as out:
        out.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
        out.writeframes(
            b"".join(struct.pack("<h", round(8000 * math.sin(math.tau * 440 * i / 48000))) for i in range(96000))
        )
    return path
