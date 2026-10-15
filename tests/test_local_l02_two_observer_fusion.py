import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'research'))
from local_l02_two_observer_fusion import fuse_observers,quality_gate,AuthorityHold,PROTECTED
SHA='a'*64
OTHER='b'*64
class Tests(unittest.TestCase):
    def setUp(self):
        self.alpha=np.ones((30,25),bool)
        self.primary=np.zeros((30,25),bool);self.primary[10:20,5:20]=True
        self.labels=np.zeros((30,25),np.uint8);self.labels[10:20,8:19]=10
        self.protect={k:np.zeros((30,25),bool) for k in PROTECTED}
    def run_fusion(self,**patch):
        a=dict(primary=self.primary,secondary_classes=self.labels,source_alpha=self.alpha,
               signed_owner_union=self.alpha,
               protected=self.protect,primary_source_sha256=SHA,
               secondary_source_sha256=SHA,secondary_weights_sha256=OTHER)
        a.update(patch)
        return fuse_observers(**a)
    def test_ordinary(self):
        out,uncertain,m=self.run_fusion()
        self.assertGreater(out.sum(),0)
        self.assertFalse(m.production_authorized)
        self.assertFalse(m.semantic_quality_verified)
        self.assertEqual(m.foreground_xor_pixels,0)
    def test_difference_is_not_cleared(self):
        _,unknown,_=self.run_fusion()
        self.assertGreater(unknown.sum(),0)
    def test_different_source_abstain(self):
        with self.assertRaises(AuthorityHold):self.run_fusion(secondary_source_sha256=OTHER)
    def test_digests_required(self):
        with self.assertRaises(AuthorityHold):self.run_fusion(secondary_weights_sha256='')
    def test_missing_arm_refuses(self):
        p=self.protect.copy();p.pop('right_arm')
        with self.assertRaises(AuthorityHold):self.run_fusion(protected=p)
    def test_wrong_dtype_primary(self):
        with self.assertRaises(AuthorityHold):self.run_fusion(primary=self.primary.astype(np.uint8))
    def test_wrong_dtype_secondary(self):
        with self.assertRaises(AuthorityHold):self.run_fusion(secondary_classes=self.labels.astype(bool))
    def test_wrong_shape_refuses(self):
        with self.assertRaises(AuthorityHold):self.run_fusion(secondary_classes=self.labels[:20])
    def test_unknown_classes_refuse(self):
        x=self.labels.copy();x[0,0]=255
        with self.assertRaises(AuthorityHold):self.run_fusion(secondary_classes=x)
    def test_nonopaque_primary_refuses(self):
        a=self.alpha.copy();a[11,11]=False
        with self.assertRaises(AuthorityHold):self.run_fusion(source_alpha=a)
    def test_protected_arms_refuse(self):
        p={k:v.copy() for k,v in self.protect.items()};p['left_arm'][15,10]=True
        with self.assertRaises(AuthorityHold):self.run_fusion(protected=p)
    def test_unsigned_pixel_clipped(self):
        union=self.alpha.copy();union[12,10]=False
        out,unknown,_=self.run_fusion(signed_owner_union=union)
        self.assertFalse(out[12,10]);self.assertFalse(unknown[12,10])
    def test_missing_owner_union_refused(self):
        with self.assertRaises(AuthorityHold):self.run_fusion(signed_owner_union=np.zeros((3,4),bool))
    def test_no_hallucinated_foreground(self):
        p=self.primary.copy();p[0,0]=False
        a=self.alpha.copy();a[:,:4]=False
        out,unk,_=self.run_fusion(primary=p,source_alpha=a,signed_owner_union=a)
        self.assertFalse((out&~a).any());self.assertFalse((unk&~a).any())
    def test_large_dilation_refuses(self):
        with self.assertRaises(AuthorityHold):self.run_fusion(dilation=9)
    def test_bad_class_refuses(self):
        with self.assertRaises(AuthorityHold):self.run_fusion(clothes_id=3)
    def test_gate_holds(self):
        self.assertEqual(quality_gate({})['production_release'],'NO_GO')
    def test_fake_gate_refuses(self):
        with self.assertRaises(AuthorityHold):quality_gate({},unseen_jacket_truth=True)

if __name__=='__main__':unittest.main()
