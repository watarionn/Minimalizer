import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_taxonomy_conflict_postscore import audit_postscore_taxonomy, TaxonomyConflictHold

class TestTaxonomyConflict(unittest.TestCase):
    def scene(self):
        cls=np.array([[10,25,7,0],[10,32,25,0]],dtype=np.uint8)
        owner=np.array([[2,0,0,0],[2,0,0,0]],dtype=np.uint8)
        alpha=np.full_like(cls,255)
        positive=np.array([[1,1,0,0],[1,0,1,0]],dtype=bool)
        negative=np.array([[0,0,1,0],[0,1,0,0]],dtype=bool)
        return dict(class_ids=cls,frozen_owner=owner,source_alpha=alpha,
                    reviewed_outerwear=positive,reviewed_known_negative=negative)
    def test_conflict_preserves_review(self):
        x=self.scene();orig=x['reviewed_outerwear'].copy()
        r=audit_postscore_taxonomy(**x)
        self.assertEqual(r['bag_wallet_vs_outerwear_review_conflict_px'],2)
        self.assertEqual(r['bag_wallet_review_status'],'REVIEW_REQUIRED')
        self.assertEqual(r['reviewed_outerwear_missing_total_px'],2)
        self.assertTrue(np.array_equal(orig,x['reviewed_outerwear']))
        self.assertEqual(r['Phase4'],'FAIL')
    def test_unknown_not_negative(self):
        x=self.scene();r=audit_postscore_taxonomy(**x)
        self.assertEqual(r['reviewed_outerwear_missing_by_class']['0']['unknown_unscored_px'],2)
        self.assertEqual(r['reviewed_outerwear_missing_by_class']['0']['known_negative_wrong_owner_px'],0)
    def test_disjoint_label_required(self):
        x=self.scene();x['reviewed_known_negative'][0,1]=True
        with self.assertRaisesRegex(TaxonomyConflictHold,'OVERLAPPING_HUMAN_LABELS'):
            audit_postscore_taxonomy(**x)
    def test_outside_source_rejected(self):
        x=self.scene();x['source_alpha'][0,1]=0
        with self.assertRaisesRegex(TaxonomyConflictHold,'POSTSCORE_OUTSIDE_SOURCE'):
            audit_postscore_taxonomy(**x)
    def test_owner_outside_source_rejected(self):
        x=self.scene();x['source_alpha'][0,0]=0
        with self.assertRaisesRegex(TaxonomyConflictHold,'OWNER_OUTSIDE_SOURCE'):
            audit_postscore_taxonomy(**x)
    def test_wrong_type_rejected(self):
        x=self.scene();x['reviewed_outerwear']=x['reviewed_outerwear'].astype(np.uint8)
        with self.assertRaisesRegex(TaxonomyConflictHold,'INVALID_POSTSCORE_MASKS'):
            audit_postscore_taxonomy(**x)
