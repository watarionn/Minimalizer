"""Source-free regression for class30 dual-owner ambiguity and frozen topology."""
import sys
import unittest
from pathlib import Path
import numpy as np
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_class30_dual_seed_extension_shadow import (
    propose_class30_dual_seed_extension_shadow, DualClass30Hold,
)


def scene():
    cls = np.zeros((9, 11), np.uint8)
    anime = np.zeros_like(cls)
    owner = np.zeros_like(cls)
    cls[4, 1], cls[4, 9] = 5, 10
    owner[4, 1], owner[4, 9] = 1, 2
    cls[4, 2:9] = 30
    anime[4, 2:9] = 10
    alpha = np.full_like(cls, 255)
    return dict(source_alpha=alpha, class_ids=cls,
                anime_classes=anime, frozen_owner=owner)


class TestClass30DualSeed(unittest.TestCase):
    def test_two_owners_split_at_geodesic_tie(self):
        x = scene()
        result, meta = propose_class30_dual_seed_extension_shadow(**x)
        self.assertEqual(list(result[4, 1:10]), [1, 1, 1, 1, 0, 2, 2, 2, 2])
        self.assertEqual(meta['source_only_added_px'], 6)
        self.assertFalse(meta['semantic_quality_pass'])
        self.assertEqual(meta['production'], 'NO_GO')

    def test_independent_observer_and_alpha_are_hard_fences(self):
        x = scene()
        x['anime_classes'][4, 4] = 11
        x['source_alpha'][4, 6] = 0
        result, _ = propose_class30_dual_seed_extension_shadow(**x)
        self.assertEqual(result[4, 4], 0)
        self.assertEqual(result[4, 6], 0)
        self.assertEqual(result[4, 1], 1)
        self.assertEqual(result[4, 9], 2)

    def test_only_class30_can_be_added(self):
        x = scene()
        x['class_ids'][4, 3] = 32
        result, _ = propose_class30_dual_seed_extension_shadow(**x)
        self.assertEqual(result[4, 3], 0)
        self.assertEqual(result[4, 2], 1)

    def test_frozen_component_merges_are_cut(self):
        x = scene()
        x['frozen_owner'][4, 9] = 0
        x['class_ids'][4, 9] = 0
        x['frozen_owner'][4, 7] = 1
        x['class_ids'][4, 7] = 5
        result, _ = propose_class30_dual_seed_extension_shadow(**x)
        for connectivity in (4, 8):
            st = ndimage.generate_binary_structure(2, 1 if connectivity == 4 else 2)
            self.assertEqual(ndimage.label(x['frozen_owner'] == 1, st)[1],
                             ndimage.label(result == 1, st)[1])
        self.assertTrue(np.array_equal(result[x['frozen_owner'] != 0],
                                       x['frozen_owner'][x['frozen_owner'] != 0]))

    def test_malformed_or_out_of_alpha_fails_closed(self):
        for key, val in (
            ('source_alpha', scene()['source_alpha'].astype(np.int16)),
            ('class_ids', scene()['class_ids'][:4]),
            ('anime_classes', scene()['anime_classes'].astype(bool)),
            ('frozen_owner', scene()['frozen_owner'].astype(np.int16)),
        ):
            x = scene()
            x[key] = val
            with self.subTest(key=key), self.assertRaises(DualClass30Hold):
                propose_class30_dual_seed_extension_shadow(**x)
        x = scene()
        x['source_alpha'][4, 1] = 0
        with self.assertRaisesRegex(DualClass30Hold, 'OUTSIDE_SOURCE'):
            propose_class30_dual_seed_extension_shadow(**x)

    def test_no_seed_does_not_hallucinate_owner(self):
        x = scene()
        x['frozen_owner'][:] = 0
        result, meta = propose_class30_dual_seed_extension_shadow(**x)
        self.assertEqual(int(np.count_nonzero(result)), 0)
        self.assertEqual(meta['source_pixels_generated'], 0)


if __name__ == '__main__':
    unittest.main()
