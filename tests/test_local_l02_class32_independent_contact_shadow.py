"""Source-only negative tests. No human masks, image coordinates or P0 claims."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_class32_independent_contact_shadow import (
    propose_independent_contact_shadow, IndependentContactHold)


def scene():
    h, w = 50, 60
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., :3] = (200, 80, 90)
    rgba[..., 3] = 255
    cls = np.zeros((h, w), np.uint8)
    anime = np.zeros((h, w), np.uint8)
    owner = np.zeros((h, w), np.uint8)
    cls[10:30, 5:19] = 5
    owner[10:30, 5:19] = 1
    cls[10:30, 19] = 32
    anime[10:30, 19] = 10
    owner[10:30, 19] = 1
    cls[10:30, 20:24] = 32
    anime[10:30, 20:24] = 11
    return dict(source_rgba=rgba, class_ids=cls,
                anime_classes=anime, baseline_owner=owner)


class TestIndependentContact(unittest.TestCase):
    def test_source_color_consistent_sleeve_admitted(self):
        x = scene()
        out, m = propose_independent_contact_shadow(**x)
        self.assertEqual(m['added_source_pixels_after_topology'], 80)
        self.assertTrue(np.all(out[10:30, 20:24] == 1))
        self.assertEqual(m['quality'], 'FAIL')
        self.assertFalse(m['human_annotations_used_for_inference'])

    def test_skin_colored_extension_abstains_as_whole(self):
        x = scene()
        x['source_rgba'][10:30, 20:24, :3] = (20, 220, 200)
        out, m = propose_independent_contact_shadow(**x)
        self.assertTrue(np.array_equal(out, x['baseline_owner']))
        self.assertEqual(m['color_incoherent_pixels_abstained'], 80)

    def test_mixed_arm_colored_subregion_must_not_be_promoted(self):
        # Negative: a 20% high-contrast region is not garment proof even if
        # the majority of a component matches a known sleeve anchor.
        x = scene()
        x['source_rgba'][10:14, 20:24, :3] = (20, 220, 200)
        out, m = propose_independent_contact_shadow(**x)
        self.assertTrue(np.all(out[10:14, 20:24] == 0),
                        'high-contrast possible arm pixels were promoted')
        self.assertEqual(m['quality'], 'FAIL')

    def test_dual_owner_contact_abstains_whole_fragment(self):
        x = scene()
        x['class_ids'][10:30, 24] = 10
        x['baseline_owner'][10:30, 24] = 2
        out, m = propose_independent_contact_shadow(**x)
        self.assertTrue(np.array_equal(out, x['baseline_owner']))
        self.assertEqual(m['ambiguous_dual_owner_pixels_abstained'], 80)

    def test_no_source_alpha_extension(self):
        x = scene()
        x['source_rgba'][10:30, 20:24, 3] = 0
        out, m = propose_independent_contact_shadow(**x)
        self.assertTrue(np.array_equal(out, x['baseline_owner']))
        self.assertEqual(m['added_source_pixels_after_topology'], 0)

    def test_invalid_observers_fail_closed(self):
        for key, value in (
            ('class_ids', scene()['class_ids'].astype(np.int16)),
            ('anime_classes', scene()['anime_classes'].astype(bool)),
            ('baseline_owner', scene()['baseline_owner'][:10]),
            ('source_rgba', scene()['source_rgba'][..., :3]),
        ):
            x = scene()
            x[key] = value
            with self.subTest(key=key), self.assertRaises(IndependentContactHold):
                propose_independent_contact_shadow(**x)

    def test_unknown_class_fails_closed(self):
        x = scene()
        x['anime_classes'][0, 0] = 255
        with self.assertRaisesRegex(IndependentContactHold, 'INVALID_DOMAIN'):
            propose_independent_contact_shadow(**x)

    def test_no_human_reference_input(self):
        x = scene()
        x['human_reference_mask'] = np.ones((50, 60), bool)
        with self.assertRaises(TypeError):
            propose_independent_contact_shadow(**x)

if __name__ == '__main__':
    unittest.main()
