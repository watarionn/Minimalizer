"""Source-free frontier safety regressions, not signed-image quality PASS."""
import unittest
import numpy as np
from tools.research.local_l02_class32_frontier_positive_shadow import (
    _frontier_safe_exclusive_assign,
    propose_pinned_run30_class32_frontier_positive,
)
from tools.research.local_l02_class32_topology_palette_shadow import SourceOnlyAbstentionHold


class FrontierShadowTest(unittest.TestCase):
    def test_single_owner_recovers_source_only_strip(self):
        o = np.zeros((18, 18), np.uint8)
        o[5:8, 3:6] = 1
        e = np.zeros(o.shape, bool)
        e[5:8, 6:10] = True
        got, receipt = _frontier_safe_exclusive_assign(e, o)
        self.assertEqual(receipt['assigned_positive_px'], 12)
        self.assertEqual(receipt['owner_components_before'], receipt['owner_components_after'])
        self.assertEqual(receipt['owner_enclosed_holes_before'], receipt['owner_enclosed_holes_after'])
        self.assertEqual(receipt['Phase4'], 'FAIL')
        self.assertFalse(receipt['uses_human_labels'])

    def test_competing_owners_do_not_make_new_contact(self):
        o = np.zeros((18, 18), np.uint8)
        o[5:8, 2:5] = 1
        o[5:8, 13:16] = 2
        e = np.zeros(o.shape, bool)
        e[5:8, 5:13] = True
        got, receipt = _frontier_safe_exclusive_assign(e, o)
        self.assertTrue(np.array_equal(got[o != 0], o[o != 0]))
        self.assertLess(receipt['assigned_positive_px'], int(e.sum()))
        self.assertEqual(receipt['owner_components_before'], receipt['owner_components_after'])
        for y, x in np.argwhere(got == 1):
            y0, y1 = max(0, y-1), min(got.shape[0], y+2)
            x0, x1 = max(0, x-1), min(got.shape[1], x+2)
            self.assertFalse(np.any(got[y0:y1, x0:x1] == 2))

    def test_original_enclosed_void_stays_empty(self):
        o = np.zeros((18, 18), np.uint8)
        o[3:13, 3:13] = 1
        o[6:10, 6:10] = 0
        e = np.zeros(o.shape, bool)
        e[6:10, 6:10] = True
        got, receipt = _frontier_safe_exclusive_assign(e, o)
        np.testing.assert_array_equal(got, o)
        self.assertEqual(receipt['abstained_original_enclosed_void_px'], 16)

    def test_open_u_cannot_become_new_hole(self):
        o = np.zeros((18, 18), np.uint8)
        o[3:13, 3] = 1
        o[3:13, 12] = 1
        o[12, 3:13] = 1
        e = np.zeros(o.shape, bool)
        e[3, 4:12] = True
        got, receipt = _frontier_safe_exclusive_assign(e, o)
        self.assertLess(receipt['assigned_positive_px'], int(e.sum()))
        self.assertEqual(receipt['owner_enclosed_holes_before'], receipt['owner_enclosed_holes_after'])

    def test_rejects_occupied_positive(self):
        o = np.zeros((6, 6), np.uint8)
        o[2, 2] = 1
        with self.assertRaisesRegex(SourceOnlyAbstentionHold, 'INVALID_FRONTIER'):
            _frontier_safe_exclusive_assign(o == 1, o)

    def test_rejects_nonpinned_case(self):
        with self.assertRaisesRegex(SourceOnlyAbstentionHold, 'UNPINNED'):
            propose_pinned_run30_class32_frontier_positive(
                case_id='unknown', source_bytes=b'',
                class_ids=np.zeros((3, 3), np.uint8),
                frozen_owner=np.zeros((3, 3), np.uint8))

if __name__ == '__main__':
    unittest.main()
