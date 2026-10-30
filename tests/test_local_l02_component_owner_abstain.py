"""Synthetic-only source component ownership tests; no user data."""
import copy
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_component_owner_abstain import propose_component_owners, ComponentOwnerHold


def sample():
    cls = np.zeros((5, 7), dtype=np.uint8)
    cls[1, 1] = 5; cls[1, 2] = 32
    cls[3, 4] = 10; cls[3, 5] = 32
    return dict(class_ids=cls, source_alpha=np.full(cls.shape, 255, np.uint8),
                candidate=np.isin(cls, (5, 10, 32)))


class ComponentOwnerTests(unittest.TestCase):
    def setUp(self):
        self.d = sample()

    def run_gate(self, connectivity=4):
        return propose_component_owners(**self.d, connectivity=connectivity)

    def hold(self, code):
        with self.assertRaisesRegex(ComponentOwnerHold, code):self.run_gate()

    def test_separate_seed_owners(self):
        o, r = self.run_gate()
        self.assertEqual((o[1, 1], o[1, 2], o[3, 4], o[3, 5]), (1, 1, 2, 2))
        self.assertEqual(r['assigned_sleeve_px'], 2)

    def test_status_never_pass(self):
        _, r = self.run_gate()
        self.assertEqual((r['L02'],r['Golden'],r['production']),('HOLD','HOLD','NO_GO'))
        self.assertFalse(r['independent_holdout_proven'])
        self.assertFalse(r['annotation_used_for_inference'])

    def test_no_input_mutation(self):
        old=copy.deepcopy(self.d);self.run_gate()
        for k in old:np.testing.assert_array_equal(self.d[k],old[k])

    def test_orphan_abstains(self):
        self.d['class_ids'][4, 0]=32;self.d['candidate'][4, 0]=True
        o,r=self.run_gate()
        self.assertEqual(o[4,0],0)
        self.assertEqual(r['orphan_components'],1)

    def test_ambiguous_abstains(self):
        self.d['class_ids'][1,3]=10;self.d['candidate'][1,3]=True
        o,r=self.run_gate()
        self.assertEqual(o[1,2],0)
        self.assertEqual(r['ambiguous_components'],1)

    def test_diagonal_4_vs_8(self):
        self.d['class_ids'][1,2]=0;self.d['candidate'][1,2]=False
        self.d['class_ids'][2,2]=32;self.d['candidate'][2,2]=True
        a,ar=self.run_gate(4);b,br=self.run_gate(8)
        self.assertEqual(a[2,2],0)
        self.assertEqual(b[2,2],1)
        self.assertEqual(ar['orphan_components'],1)
        self.assertEqual(br['orphan_components'],0)

    def test_seed_not_selected_does_not_attach(self):
        self.d['candidate'][1,1]=False
        o,r=self.run_gate()
        self.assertEqual(o[1,2],0)
        self.assertEqual(r['orphan_components'],1)

    def test_unselected_sleeve_remains_abstain(self):
        self.d['candidate'][1,2]=False
        o,r=self.run_gate()
        self.assertEqual(o[1,2],0)
        self.assertEqual(r['sleeve_components'],1)

    def test_empty_candidate(self):
        self.d['candidate'][:]=False
        o,r=self.run_gate()
        self.assertEqual(int(o.sum()),0)
        self.assertEqual(r['sleeve_components'],0)

    def test_alpha_partial_preserved(self):
        self.d['source_alpha'][1,2]=128
        o,r=self.run_gate()
        self.assertEqual(o[1,2],1)

    def test_alpha_zero_reject(self):
        self.d['source_alpha'][1,2]=0
        self.hold('CANDIDATE_OUTSIDE_SOURCE_ALPHA')

    def test_transparent_background_allowed(self):
        self.d['source_alpha'][0,0]=0
        self.assertEqual(self.run_gate()[1]['assigned_sleeve_px'],2)

    def test_other_class_candidate_reject(self):
        self.d['class_ids'][0,0]=4;self.d['candidate'][0,0]=True
        self.hold('NON_OUTERWEAR_CANDIDATE')

    def test_invalid_class_dtype(self):
        self.d['class_ids']=self.d['class_ids'].astype(np.int32)
        self.hold('INVALID_CLASS_IDS')

    def test_invalid_class_ndim(self):
        self.d['class_ids']=self.d['class_ids'][None,:,:]
        self.hold('INVALID_CLASS_IDS')

    def test_invalid_alpha_dtype(self):
        self.d['source_alpha']=self.d['source_alpha'].astype(np.int32)
        self.hold('INVALID_SOURCE_ALPHA')

    def test_invalid_alpha_shape(self):
        self.d['source_alpha']=self.d['source_alpha'][:4]
        self.hold('INVALID_SOURCE_ALPHA')

    def test_invalid_candidate_dtype(self):
        self.d['candidate']=self.d['candidate'].astype(np.uint8)
        self.hold('INVALID_CANDIDATE')

    def test_invalid_candidate_shape(self):
        self.d['candidate']=self.d['candidate'][:4]
        self.hold('INVALID_CANDIDATE')

    def test_invalid_connectivity(self):
        with self.assertRaisesRegex(ComponentOwnerHold,'INVALID_CONNECTIVITY'):
            self.run_gate(6)

    def test_boolean_connectivity_rejected(self):
        with self.assertRaisesRegex(ComponentOwnerHold,'INVALID_CONNECTIVITY'):
            self.run_gate(True)

    def test_diagonal_8_conflicting_seeds_abstain(self):
        self.d['class_ids'][1,2]=0;self.d['candidate'][1,2]=False
        self.d['class_ids'][2,2]=32;self.d['candidate'][2,2]=True
        self.d['class_ids'][2,3]=10;self.d['candidate'][2,3]=True
        o,r=self.run_gate(8)
        self.assertEqual(o[2,2],0)
        self.assertEqual(r['ambiguous_components'],1)

    def test_same_owner_component_assignment(self):
        self.d['class_ids'][1,3]=32;self.d['candidate'][1,3]=True
        o,r=self.run_gate()
        self.assertEqual(o[1,3],1)
        self.assertEqual(r['assigned_sleeve_px'],3)

    def test_no_wraparound(self):
        self.d['class_ids'][1,2]=0;self.d['candidate'][1,2]=False
        self.d['class_ids'][1,6]=32;self.d['candidate'][1,6]=True
        o,r=self.run_gate()
        self.assertEqual(o[1,6],0)
        self.assertEqual(r['orphan_components'],1)

    def test_output_uint8(self):
        o,_=self.run_gate()
        self.assertEqual(o.dtype,np.uint8)


if __name__=='__main__':unittest.main()
