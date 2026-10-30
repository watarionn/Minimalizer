"""Source-free negative tests for non-release composition; no human labels."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_composed_p0_shadow import propose_composed_p0_shadow, ComposedP0Hold


def scene():
    h, w = 16, 28
    classes = np.zeros((h, w), np.uint8)
    anime = np.zeros((h, w), np.uint8)
    owner = np.zeros((h, w), np.uint8)
    classes[3:11, 1:11] = 10
    owner[3:11, 1:11] = 2
    classes[7, 11:16] = 30
    anime[7, 11:16] = 10
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., 3] = 255
    rgba[3:11, 1:11, :3] = (200, 30, 30)
    return dict(source_rgba=rgba, class_ids=classes,
                anime_classes=anime, frozen_owner=owner)


class TestComposedP0(unittest.TestCase):
    def test_class30_reaches_coat_without_source_creation(self):
        x = scene()
        result, meta = propose_composed_p0_shadow(**x)
        self.assertEqual(int(np.count_nonzero(result == 2)), 85)
        self.assertEqual(meta['class30_added_pixels'], 5)
        self.assertEqual(meta['quality'], 'FAIL')
        self.assertEqual(meta['L03'], 'NO_GO')
        self.assertFalse(meta['human_annotations_used_for_inference'])
        self.assertFalse(meta['source_sha_verified_by_wrapper'])

    def test_ambiguous_whole_fragment_abstains(self):
        x = scene()
        x['frozen_owner'][3:11, 16:26] = 1
        x['class_ids'][3:11, 16:26] = 5
        x['source_rgba'][3:11, 16:26, :3] = (200, 30, 30)
        out, meta = propose_composed_p0_shadow(**x)
        self.assertEqual(meta['class30_added_pixels'], 0)
        self.assertTrue(np.array_equal(out, x['frozen_owner']))

    def test_two_incompatible_dominant_seed_hues_fail_closed(self):
        x = scene()
        x['frozen_owner'][3:11, 16:26] = 1
        x['class_ids'][3:11, 16:26] = 5
        x['source_rgba'][3:11, 16:26, :3] = (30, 40, 200)
        with self.assertRaisesRegex(ValueError, 'NO_DOMINANT_SEED_HUE'):
            propose_composed_p0_shadow(**x)

    def test_no_owner_promotion_outside_alpha(self):
        x = scene()
        x['source_rgba'][7, 12, 3] = 0
        out, _ = propose_composed_p0_shadow(**x)
        self.assertEqual(int(out[7, 12]), 0)

    def test_unknown_observer_class_fails_closed(self):
        x = scene()
        x['anime_classes'][0, 0] = 255
        with self.assertRaisesRegex(ComposedP0Hold, 'INVALID_OBSERVER_DOMAIN'):
            propose_composed_p0_shadow(**x)

    def test_frozen_owner_alpha_escape_fails_closed(self):
        x = scene()
        x['source_rgba'][3, 1, 3] = 0
        with self.assertRaisesRegex(ComposedP0Hold, 'FROZEN_OWNER_OUTSIDE_SOURCE'):
            propose_composed_p0_shadow(**x)

    def test_invalid_independent_model_shape_fails_closed(self):
        x = scene()
        x['independent_outerwear'] = np.zeros((3, 3), np.uint8)
        with self.assertRaisesRegex(ComposedP0Hold, 'INVALID_INDEPENDENT_OBSERVER'):
            propose_composed_p0_shadow(**x)

    def test_independent_model_dtype_fails_closed(self):
        x = scene()
        x['independent_outerwear'] = np.zeros((16, 28), bool)
        with self.assertRaisesRegex(ComposedP0Hold, 'INVALID_INDEPENDENT_OBSERVER'):
            propose_composed_p0_shadow(**x)

    def test_human_mask_argument_not_supported(self):
        x = scene()
        x['human_reference_mask'] = np.ones((16, 28), bool)
        with self.assertRaises(TypeError):
            propose_composed_p0_shadow(**x)


if __name__ == '__main__':
    unittest.main()
