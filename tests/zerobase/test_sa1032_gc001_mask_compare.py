import unittest
import numpy as np
from tools.run_sa1032_gc001_mask_compare import compare_masks

class MaskComparisonTests(unittest.TestCase):
    def test_identical(self):
        a = np.array([[True, False], [True, True]])
        self.assertEqual(compare_masks(a, a)["iou"], 1.0)
    def test_missing_pixels(self):
        a = np.array([[True, True], [False, False]])
        b = np.array([[True, False], [False, False]])
        r = compare_masks(a, b)
        self.assertEqual(r["source_missing_pixels"], 1)
        self.assertEqual(r["iou"], 0.5)
    def test_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            compare_masks(np.ones((2, 2), bool), np.ones((3, 3), bool))
