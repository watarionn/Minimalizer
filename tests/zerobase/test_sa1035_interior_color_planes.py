import unittest

import numpy as np
import cv2

from minimalizer_zerobase.reviewed_sa10.interior_color_planes import (
    INTERIOR_RESEARCH_SCHEMA, propose_interior_plane,
    rasterize_interior_plane, render_with_interior_planes,
)


class InteriorColorPlaneTests(unittest.TestCase):
    def setUp(self):
        self.rgb = np.full((80, 80, 3), [45, 50, 55], np.uint8)
        self.rgb[23:52, 23:52] = [230, 185, 83]
        self.parent = np.zeros((80, 80), bool)
        self.parent[10:68, 10:68] = True
        self.protected = np.zeros((80, 80), bool)
        self.protected[35:40, 35:40] = True

    def propose(self, owner="major_clothing"):
        return propose_interior_plane(
            owner=owner, parent_primitive_id="p-clothing",
            source_rgb=self.rgb, owner_mask=self.parent,
            parent_palette_rgb=[45, 50, 55],
            protected_mask=self.protected, min_pixels=55,
        )

    def test_large_observed_source_color_plane_improves_error(self):
        result = self.propose()
        self.assertIsNotNone(result)
        proposal, raster = result
        self.assertEqual(proposal["schema"], INTERIOR_RESEARCH_SCHEMA)
        self.assertGreater(proposal["relative_lab_mse_reduction"], 0.10)
        self.assertLessEqual(proposal["polygon_vertex_count"], 28)
        self.assertTrue(proposal["additional_geometric_subpath"])
        self.assertIn(tuple(proposal["observed_rgb"]), set(map(tuple, self.rgb.reshape(-1, 3))))
        self.assertFalse(np.any(raster & ~self.parent))
        self.assertFalse(np.any(raster & self.protected))
        self.assertTrue(np.array_equal(
            rasterize_interior_plane(proposal, width=80, height=80,
                                     parent_mask=self.parent, protected_mask=self.protected),
            raster,
        ))

    def test_face_arms_and_unbound_never_eligible(self):
        for owner in ("face", "left_arm", "right_arm", "unknown", "neck"):
            self.assertIsNone(self.propose(owner=owner))

    def test_no_redundant_plane_when_source_is_flat(self):
        flat = np.full((80, 80, 3), [45, 50, 55], np.uint8)
        result = propose_interior_plane(
            owner="hair", parent_primitive_id="hair",
            source_rgb=flat, owner_mask=self.parent,
            parent_palette_rgb=[45, 50, 55], protected_mask=self.protected,
            min_pixels=55,
        )
        self.assertIsNone(result)

    def test_all_changes_clipped_and_face_arm_pixels_unchanged(self):
        proposal, raster = self.propose()
        mask2 = np.zeros_like(self.parent)
        mask2[38:65, 52:70] = True
        records = [
            {"primitive_id": "p-clothing", "semantic_part_id": "major_clothing",
             "palette_color_rgb": [45, 50, 55]},
            {"primitive_id": "p-arm", "semantic_part_id": "left_arm",
             "palette_color_rgb": [200, 130, 120]},
        ]
        raw = {"p-clothing": self.parent, "p-arm": mask2}
        baseline, enhanced, color_mask = render_with_interior_planes(
            primitives=records, primitive_masks=raw, planes=[proposal],
            protected_mask=self.protected | mask2,
        )
        self.assertFalse(np.any(color_mask & self.protected))
        self.assertFalse(np.any(color_mask & mask2))
        self.assertTrue(np.array_equal(baseline[self.protected], enhanced[self.protected]))
        self.assertTrue(np.array_equal(baseline[mask2], enhanced[mask2]))
        self.assertTrue(np.array_equal(baseline[~(self.parent | mask2)], enhanced[~(self.parent | mask2)]))
        self.assertTrue(np.any(baseline != enhanced))

    def test_no_extra_subplanes_or_false_parent_allowed(self):
        proposal, _ = self.propose()
        records = [{"primitive_id": "p-clothing",
                    "semantic_part_id": "major_clothing",
                    "palette_color_rgb": [45, 50, 55]}]
        with self.assertRaises(ValueError):
            render_with_interior_planes(
                primitives=records, primitive_masks={"p-clothing": self.parent},
                planes=[proposal, proposal], protected_mask=self.protected,
            )
        bogus = {**proposal, "parent_primitive_id": "does-not-exist"}
        with self.assertRaises(ValueError):
            render_with_interior_planes(
                primitives=records, primitive_masks={"p-clothing": self.parent},
                planes=[bogus], protected_mask=self.protected,
            )

    def test_consistent_identical_inputs(self):
        first = self.propose()
        second = self.propose()
        self.assertIsNotNone(first)
        self.assertEqual(first[0], second[0])
        self.assertTrue(np.array_equal(first[1], second[1]))

    def test_unverified_polygon_coordinates_rejected(self):
        proposal, _ = self.propose()
        bad = {**proposal, "points": [[1, 2], [3, 4]]}
        with self.assertRaises(ValueError):
            rasterize_interior_plane(bad, width=80, height=80,
                                     parent_mask=self.parent, protected_mask=self.protected)


if __name__ == "__main__":
    unittest.main()
