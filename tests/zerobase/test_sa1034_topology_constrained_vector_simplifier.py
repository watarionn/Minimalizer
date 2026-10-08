import unittest

import cv2
import numpy as np

from minimalizer_zerobase.reviewed_sa10.source_exact_vector_replay import evaluate_exact_replay
from minimalizer_zerobase.reviewed_sa10.topology_constrained_vector_simplifier import adapt_exact_contours
from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate


def template(owner):
    return {
        "primitive_id": f"src-{owner}",
        "primitive_type": "polygon",
        "composition_part": "__unbound__" if owner=="unknown" else owner,
        "semantic_part_id": None if owner=="unknown" else owner,
        "source_mask_owner": owner,
        "source_mask_replay": True,
        "source_evidence_refs": [f"phase04:part_masks/{owner}.png"],
        "palette_color_rgb": [10, 20, 30],
        "raster_index": 0,
        "parameters": {
            "components": [[[2,2],[5,2],[5,5],[2,5]]],
            "holes": [],
            "rings": [{"points": [[2,2],[5,2],[5,5],[2,5]],"depth":0,"role":"fill"}],
            "hole_preservation": "contour-tree-even-odd",
        },
    }


def fixtures():
    source = {}
    originals = []
    for index, owner in enumerate(("face", "hair", "left_arm", "right_arm", "unknown")):
        m = np.zeros((64, 64), np.uint8)
        x = index * 12
        cv2.rectangle(m, (x+1, 18), (x+8, 35), 1, -1)
        m[3, x+5] = 1
        m[25, x+4] = 0
        source[owner] = m
        originals.append(template(owner))
    exact, masks, report = evaluate_exact_replay(originals, source, width=64, height=64)
    return source, exact, masks, report


class ConstrainedVectorTests(unittest.TestCase):
    def test_adaptive_edits_keep_micro_islands_and_global_topology(self):
        source, exact, masks, first = fixtures()
        candidates, output, report = adapt_exact_contours(
            exact, masks, source, width=64, height=64,
            minimum_global_iou=0.99, minimum_owner_iou=0.99,
            original_ring_budget=first["old_vertices"]["ring_vertices"],
            original_component_budget=first["old_vertices"]["component_vertices"],
        )
        self.assertEqual(report["global_anatomy"]["gate"], "PASS")
        self.assertTrue(report["raw_owner_topology_pass"])
        self.assertTrue(report["tiny_source_islands_and_holes_preserved"])
        self.assertTrue(report["opencv_vector_render_parity"])
        self.assertFalse(report["promotion_authorized"])
        for record in candidates:
            name=record["source_mask_owner"]
            self.assertTrue(output[record["primitive_id"]][3, int(name=="hair")*12+5] if name=="hair" else True)
            self.assertTrue(np.array_equal(
                rasterize_primitive_candidate(record,width=64,height=64),output[record["primitive_id"]]
            ))

    def test_exact_required_iou_cannot_silently_mutate_masks(self):
        source, exact, masks, first = fixtures()
        before={k:v.copy() for k,v in masks.items()}
        candidates, output, report = adapt_exact_contours(
            exact, masks, source, width=64, height=64,
            minimum_global_iou=1.0, minimum_owner_iou=1.0,
            original_ring_budget=first["old_vertices"]["ring_vertices"],
            original_component_budget=first["old_vertices"]["component_vertices"],
        )
        self.assertEqual(report["global_anatomy"]["metrics"]["silhouette_iou"],1.0)
        self.assertTrue(all(np.array_equal(output[k],before[k]) for k in output))
        self.assertTrue(all(np.array_equal(masks[k],before[k]) for k in masks))
        self.assertFalse(report["promotion_authorized"])

    def test_below_original_silhouette_gate_rejected(self):
        source, exact, masks, first = fixtures()
        with self.assertRaises(ValueError):
            adapt_exact_contours(
                exact, masks, source, width=64, height=64,
                minimum_global_iou=0.90,
                original_ring_budget=first["old_vertices"]["ring_vertices"],
                original_component_budget=first["old_vertices"]["component_vertices"],
            )


if __name__ == "__main__":
    unittest.main()
