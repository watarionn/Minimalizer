import unittest

import cv2
import numpy as np

from minimalizer_zerobase.reviewed_sa10.phase7_geometry_authority import (
    component_loss_evidence, mask_fidelity, owner_fidelity, zorder_visibility,
)


class Phase7GeometryAuthorityTests(unittest.TestCase):
    def test_canonical_diagnostic_never_overrides_raw_loss(self):
        source = np.zeros((64, 64), np.uint8)
        cv2.rectangle(source, (12, 12), (52, 52), 1, -1)
        source[4, 4] = 1
        render = source.copy()
        render[4, 4] = 0
        evidence = owner_fidelity(source, render, render)
        self.assertFalse(evidence["raw_source_topology_pass"])
        self.assertFalse(evidence["source_to_render"]["exact"])
        self.assertTrue(evidence["diagnostic_canonical_source_to_render"]["exact"])
        self.assertEqual(evidence["lost_source_components_in_render"]["fully_missing_component_count"], 1)

    def test_export_drift_detected_even_when_topology_stable(self):
        source = np.zeros((32, 32), np.uint8)
        cv2.rectangle(source, (4, 4), (24, 24), 1, -1)
        export = source.copy()
        export[4, 4] = 0
        result = owner_fidelity(source, source, export)
        self.assertTrue(result["source_to_render"]["exact"])
        self.assertFalse(result["export_consistency_pass"])
        self.assertEqual(result["render_to_export"]["xor_pixels"], 1)

    def test_component_loss_reports_source_islands(self):
        source = np.zeros((32, 32), np.uint8)
        source[1, 1] = 1
        source[10:20, 10:20] = 1
        exported = np.zeros_like(source)
        exported[10:20, 10:20] = 1
        result = component_loss_evidence(source, exported, cutoff=8)
        self.assertEqual(result["fully_missing_component_count"], 1)
        self.assertEqual(result["fully_missing_pixels"], 1)
        self.assertEqual(result["fully_missing_below_threshold_pixels"], 1)
        self.assertEqual(result["damaged_components"][0]["bbox_xywh"], [1, 1, 1, 1])

    def test_zorder_retains_owner_visibility(self):
        a = np.zeros((8, 8), np.uint8)
        b = np.zeros((8, 8), np.uint8)
        a[2:6, 2:6] = 1
        b[4:7, 4:7] = 1
        records = [
            {"primitive_id": "arm", "semantic_part_id": "left_arm"},
            {"primitive_id": "top", "semantic_part_id": "major_clothing"},
        ]
        evidence = zorder_visibility(records, {"arm": a, "top": b})
        self.assertEqual(evidence["pre_face_guard_owner_visibility"]["left_arm"]["raw_pixels"], 16)
        self.assertEqual(evidence["pre_face_guard_owner_visibility"]["left_arm"]["visible_pixels"], 12)
        self.assertEqual(evidence["pre_face_guard_owner_visibility"]["major_clothing"]["visible_pixels"], 9)

    def test_unreplayable_owner_cannot_be_assumed(self):
        a = np.ones((8, 8), np.uint8)
        with self.assertRaises(ValueError):
            zorder_visibility([{"primitive_id": "missing"}], {"other": a})

    def test_tampered_canvas_rejected(self):
        with self.assertRaises(ValueError):
            mask_fidelity(np.zeros((8, 8), np.uint8), np.zeros((9, 9), np.uint8))


if __name__ == "__main__":
    unittest.main()
