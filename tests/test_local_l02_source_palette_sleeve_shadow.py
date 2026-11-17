"""Synthetic source-free safety tests, NOT signed-image quality approval."""
import sys
import unittest
from pathlib import Path
import numpy as np
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_source_palette_sleeve_shadow import (
    propose_source_palette_sleeve_shadow, PaletteSleeveHold,
)


def scene(color_width=25):
    h, w = 100, 100
    rgba = np.empty((h, w, 4), dtype=np.uint8)
    rgba[..., :3] = (110, 150, 180)
    rgba[..., 3] = 255
    cls = np.zeros((h, w), np.uint8)
    anime = np.zeros_like(cls)
    owner = np.zeros_like(cls)
    cls[20:80, 1] = 5
    owner[20:80, 1] = 1
    cls[20:80, 2:35] = 32
    anime[20:80, 2:35] = 10
    cls[20:80, 35:35+color_width] = 32
    anime[20:80, 35:35+color_width] = 11
    return dict(source_rgba=rgba, class_ids=cls, anime_classes=anime,
                frozen_candidate=np.isin(cls, (5, 10, 32)), frozen_owner=owner)


class TestSourcePaletteSleeve(unittest.TestCase):
    def test_coherent_color_region_recovers_source_only_pixels(self):
        x = scene()
        snapshot = {k:v.copy() for k,v in x.items()}
        out, meta = propose_source_palette_sleeve_shadow(**x)
        self.assertGreater(meta['color_added_pixels'], 1000)
        self.assertEqual(int(out[50, 50]), 1)
        self.assertFalse(meta['semantic_quality_pass'])
        self.assertEqual(meta['source_pixels_generated'], 0)
        self.assertEqual(meta['L03'], 'NO_GO')
        self.assertEqual(ndimage.label(out == 1)[1], ndimage.label(x['frozen_owner'] == 1)[1])
        for key in x:
            np.testing.assert_array_equal(x[key], snapshot[key])

    def test_small_ambiguous_color_region_stays_abstained(self):
        x = scene(color_width=6)  # 360 px, below fixed 1024 px gate
        out, meta = propose_source_palette_sleeve_shadow(**x)
        self.assertEqual(meta['color_added_pixels'], 0)
        self.assertEqual(int(out[50, 37]), 0)
        self.assertEqual(int(out[50, 10]), 1)

    def test_no_trusted_observer_returns_existing_safe_baseline(self):
        x = scene()
        x['anime_classes'][x['anime_classes'] == 10] = 11
        out, meta = propose_source_palette_sleeve_shadow(**x)
        self.assertFalse(meta['color_policy_applied'])
        np.testing.assert_array_equal(out, x['frozen_owner'])

    def test_invalid_alpha_fails_closed(self):
        x = scene()
        x['source_rgba'][30, 1, 3] = 0
        with self.assertRaises(Exception):
            propose_source_palette_sleeve_shadow(**x)

    def test_invalid_classes_and_shapes_fail_closed(self):
        for name, value in (
            ('class_ids', np.full((100,100), 99, dtype=np.uint8)),
            ('anime_classes', np.full((100,100), 99, dtype=np.uint8)),
            ('frozen_candidate', np.zeros((100,100), dtype=np.uint8)),
            ('frozen_owner', np.zeros((90,100), dtype=np.uint8)),
            ('source_rgba', np.zeros((100,100,3), dtype=np.uint8)),
        ):
            with self.subTest(name=name):
                x = scene()
                x[name] = value
                with self.assertRaises(Exception):
                    propose_source_palette_sleeve_shadow(**x)


    def test_color_bridge_does_not_merge_distinct_frozen_components(self):
        x = scene()
        x['class_ids'][:] = 0
        x['anime_classes'][:] = 0
        x['frozen_owner'][:] = 0
        x['class_ids'][20:80, 1] = 5
        x['class_ids'][20:80, 98] = 5
        x['frozen_owner'][20:80, 1] = 1
        x['frozen_owner'][20:80, 98] = 1
        x['class_ids'][20:80, 2:98] = 32
        x['anime_classes'][20:80, 2:40] = 10
        x['anime_classes'][20:80, 60:98] = 10
        x['anime_classes'][20:80, 40:60] = 11
        x['frozen_candidate'] = np.isin(x['class_ids'], (5, 10, 32))
        out, meta = propose_source_palette_sleeve_shadow(**x)
        for connectivity in (1, 2):
            structure = ndimage.generate_binary_structure(2, connectivity)
            self.assertEqual(ndimage.label(out == 1, structure=structure)[1], 2)
        np.testing.assert_array_equal(out[x['frozen_owner'] > 0],
                                      x['frozen_owner'][x['frozen_owner'] > 0])
        self.assertEqual(meta['L02'], 'HOLD')

    def test_replay_is_deterministic_and_does_not_draw_faces(self):
        x = scene()
        a, meta_a = propose_source_palette_sleeve_shadow(**x)
        b, meta_b = propose_source_palette_sleeve_shadow(**x)
        np.testing.assert_array_equal(a, b)
        self.assertEqual(meta_a, meta_b)
        self.assertEqual(int(np.count_nonzero(a & (x['class_ids'] != 32) & (x['frozen_owner'] == 0))), 0)


if __name__ == '__main__':
    unittest.main()
