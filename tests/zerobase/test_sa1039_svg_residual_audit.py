import unittest

import cv2
import numpy as np

from tools.run_sa1039_svg_residual_audit import (
    _border, classify_residual_pixels,
)


class ChromeResidualAttributionTests(unittest.TestCase):
    def _source(self):
        expected=np.full((16,16,3),255,dtype=np.uint8)
        parent=np.zeros((16,16),bool)
        parent[2:12,2:12]=True
        masks=[np.zeros((16,16),bool) for _ in range(5)]
        masks[0][4:8,4:8]=True
        expected[masks[0]]=[20,35,65]
        actual=expected.copy()
        actual[4,4]=[255,255,255]
        actual[5,5]=[20,35,66]
        return expected,actual,parent,masks

    def test_occupancy_and_color_errors_are_accounted_separately(self):
        expected,actual,parent,masks=self._source()
        data,debug=classify_residual_pixels(
            authoritative_rgb=expected,chrome_rgb=actual,
            owner_mask=parent,material_masks=masks,
        )
        self.assertEqual(data["chrome_different_rgb_pixels"],2)
        self.assertEqual(data["occupancy_differences"],1)
        self.assertEqual(data["different_color_on_jointly_painted_pixels"],1)
        self.assertEqual(sum(data["source_owner_parent_boundary"].values()),2)
        self.assertEqual(data["pixel_disagreement_outside_signed_owner"],0)
        self.assertFalse(data["svg_exact_pixel_parity"])
        self.assertEqual(debug.shape,expected.shape)
        self.assertEqual(data["connected_mismatch_region_count"],1)

    def test_exactly_matching_browser_pixels_mean_only_audited_parity(self):
        expected,_,parent,masks=self._source()
        data,_=classify_residual_pixels(
            authoritative_rgb=expected,chrome_rgb=expected.copy(),
            owner_mask=parent,material_masks=masks,
        )
        self.assertTrue(data["svg_exact_pixel_parity"])
        self.assertEqual(data["chrome_different_rgb_pixels"],0)
        self.assertEqual(data["connected_mismatch_region_count"],0)

    def test_mismatched_canvas_or_unbound_material_masks_rejected(self):
        expected,actual,parent,masks=self._source()
        for parent_mask,materials,observed in (
            (parent,masks[:4],actual),
            (parent[:8,:8],masks,actual),
            (parent,masks,actual[:8,:8]),
        ):
            with self.subTest(case=len(materials)),self.assertRaises(ValueError):
                classify_residual_pixels(
                    authoritative_rgb=expected,chrome_rgb=observed,
                    owner_mask=parent_mask,material_masks=materials,
                )

    def test_edges_are_never_mutated_to_force_a_pass(self):
        source=np.zeros((8,8),bool)
        source[2:6,2:6]=True
        original=source.copy()
        edge=_border(source,margin=1)
        self.assertGreater(np.count_nonzero(edge),0)
        self.assertTrue(np.array_equal(source,original))


if __name__=="__main__":
    unittest.main()
