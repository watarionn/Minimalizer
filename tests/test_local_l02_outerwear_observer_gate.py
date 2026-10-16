"""Source-free tests of exact-taxonomy and source-alpha observer hold."""
import hashlib,sys,unittest
from dataclasses import replace
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'research'))
from local_l02_outerwear_observer_gate import ObserverSpec,AuthorityHold,source_only_candidate,known_only_evaluation

class ObserverGateTests(unittest.TestCase):
 def fixture(self,labels=None):
  cl=np.zeros((16,12),dtype=np.uint8);cl[1:8,3:9]=10;cl[9:12,3:9]=5
  alpha=np.ones((16,12),dtype=bool);alpha[:,0:2]=False
  m={0:'background',5:'hair',10:'clothes'} if labels is None else labels
  sp=ObserverSpec('pinned-independent-model','a'*64,'b'*64,hashlib.sha256(cl.tobytes()).hexdigest(),m)
  return alpha,cl,sp
 def test_generic_clothes_is_abstention_not_owner(self):
  a,c,s=self.fixture();v,r=source_only_candidate(a,c,s)
  self.assertEqual(r['status'],'ABSTAIN_NO_OUTERWEAR_CLASS')
  self.assertFalse(v.any());self.assertFalse(r['owner_promotion_authorized'])
 def test_fine_grained_jacket_class_remains_research(self):
  a,c,s=self.fixture({0:'background',5:'hair',10:'jacket'})
  v,r=source_only_candidate(a,c,s)
  self.assertEqual(int(v.sum()),42)
  self.assertFalse(r['owner_promotion_authorized']);self.assertEqual(r['source_pixels_generated'],0)
 def test_outside_alpha_is_always_clipped(self):
  a,c,s=self.fixture({0:'background',5:'hair',10:'coat'})
  a[:,3]=False
  v,r=source_only_candidate(a,c,s)
  self.assertFalse((v&~a).any());self.assertEqual(int(v.sum()),35)
 def test_spoofed_non_specific_model_rejected(self):
  a,c,s=self.fixture({0:'background',5:'sleeve',10:'upper clothes'})
  v,r=source_only_candidate(a,c,s)
  self.assertEqual(r['status'],'ABSTAIN_NO_OUTERWEAR_CLASS')
 def test_class_map_tamper_rejected(self):
  a,c,s=self.fixture();c[0,0]=5
  with self.assertRaisesRegex(AuthorityHold,'CLASS_MAP_SHA_MISMATCH'):source_only_candidate(a,c,s)
 def test_unknown_class_rejected(self):
  a,c,s=self.fixture({0:'background',10:'jacket'})
  with self.assertRaisesRegex(AuthorityHold,'UNKNOWN_PREDICTED_CLASS'):source_only_candidate(a,c,s)
 def test_missing_model_digest_rejected(self):
  a,c,s=self.fixture()
  with self.assertRaisesRegex(AuthorityHold,'UNSIGNED'):source_only_candidate(a,c,replace(s,model_sha256=''))
 def test_shape_mismatch_rejected(self):
  a,c,s=self.fixture()
  with self.assertRaisesRegex(AuthorityHold,'INVALID_SOURCE'):source_only_candidate(a,c[:-1],s)
 def test_known_evaluation_does_not_score_unknown_negative(self):
  a,c,s=self.fixture();p=np.zeros_like(a);n=np.zeros_like(a);v=np.zeros_like(a)
  p[2,4]=True;n[2,5]=True;v[2,4]=True;v[4,4]=True
  z=known_only_evaluation(a,p,n,v)
  self.assertEqual(z['known_only_iou'],1.0)
  self.assertEqual(z['unknown_predicted_px'],1)
  self.assertFalse(z['unknown_are_negative'])
 def test_explicit_nonouterwear_is_negative(self):
  a,c,s=self.fixture();p=np.zeros_like(a);n=np.zeros_like(a);v=np.zeros_like(a)
  p[2,4]=True;n[2,5]=True;v[2,4]=True;v[2,5]=True
  z=known_only_evaluation(a,p,n,v)
  self.assertEqual(z['known_only_iou'],0.5);self.assertEqual(z['known_negative_fp_rate'],1)
 def test_evaluation_rejects_overlap(self):
  a,c,s=self.fixture();p=np.zeros_like(a);p[2,4]=True;n=p.copy()
  with self.assertRaisesRegex(AuthorityHold,'OVERLAPPING'):known_only_evaluation(a,p,n,np.zeros_like(a))
 def test_evaluation_rejects_generated_pixel(self):
  a,c,s=self.fixture();p=np.zeros_like(a);n=np.zeros_like(a);v=np.zeros_like(a);v[2,0]=True
  with self.assertRaisesRegex(AuthorityHold,'OUTSIDE_SIGNED_ALPHA'):known_only_evaluation(a,p,n,v)
if __name__=='__main__':unittest.main(verbosity=2)
