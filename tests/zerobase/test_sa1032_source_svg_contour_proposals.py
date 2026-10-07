import unittest

import numpy as np
import cv2

from minimalizer_zerobase.reviewed_sa10.source_svg_contour_proposals import propose_existing_contour


class SourceContourTests(unittest.TestCase):
    def test_rectangle_observation_only(self):
        m = np.zeros((64, 64), np.uint8)
        cv2.rectangle(m, (10, 12), (40, 50), 1, -1)
        original = m.copy()
        p = propose_existing_contour("hair", m, m)
        self.assertIsNotNone(p)
        self.assertGreaterEqual(p.source_iou, 0.90)
        self.assertTrue(np.array_equal(m, original))

    def test_hole_fails_closed(self):
        m = np.zeros((64, 64), np.uint8)
        cv2.rectangle(m, (5, 5), (55, 55), 1, -1)
        cv2.rectangle(m, (20, 20), (40, 40), 0, -1)
        self.assertIsNone(propose_existing_contour("face", m, m))

    def test_missing_part_fails_closed(self):
        m = np.zeros((32, 32), np.uint8)
        self.assertIsNone(propose_existing_contour("face", m, m))

    def test_non_face_hair_rejected(self):
        m = np.ones((16, 16), np.uint8)
        with self.assertRaises(ValueError):
            propose_existing_contour("left_arm", m, m)


if __name__ == "__main__":
    unittest.main()
