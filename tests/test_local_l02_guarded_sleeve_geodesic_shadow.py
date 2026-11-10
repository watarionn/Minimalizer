"""Source-free synthetic negatives for the research-only sleeve geodesic proposal."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_guarded_sleeve_geodesic_shadow import propose_guarded_sleeve, SleeveShadowHold


def scene():
    cls = np.zeros((7, 11), np.uint8)
    cls[3, 1] = 5
    cls[3, 9] = 10
    cls[3, 2:9] = 32
    anime = np.zeros_like(cls)
    anime[3, 2:9] = 10
    alpha = np.ones_like(cls) * 255
    owner = np.zeros_like(cls)
    owner[3, 1] = 1
    owner[3, 9] = 2
    return dict(class_ids=cls, anime_classes=anime, source_alpha=alpha,
                frozen_candidate=np.isin(cls, (5, 10, 32)), frozen_owner=owner)


class TestGuardedSleeve(unittest.TestCase):
    def test_dual_seed_tie_abstains(self):
        x = scene()
        out, meta = propose_guarded_sleeve(**x)
        self.assertEqual(list(out[3, 1:10]), [1, 1, 1, 1, 0, 2, 2, 2, 2])
        self.assertEqual(meta['added_sleeve_pixels'], 6)
        self.assertFalse(meta['semantic_quality_pass'])

    def test_skin_veto_no_gap_bridging(self):
        x = scene()
        x['anime_classes'][3, 4] = 1
        out, _ = propose_guarded_sleeve(**x)
        self.assertEqual(out[3, 4], 0)
        self.assertEqual(out[3, 3], 1)
        self.assertEqual(out[3, 5], 2)

    def test_orphan_remains_unowned(self):
        x = scene()
        x['class_ids'][0, 5] = 32
        x['anime_classes'][0, 5] = 10
        x['frozen_candidate'][0, 5] = True
        out, _ = propose_guarded_sleeve(**x)
        self.assertEqual(out[0, 5], 0)

    def test_source_alpha_fence(self):
        x = scene()
        x['source_alpha'][3, 5] = 0
        x['frozen_candidate'][3, 5] = False
        out, _ = propose_guarded_sleeve(**x)
        self.assertEqual(out[3, 5], 0)

    def test_invalid_inputs_fail_closed(self):
        for name, value in [('class_ids', scene()['class_ids'].astype(np.int16)),
                            ('anime_classes', scene()['anime_classes'].astype(bool)),
                            ('source_alpha', scene()['source_alpha'][:3]),
                            ('frozen_owner', scene()['frozen_owner'].astype(np.int16)),
                            ('frozen_candidate', scene()['frozen_candidate'].astype(np.uint8)),
                            ('connectivity', 3)]:
            x = scene()
            x[name] = value
            with self.subTest(name=name), self.assertRaises(SleeveShadowHold):
                propose_guarded_sleeve(**x)

    def test_conflicting_seed_rejected(self):
        x = scene()
        x['class_ids'][3, 1] = 10
        with self.assertRaisesRegex(SleeveShadowHold, 'CLASS_CONFLICT'):
            propose_guarded_sleeve(**x)

    def test_no_seed_rejected(self):
        x = scene()
        x['frozen_owner'][:] = 0
        with self.assertRaisesRegex(SleeveShadowHold, 'NO_OUTERWEAR_SEED'):
            propose_guarded_sleeve(**x)

    def test_8_neighbour_diagonal(self):
        x = scene()
        x['class_ids'][2, 2] = 32
        x['anime_classes'][2, 2] = 10
        x['frozen_candidate'][2, 2] = True
        four, _ = propose_guarded_sleeve(**x, connectivity=4)
        eight, _ = propose_guarded_sleeve(**x, connectivity=8)
        self.assertEqual(four[2, 2], 1)
        self.assertEqual(eight[2, 2], 1)


if __name__ == '__main__':
    unittest.main()
