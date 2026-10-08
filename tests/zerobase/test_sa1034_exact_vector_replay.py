import unittest
from copy import deepcopy

import cv2
import numpy as np

from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from minimalizer_zerobase.reviewed_sa10.source_exact_vector_replay import (
    evaluate_exact_replay, exact_source_bound_polygon,
)


def template(owner: str, *, unbound: bool = False, support_only: bool = False) -> dict:
    return {
        "primitive_id": f"primitive-{owner}",
        "primitive_type": "polygon",
        "composition_part": "__unbound__" if unbound else owner,
        "semantic_part_id": None if unbound else owner,
        "binding_status": "unbound" if unbound else "bound",
        "source_mask_owner": owner,
        "source_mask_replay": True,
        "source_evidence_refs": [f"phase04:part_masks/{owner}.png"],
        "palette_color_rgb": [100, 110, 120],
        "raster_index": 0,
        "structural_support_only": support_only,
        "parameters": {
            "components": [[[2., 2.], [5., 2.], [5., 5.], [2., 5.]]],
            "holes": [],
            "rings": [{"depth": 0, "role": "fill",
                       "points": [[2., 2.], [5., 2.], [5., 5.], [2., 5.]]}],
            "hole_preservation": "contour-tree-even-odd",
        },
    }


class SourceExactVectorReplayTests(unittest.TestCase):
    def setUp(self):
        self.source = np.zeros((48, 48), np.uint8)
        cv2.rectangle(self.source, (8, 8), (30, 30), 1, -1)
        cv2.rectangle(self.source, (16, 16), (20, 20), 0, -1)
        self.source[2, 2] = 1
        self.source[40:42, 42:44] = 1

    def test_exact_contour_preserves_holes_and_single_pixel_islands(self):
        original = template("hair")
        snapshot = deepcopy(original)
        candidate, observed, evidence = exact_source_bound_polygon(
            original, self.source, width=48, height=48
        )
        self.assertTrue(np.array_equal(observed, self.source.astype(bool)))
        self.assertGreater(evidence["degenerate_1_or_2_point_rings"], 0)
        self.assertTrue(evidence["owner_and_material_unchanged"])
        self.assertEqual(original, snapshot)
        self.assertTrue(np.array_equal(
            rasterize_primitive_candidate(candidate, width=48, height=48),
            observed,
        ))

    def test_unknown_part_remains_unbound(self):
        candidate, _, _ = exact_source_bound_polygon(
            template("unknown", unbound=True), self.source, width=48, height=48
        )
        self.assertIsNone(candidate["semantic_part_id"])
        self.assertEqual(candidate["composition_part"], "__unbound__")

    def test_unauthorized_owner_and_provenance_rejected(self):
        rogue = template("hair")
        rogue["semantic_part_id"] = "face"
        with self.assertRaises(ValueError):
            exact_source_bound_polygon(rogue, self.source, width=48, height=48)
        rogue = template("hair")
        rogue["source_evidence_refs"] = []
        with self.assertRaises(ValueError):
            exact_source_bound_polygon(rogue, self.source, width=48, height=48)

    def test_hard_budget_blocks_production_promotion(self):
        sources = {}
        existing = []
        for index, owner in enumerate(("hair", "face", "left_arm", "right_arm", "unknown")):
            mask = np.zeros((48, 48), np.uint8)
            cv2.rectangle(mask, (index * 7 + 1, 10), (index * 7 + 5, 25), 1, -1)
            mask[index, 45] = 1
            sources[owner] = mask
            existing.append(template(owner, unbound=owner=="unknown"))
        records, observed, report = evaluate_exact_replay(
            existing, sources, width=48, height=48
        )
        self.assertEqual(len(records), len(existing))
        self.assertEqual(len(observed), len(existing))
        self.assertEqual(report["full_anatomy"]["gate"], "PASS")
        self.assertTrue(report["source_raster_exact"])
        self.assertTrue(report["opencv_polygon_export_render_parity"])
        self.assertFalse(report["vertex_budget_pass"])
        self.assertIn("VERTEX_BUDGET_EXCEEDED", report["blockers"])
        self.assertIn("DEGENERATE_SVG_FILL_PATHS", report["blockers"])
        self.assertFalse(report["browser_svg_parity_verified"])
        self.assertFalse(report["promotion_authorized"])

    def test_missing_explicit_unknown_cannot_pass(self):
        with self.assertRaises(ValueError):
            evaluate_exact_replay(
                [template("hair")], {"hair": self.source}, width=48, height=48
            )


if __name__ == "__main__":
    unittest.main()
