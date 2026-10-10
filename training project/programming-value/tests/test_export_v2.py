"""Real media checks for frame-aligned checkpoint reuse and final audio muxing."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from main import PROJECT
from scene.export_v2 import export_full, fingerprint
from scene.renderer_v2 import FilmRenderer

from faceless_champ import Canvas, ExportSettings, Rectangle, Scene


class CheckpointExportTests(unittest.TestCase):
    def test_real_chunks_join_without_frame_loss_and_resume_without_rendering(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project/video"
            (root / "scene").mkdir(parents=True)
            (root / "assets/fonts").mkdir(parents=True)
            (root / "audio.mp3").symlink_to(PROJECT / "audio.mp3")
            for name in ("main.py", "cue-per-word.srt"):
                (root / name).write_text("fixture\n")
            for name in ("story_v2.py", "design_v2.py", "design.py", "renderer_v2.py"):
                (root / "scene" / name).write_text("fixture\n")
            scene = Scene(Canvas(320, 180, "black"))
            marker = Rectangle(width=30, height=20, fill="#56B4E9", position=(70, 90))
            scene.add(marker)
            with scene.at(9.7):
                scene.play(marker.animate.move_to(240, 90), run_time=1.2)
            scene.wait_until(11.03)
            compiled = SimpleNamespace(context=SimpleNamespace(root=root), composition=scene, duration=11.03, report={})
            settings = ExportSettings(width=320, height=180, fps=30, antialias=2, crf=18, preset="medium")
            first = Path(temporary) / "first.mp4"
            export_full(compiled, first, settings, FilmRenderer(2))
            p = subprocess.run(
                ["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(first)],
                capture_output=True,
                text=True,
                check=True,
            )
            streams = json.loads(p.stdout)["streams"]
            video = next(s for s in streams if s["codec_type"] == "video")
            self.assertEqual(int(video["nb_frames"]), 331)
            self.assertTrue(any(s["codec_type"] == "audio" for s in streams))
            subprocess.run(
                ["ffmpeg", "-v", "error", "-xerror", "-i", str(first), "-f", "null", "-"],
                capture_output=True,
                check=True,
            )
            with patch("scene.export_v2.render", side_effect=AssertionError("Completed chunks were rendered again")):
                export_full(compiled, Path(temporary) / "resumed.mp4", settings, FilmRenderer(2))
            before = fingerprint(root, settings)
            (root / "cue-per-word.srt").write_text("changed fixture\n")
            self.assertNotEqual(before, fingerprint(root, settings))


if __name__ == "__main__":
    unittest.main()
