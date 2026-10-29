"""Focused regression: native Manim cue rounding at the three runner profiles."""

import unittest
from fractions import Fraction
from types import SimpleNamespace

import numpy as np
from manim import tempconfig
from network_scene import NeuralBackpropagation


class TimingTests(unittest.TestCase):
    def test_cumulative_cues_keep_exact_frame_count(self):
        cues = (
            [3, 0.5]
            + [1, 0.5] * 3
            + [2]
            + [0.5, 0.75] * 4
            + [2, 1, 4, 1, 1]
            + [1.25, 0.75] * 3
            + [2, 1]
            + [0.5] * 20
            + [2]
        )
        self.assertEqual(sum(cues), 45)
        for fps in (4, 15, 30):
            with self.subTest(fps=fps), tempconfig({"frame_rate": fps}):
                counts = []
                scene = SimpleNamespace(
                    play=lambda counts=counts, fps=fps, **kwargs: counts.append(
                        len(np.arange(0, kwargs["run_time"], 1 / fps))
                    )
                )
                elapsed = Fraction(0)
                for seconds in cues:
                    NeuralBackpropagation.play_for(scene, run_time=seconds)
                    elapsed += Fraction(str(seconds))
                    self.assertEqual(sum(counts), round(elapsed * fps))
                self.assertEqual(sum(counts), 45 * fps)


if __name__ == "__main__":
    unittest.main()
