import unittest

import cv2
import numpy as np

from tools.run_sa1032_gc001_real_contour_eval import (
    compare_part, evaluate, rasterize_primitive,
)


def polygon(owner, shape=((2, 2), (21, 2), (21, 21), (2, 21)), holes=()):
    rings = [{"depth": 0, "points": list(shape)}]
    rings.extend({"depth": 1, "points": list(hole)} for hole in holes)
    return {
        "semantic_part_id": owner,
        "composition_part": owner,
        "source_mask_replay": True,
        "source_mask_owner": owner,
        "primitive_id": "test-" + owner,
        "palette_color_rgb": [12, 34, 56],
        "parameters": {
            "components": [list(shape)],
            "rings": rings,
            "hole_preservation": "contour-tree-even-odd",
        },
    }


class RealGC001ContourTests(unittest.TestCase):
    def test_contour_tree_hole_replayed(self):
        primitive = polygon("face", holes=[((8, 8), (15, 8), (15, 15), (8, 15))])
        mask = rasterize_primitive(primitive, (24, 24))
        self.assertTrue(mask[3, 3])
        self.assertFalse(mask[10, 10])
        self.assertEqual(compare_part(mask, mask)["source_topology"], [1, 1])

    def test_unreflected_missing_pixel(self):
        p = polygon("face")
        mask = rasterize_primitive(p, (24, 24))
        altered = mask.copy()
        altered[3, 3] = False
        m = compare_part(mask, altered)
        self.assertGreater(m["missing_source_pixels"], 0)
        self.assertLess(m["iou"], 1)

    def test_missing_ring_semantics_fails_closed(self):
        p = polygon("hair")
        p["parameters"]["hole_preservation"] = "unknown"
        with self.assertRaises(ValueError):
            rasterize_primitive(p, (24, 24))

    def test_global_hard_gate_stays_hold(self):
        owners = ("face", "hair", "left_arm", "right_arm")
        records = [polygon(owner) for owner in owners]
        scene = {
            "coordinate_space": {"pixel_width": 24, "pixel_height": 24},
            "selected_name": "aggressive",
            "candidates": [{"name": "aggressive", "metrics": {"primitive_count": 4}, "primitives": records}],
        }
        masks = {p["semantic_part_id"]: rasterize_primitive(p, (24, 24)) for p in records}
        prior = {"baseline": {"anatomy": {"gate": "FAIL", "hard_failures": ["source_topology_changed"]}}}
        result = evaluate(scene, masks, prior_benchmark=prior)
        self.assertEqual(result["status"], "HOLD_PREVIOUS_GLOBAL_HARD_GATE")
        self.assertFalse(result["promotion_authorized"])
        self.assertEqual(result["research_candidates"], 0)
        self.assertEqual(result["parts"]["left_arm"]["status"], "OBSERVE_ONLY_PROTECTED_ARM")

    def test_selected_count_disagreement_fails(self):
        p = polygon("face")
        scene = {
            "coordinate_space": {"pixel_width": 24, "pixel_height": 24},
            "selected_name": "aggressive",
            "candidates": [{"name": "aggressive", "metrics": {"primitive_count": 11}, "primitives": [p]}],
        }
        with self.assertRaises(ValueError):
            evaluate(scene, {"face": rasterize_primitive(p, (24, 24))})


if __name__ == "__main__":
    unittest.main()
