"""Source-free frozen owner topology negatives; no human labels or image data."""
import unittest
import numpy as np
from tools.research.local_l02_component_join_gate import (
    audit_owner_component_joins, ComponentJoinHold,
)


class ComponentJoinGateTests(unittest.TestCase):
    def scene(self):
        old = np.zeros((9, 11), np.uint8)
        old[4, 1:3] = 1
        old[4, 8:10] = 1
        return dict(source_alpha=np.full_like(old, 255),
                    frozen_owner=old, proposed_owner=old.copy())

    def test_noop_never_promotes_semantic_pass(self):
        result = audit_owner_component_joins(**self.scene())
        self.assertFalse(result["topology_review_required"])
        self.assertFalse(result["semantic_quality_pass"])

    def test_two_old_components_join(self):
        x = self.scene()
        x["proposed_owner"][4, 3:8] = 1
        result = audit_owner_component_joins(**x)
        self.assertTrue(result["topology_review_required"])
        self.assertEqual(result["component_witnesses"]["owner1_4"]["merged_component_groups"], 1)

    def test_diagonal_join_only_eight_neighbor(self):
        x = self.scene()
        x["proposed_owner"][3, 3:8] = 1
        result = audit_owner_component_joins(**x)
        self.assertEqual(result["component_witnesses"]["owner1_4"]["merged_component_groups"], 0)
        self.assertEqual(result["component_witnesses"]["owner1_8"]["merged_component_groups"], 1)

    def test_new_island_requires_review(self):
        x = self.scene()
        x["proposed_owner"][1, 5] = 1
        result = audit_owner_component_joins(**x)
        self.assertTrue(result["topology_review_required"])
        self.assertEqual(result["component_witnesses"]["owner1_4"]["new_island_components"], 1)
        self.assertEqual(result["component_witnesses"]["owner1_4"]["new_island_pixels"], 1)

    def test_four_neighbor_island_eight_neighbor_attached(self):
        x = self.scene()
        x["proposed_owner"][3, 3] = 1
        result = audit_owner_component_joins(**x)
        self.assertEqual(result["component_witnesses"]["owner1_4"]["new_island_components"], 1)
        self.assertEqual(result["component_witnesses"]["owner1_8"]["new_island_components"], 0)

    def test_owner_without_any_seed_is_island(self):
        x = self.scene()
        x["frozen_owner"][:] = 0
        x["proposed_owner"][:] = 0
        x["proposed_owner"][2, 4:7] = 2
        result = audit_owner_component_joins(**x)
        self.assertTrue(result["topology_review_required"])
        self.assertEqual(result["component_witnesses"]["owner2_4"]["new_island_pixels"], 3)

    def test_frozen_owner_change_rejected(self):
        x = self.scene()
        x["proposed_owner"][4, 1] = 2
        with self.assertRaisesRegex(ComponentJoinHold, "FROZEN_OWNER_CHANGED"):
            audit_owner_component_joins(**x)

    def test_source_alpha_violation_rejected(self):
        x = self.scene()
        x["source_alpha"][4, 4] = 0
        x["proposed_owner"][4, 4] = 1
        with self.assertRaisesRegex(ComponentJoinHold, "OWNER_OUTSIDE_SOURCE"):
            audit_owner_component_joins(**x)

    def test_dtype_and_shape_rejected(self):
        x = self.scene()
        x["source_alpha"] = x["source_alpha"].astype(bool)
        with self.assertRaisesRegex(ComponentJoinHold, "INVALID_UINT8_ARRAY"):
            audit_owner_component_joins(**x)
        x = self.scene()
        x["source_alpha"] = x["source_alpha"][:-1]
        with self.assertRaisesRegex(ComponentJoinHold, "SHAPE_MISMATCH"):
            audit_owner_component_joins(**x)

    def test_replay_is_deterministic_and_immutable(self):
        x = self.scene()
        frozen = x["proposed_owner"].copy()
        self.assertEqual(audit_owner_component_joins(**x),
                         audit_owner_component_joins(**x))
        np.testing.assert_array_equal(x["proposed_owner"], frozen)


if __name__ == "__main__":
    unittest.main()
