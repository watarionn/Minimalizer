"""Source-free regressions; these are not image quality or blind PASS."""
import unittest
import numpy as np
from tools.research.local_l02_class32_robust_frontier_shadow import (
    _robust_two_order_candidate,
    propose_pinned_run30_class32_robust_frontier_shadow,
)
from tools.research.local_l02_class32_topology_palette_shadow import SourceOnlyAbstentionHold
from unittest.mock import patch


class RobustFrontierTest(unittest.TestCase):
    def test_one_owner_strip_kept_unassessed(self):
        o = np.zeros((18, 18), np.uint8)
        o[5:8, 3:6] = 1
        p = np.zeros(o.shape, bool)
        p[5:8, 6:10] = True
        got, receipt = _robust_two_order_candidate(p, o)
        self.assertEqual(int(np.count_nonzero(got != o)), 12)
        self.assertEqual(receipt['quality'], 'UNASSESSED')
        self.assertEqual(receipt['Phase4'], 'FAIL')
        self.assertFalse(receipt['uses_human_labels'])

    def test_competing_owners_keep_ambiguous_gap(self):
        o = np.zeros((18, 30), np.uint8)
        o[5:8, 2:5] = 1
        o[5:8, 20:23] = 2
        p = np.zeros(o.shape, bool)
        p[5:8, 5:20] = True
        got, receipt = _robust_two_order_candidate(p, o)
        np.testing.assert_array_equal(got[o != 0], o[o != 0])
        self.assertLess(receipt['assigned_positive_px'], int(p.sum()))
        self.assertEqual(receipt['owner_topology_before'], receipt['owner_topology_after'])
        self.assertEqual(receipt['Phase4'], 'FAIL')

    def test_enclosed_void_preserved(self):
        o = np.zeros((18, 18), np.uint8)
        o[3:13, 3:13] = 1
        o[6:10, 6:10] = 0
        p = np.zeros(o.shape, bool)
        p[6:10, 6:10] = True
        got, receipt = _robust_two_order_candidate(p, o)
        np.testing.assert_array_equal(got, o)
        self.assertEqual(receipt['assigned_positive_px'], 0)

    def test_rejects_occupied_positive(self):
        o = np.zeros((6, 6), np.uint8)
        o[2, 2] = 1
        with self.assertRaisesRegex(SourceOnlyAbstentionHold, 'INVALID_ROBUST'):
            _robust_two_order_candidate(o == 1, o)

    def test_wrapper_uses_only_pinned_observer(self):
        o = np.zeros((18, 18), np.uint8)
        o[5:8, 3:6] = 1
        p = np.zeros(o.shape, bool)
        p[5:8, 6:10] = True
        evidence = {'source_class_owner_sha_pinned': True, 'reason': 'synthetic'}
        with patch('tools.research.local_l02_class32_robust_frontier_shadow.'
                   'propose_pinned_run30_class32_positive', return_value=(p, evidence)):
            got, receipt = propose_pinned_run30_class32_robust_frontier_shadow(
                case_id='synthetic', source_bytes=b'',
                class_ids=np.zeros(o.shape, np.uint8), frozen_owner=o)
        self.assertEqual(receipt['case'], 'synthetic')
        self.assertTrue(receipt['pinned_source_class_owner'])
        self.assertEqual(receipt['quality'], 'UNASSESSED')
        self.assertGreater(np.count_nonzero(got != o), 0)

    def test_two_order_disagreement_is_not_arbitrarily_assigned(self):
        o = np.zeros((18, 18), np.uint8)
        o[5:8, 3:6] = 1
        o[5:8, 13:16] = 2
        p = np.zeros(o.shape, bool)
        p[5:8, 6:13] = True
        forward = o.copy()
        reverse = o.copy()
        forward[6, 8] = 1
        reverse[6, 8] = 2
        with patch('tools.research.local_l02_class32_robust_frontier_shadow.'
                   '_ordered_growth', side_effect=[forward, reverse]):
            got, receipt = _robust_two_order_candidate(p, o)
        np.testing.assert_array_equal(got, o)
        self.assertEqual(receipt['two_order_disagreement_px'], 1)
        self.assertEqual(receipt['assigned_positive_px'], 0)

    def test_unreachable_positive_abstains(self):
        o = np.zeros((18, 18), np.uint8)
        o[2:4, 2:4] = 1
        p = np.zeros(o.shape, bool)
        p[12:14, 12:14] = True
        got, receipt = _robust_two_order_candidate(p, o)
        np.testing.assert_array_equal(got, o)
        self.assertEqual(receipt['abstained_positive_px'], 4)

    def test_invalid_dtype_fails_closed(self):
        o = np.zeros((6, 6), np.uint8)
        with self.assertRaisesRegex(SourceOnlyAbstentionHold, 'INVALID_ROBUST'):
            _robust_two_order_candidate(np.zeros(o.shape, np.uint8), o)


if __name__ == '__main__':
    unittest.main()
