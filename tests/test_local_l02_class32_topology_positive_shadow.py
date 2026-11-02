"""Source-free topology and abstention regression. No private images/masks."""
import unittest
import numpy as np
from scipy import ndimage as ndi

from tools.research.local_l02_class32_topology_positive_shadow import (
    _topology_safe_exclusive_assign, propose_pinned_run30_class32_topology_positive,
)
from tools.research.local_l02_class32_topology_palette_shadow import SourceOnlyAbstentionHold


class TopologyPositiveTest(unittest.TestCase):
    def test_unique_owner_component_grows_without_topology_change(self):
        o = np.zeros((16, 16), np.uint8)
        o[5:8, 3:6] = 1
        e = np.zeros_like(o, dtype=bool)
        e[5:8, 6:10] = True
        got, receipt = _topology_safe_exclusive_assign(e, o)
        self.assertEqual(int((got != o).sum()), 12)
        self.assertEqual(receipt['original_owner_4_8_components'], receipt['proposed_owner_4_8_components'])

    def test_two_semantic_owners_abstain(self):
        o = np.zeros((16, 16), np.uint8)
        o[5:8, 2:5] = 1
        o[5:8, 12:15] = 2
        e = np.zeros_like(o, dtype=bool)
        e[5:8, 5:12] = True
        got, receipt = _topology_safe_exclusive_assign(e, o)
        np.testing.assert_array_equal(got, o)
        self.assertEqual(receipt['assigned_positive_px'], 0)

    def test_two_components_same_owner_cannot_merge(self):
        o = np.zeros((16, 16), np.uint8)
        o[5:8, 2:5] = 1
        o[5:8, 12:15] = 1
        e = np.zeros_like(o, dtype=bool)
        e[5:8, 5:12] = True
        got, receipt = _topology_safe_exclusive_assign(e, o)
        np.testing.assert_array_equal(got, o)
        self.assertEqual(receipt['assigned_positive_px'], 0)

    def test_diagonal_only_contact_abstains_four_connected(self):
        o = np.zeros((8, 8), np.uint8)
        o[2, 2] = 1
        e = np.zeros_like(o, dtype=bool)
        e[3, 3] = True
        got, _ = _topology_safe_exclusive_assign(e, o)
        np.testing.assert_array_equal(got, o)

    def test_existing_enclosed_arm_opening_is_not_filled(self):
        # Owner component counts alone miss loss of a hole in the silhouette.
        o = np.zeros((16, 16), np.uint8)
        o[3:12, 3:12] = 1
        o[5:10, 5:10] = 0
        e = np.zeros_like(o, dtype=bool)
        e[5:10, 5:10] = True
        got, receipt = _topology_safe_exclusive_assign(e, o)
        np.testing.assert_array_equal(got, o)
        self.assertEqual(receipt['abstained_enclosed_void_px'], 25)
        self.assertEqual(receipt['original_owner_4_8_enclosed_holes'],
                         receipt['proposed_owner_4_8_enclosed_holes'])

    def test_new_enclosed_void_creation_fails_closed(self):
        # Closing an open U can create a new void without changing owner count.
        o = np.zeros((16, 16), np.uint8)
        o[3:12, 3] = 1
        o[3:12, 11] = 1
        o[11, 3:12] = 1
        e = np.zeros_like(o, dtype=bool)
        e[3, 4:11] = True
        with self.assertRaisesRegex(SourceOnlyAbstentionHold,
                                    'EXCLUSIVE_POSITIVE_TOPOLOGY_FAIL'):
            _topology_safe_exclusive_assign(e, o)

    def test_nonempty_occupied_evidence_rejected(self):
        o = np.zeros((8, 8), np.uint8)
        o[2, 2] = 1
        e = o == 1
        with self.assertRaisesRegex(SourceOnlyAbstentionHold, 'INVALID'):
            _topology_safe_exclusive_assign(e, o)

    def test_nonpinned_public_entry_rejected(self):
        with self.assertRaisesRegex(SourceOnlyAbstentionHold, 'UNPINNED'):
            propose_pinned_run30_class32_topology_positive(
                case_id='unknown', source_bytes=b'bad',
                class_ids=np.zeros((2, 2), np.uint8),
                frozen_owner=np.zeros((2, 2), np.uint8))


if __name__ == '__main__':
    unittest.main()
