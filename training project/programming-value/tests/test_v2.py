"""Regression checks for timing protection and animated layout geometry."""

import unittest
from copy import deepcopy

import numpy as np
from main import programming_value_video
from scene.audit_v2 import check, intersects, segment_hits_box, world_matrix
from scene.renderer_v2 import FilmRenderer

from faceless_champ import Canvas, Circle, Group, PillowRenderer, Rectangle, Scene


class AcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiled = programming_value_video()

    def test_original_timing_and_complete_visual_coverage(self):
        result = check(self.compiled)
        self.assertTrue(result["passed"])
        self.assertLessEqual(result["maximum_attention_gap"], 3)

    def test_changed_reported_word_timestamp_is_rejected(self):
        report = deepcopy(self.compiled.report)
        report["narration"]["cues"][0]["start"] += 0.1
        clone = type(self.compiled)(self.compiled.composition, report, self.compiled.context)
        with self.assertRaisesRegex(ValueError, "cue timing"):
            check(clone)

    def test_visual_gap_is_rejected(self):
        report = deepcopy(self.compiled.report)
        report["visual_events"][2]["start"] += 0.1
        clone = type(self.compiled)(self.compiled.composition, report, self.compiled.context)
        with self.assertRaisesRegex(ValueError, "Gap or overlap"):
            check(clone)

    def test_v1_remains_available(self):
        original = programming_value_video(version="v1")
        self.assertEqual(original.composition.canvas.bg, "#FFFFFF")
        self.assertEqual(original.duration, self.compiled.duration)
        self.assertEqual(len(original.report["segments"]), 6)


class GeometryTests(unittest.TestCase):
    def test_layer_renderer_preserves_parent_opacity_and_motion(self):
        rectangle = Rectangle(width=100, height=45, fill="#56B4E9", stroke=None, position=(120, 90), opacity=0.8)
        circle = Circle(radius=18, fill="#E69F00", stroke=None, position=(250, 95))
        group = Group(rectangle, circle, opacity=0.65)
        scene = Scene(Canvas(400, 200, "black"))
        scene.add(group)
        scene.play(group.animate.move_to(215, 110).scale_to(1.08).rotate_to(8), run_time=1)
        reference = PillowRenderer(2)
        optimized = FilmRenderer(2)
        for t in (0, 0.25, 0.5, 1):
            a = np.asarray(reference.frame(scene, t, (400, 200))).astype(float)
            b = np.asarray(optimized.frame(scene, t, (400, 200))).astype(float)
            self.assertLess(float(np.abs(a - b).mean()), 1)

    def test_layer_renderer_preserves_top_left_anchor(self):
        scene = Scene(Canvas(400, 200, "black"))
        scene.add(Rectangle(width=100, height=45, fill="white", position=(20, 25), anchor="top_left"))
        a = np.asarray(PillowRenderer(2).frame(scene, 0, (400, 200)))
        b = np.asarray(FilmRenderer(2).frame(scene, 0, (400, 200)))
        np.testing.assert_array_equal(a, b)

    def test_animated_parent_transform_matches_public_bounds(self):
        child = Rectangle(width=120, height=60, position=(300, 300))
        group = Group(child)
        scene = Scene(Canvas(1920, 1080, "black"))
        scene.add(group)
        scene.play(group.animate.move_to(700, 600).scale_to(1.4).rotate_to(15), run_time=1)
        entry = scene._objects[child]
        for t in (0, 0.25, 0.5, 0.75, 1):
            matrix = world_matrix(entry, np.array([t]), {})[0]
            initial = child.bounds
            w, h = initial.width, initial.height
            corners = np.array([[-w / 2, -h / 2, 1], [w / 2, -h / 2, 1], [w / 2, h / 2, 1], [-w / 2, h / 2, 1]])
            points = corners @ matrix.T
            public = scene.bounds_at(child, t)
            np.testing.assert_allclose(
                [points[:, 0].min(), points[:, 1].min(), points[:, 0].max(), points[:, 1].max()],
                [public.left, public.top, public.right, public.bottom],
                atol=1e-7,
            )

    def test_diagonal_connector_uses_line_geometry(self):
        p = np.array([[0.0, 0.0], [0.0, 0.0]])
        q = np.array([[100.0, 100.0], [100.0, 100.0]])
        boxes = np.array([[70, 10, 90, 30], [40, 40, 60, 60]])
        self.assertEqual(segment_hits_box(p, q, boxes).tolist(), [False, True])

    def test_collision_and_clear_gap(self):
        a = np.array([[0, 0, 20, 20], [0, 0, 20, 20]])
        b = np.array([[19, 19, 30, 30], [52, 0, 72, 20]])
        self.assertEqual(intersects(a, b, gap=2).tolist(), [True, False])


if __name__ == "__main__":
    unittest.main()
