"""Research-only synthetic safety regression, not semantic quality approval."""
import sys
from pathlib import Path
import unittest
import numpy as np
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_sleeve_contact_safe_shadow import propose_sleeve_contact_safe_shadow


def scene(two_owners=False):
    cls = np.zeros((7, 13), np.uint8); anime = np.zeros_like(cls)
    owner = np.zeros_like(cls); owner[3, 1] = 1; cls[3, 1] = 5
    if two_owners:
        owner[3, 11] = 2; cls[3, 11] = 10; end = 11
    else:
        end = 6
    cls[3, 2:end] = 32; anime[3, 2:end] = 10
    candidate = np.zeros_like(cls, bool)
    candidate[owner > 0] = True; candidate[3, 2:end] = True
    return dict(class_ids=cls, anime_classes=anime,
        source_alpha=np.full_like(cls, 255), frozen_candidate=candidate,
        frozen_owner=owner)


class TestSleeveContactSafe(unittest.TestCase):
    def test_single_owner_keeps_sleeve(self):
        x = scene(); a, r = propose_sleeve_contact_safe_shadow(**x)
        self.assertEqual(r['safe_added_px'], 4)
        self.assertEqual(r['Phase4'], 'FAIL')
    def test_dual_owner_never_creates_contact(self):
        x = scene(True); a, r = propose_sleeve_contact_safe_shadow(**x)
        self.assertTrue(np.array_equal(a[x['frozen_owner'] > 0], x['frozen_owner'][x['frozen_owner'] > 0]))
        self.assertEqual(ndimage.label(a == 1)[1], 1)
        self.assertEqual(ndimage.label(a == 2)[1], 1)
        self.assertGreater(r['safe_added_px'], 0)
        self.assertFalse(np.any(ndimage.binary_dilation(a == 1, structure=np.ones((3, 3))) & (a == 2)))
    def test_alpha_escape_rejected(self):
        x = scene(); x['source_alpha'][3, 3] = 0
        with self.assertRaises(Exception):
            propose_sleeve_contact_safe_shadow(**x)
    def test_no_input_mutation(self):
        x = scene(True); before = {k: v.copy() for k, v in x.items()}
        _, r = propose_sleeve_contact_safe_shadow(**x)
        for k, v in x.items():
            np.testing.assert_array_equal(v, before[k])
        self.assertEqual(r['frozen_owner_modified_px'], 0)


if __name__ == '__main__':
    unittest.main()
