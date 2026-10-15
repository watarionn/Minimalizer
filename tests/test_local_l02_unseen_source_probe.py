"""Offline, synthetic, byte-authority and fail-closed transfer probe tests."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'/'research'))
from local_l02_unseen_source_probe import (
    SourceProbe, verify_exact_bytes, assess_transparency, raw_probe, release_gate, AuthorityHold)


class MockModel:
    def predict_proba(self, a):
        x=np.empty((len(a),2),np.float32)
        x[:,0]=.1;x[:,1]=.9
        return x


class Tests(unittest.TestCase):
    def setUp(self):
        self.img=np.zeros((320,220,4),np.uint8)
        self.img[30:290,35:195,:3]=[48,55,75]
        self.img[30:290,35:195,3]=255
        self.digest='a'*64

    def test_sha_matches(self):
        import hashlib
        a=b'yes';self.assertEqual(verify_exact_bytes(a,hashlib.sha256(a).hexdigest()),hashlib.sha256(a).hexdigest())
    def test_sha_mismatch_refused(self):
        with self.assertRaises(AuthorityHold): verify_exact_bytes(b'a','0'*64)
    def test_valid_source(self):
        a,b=assess_transparency(self.img);self.assertGreater(a,.1);self.assertLess(b,.01)
    def test_opaque_background_abstains(self):
        a=self.img.copy();a[:,:,3]=255
        r,p,s=raw_probe('TEST',a,self.digest,MockModel())
        self.assertEqual(r.status,'ABSTAIN');self.assertIsNone(p);self.assertIsNone(s)
    def test_background_border_abstains(self):
        a=self.img.copy();a[0,:,3]=255;a[-1,:,3]=255;a[:,0,3]=255;a[:,-1,3]=255
        r,p,s=raw_probe('TEST',a,self.digest,MockModel());self.assertEqual(r.status,'ABSTAIN')
    def test_rgba_required(self):
        with self.assertRaises(AuthorityHold):assess_transparency(self.img[:,:,:3])
    def test_no_missing_sha(self):
        with self.assertRaises(AuthorityHold):raw_probe('TEST',self.img,'',MockModel())
    def test_raw_probe_does_not_create_owner(self):
        r,p,s=raw_probe('TEST',self.img,self.digest,MockModel())
        self.assertEqual(r.status,'RAW_PROBE_ONLY');self.assertIsNone(r.semantic_iou)
        self.assertFalse(r.production_candidate);self.assertFalse(r.original_masks_available)
        self.assertEqual(r.positive_pixels,r.source_foreground_samples)
        self.assertEqual(s.shape[:2],p.shape)
    def test_source_only_support(self):
        r,p,s=raw_probe('TEST',self.img,self.digest,MockModel())
        self.assertFalse(np.any(p &(s[:,:,3]==0)))
    def test_bad_resources(self):
        with self.assertRaises(AuthorityHold):raw_probe('TEST',self.img,self.digest,MockModel(),max_dimension=3)
    def test_gate_denies_unlabelled(self):
        r,p,s=raw_probe('TEST',self.img,self.digest,MockModel())
        v=release_gate([r],0)
        self.assertEqual(v['status'],'HOLD');self.assertIsNone(v['semantic_iou'])
    def test_gate_refuses_fake_signed_labels(self):
        r,p,s=raw_probe('TEST',self.img,self.digest,MockModel())
        with self.assertRaises(AuthorityHold):release_gate([r],1)
    def test_gate_refuses_release_record(self):
        from dataclasses import replace
        r,p,s=raw_probe('TEST',self.img,self.digest,MockModel())
        with self.assertRaises(AuthorityHold):release_gate([replace(r,semantic_pass=True)],0)
    def test_nonfinite_probability_refuses(self):
        class BadModel:
            def predict_proba(self,x):return np.full((len(x),2),np.nan)
        with self.assertRaises(AuthorityHold):raw_probe('TEST',self.img,self.digest,BadModel())
    def test_probabilities_out_of_bounds_refused(self):
        class BadModel:
            def predict_proba(self,x):return np.full((len(x),2),4.)
        with self.assertRaises(AuthorityHold):raw_probe('TEST',self.img,self.digest,BadModel())

if __name__=='__main__':unittest.main()
