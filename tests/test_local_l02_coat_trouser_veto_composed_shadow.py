"""Source-free coat/underlayer veto composition regression; known-only hypothesis."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_coat_trouser_veto_composed_shadow import propose_coat_trouser_veto_shadow


def scene():
    h, w = 60, 60
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., :3] = (35, 140, 180)
    rgba[..., 3] = 255
    cls = np.zeros((h, w), np.uint8)
    owner = np.zeros((h, w), np.uint8)
    cls[10:50, 10:50] = 10
    owner[10:50, 10:50] = 2
    independent = np.zeros_like(owner)
    return dict(source_rgba=rgba, class_ids=cls,
                independent_outerwear=independent, frozen_owner=owner)


class TestCoatTrouserVeto(unittest.TestCase):
    def test_no_independent_support_keeps_frozen_owner(self):
        x = scene()
        out, meta = propose_coat_trouser_veto_shadow(**x)
        np.testing.assert_array_equal(out, x['frozen_owner'])
        self.assertEqual(meta['owner_promotions'], 0)
        self.assertFalse(meta['semantic_quality_pass'])

    def test_alpha_violation_fails_closed(self):
        x = scene()
        x['source_rgba'][20,20,3] = 0
        with self.assertRaises(Exception):
            propose_coat_trouser_veto_shadow(**x)

    def test_input_arrays_not_modified(self):
        x = scene()
        snap = {k:v.copy() for k,v in x.items()}
        propose_coat_trouser_veto_shadow(**x)
        for k in x: np.testing.assert_array_equal(x[k], snap[k])


if __name__ == '__main__':
    unittest.main()
