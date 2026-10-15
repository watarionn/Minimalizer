from __future__ import annotations
import unittest,hashlib,sys,io
from PIL import Image
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'research'))
from local_l02_flip_consistency_gate import AuthorityHold,flip_agreement,verify_rgba,probabilities
class Constant:
 def predict_proba(self,x):
  p=np.full(len(x),.9,np.float32);return np.stack([1-p,p],axis=1)
class LeftOnly:
 def predict_proba(self,x):
  p=np.where(x[:,0]<.48,.9,.1).astype(np.float32);return np.stack([1-p,p],axis=1)
class Nan:
 def predict_proba(self,x):return np.full((len(x),2),np.nan,np.float32)
def features(a):
 x=np.arange(a.shape[1],dtype=np.float32)[None,:]/max(1,a.shape[1]-1)
 return np.broadcast_to(x[:,:,None],(*a.shape[:2],1)).copy()
class Tests(unittest.TestCase):
 def setUp(self):
  self.img=np.zeros((90,60,4),np.uint8);self.img[5:85,5:55,3]=255;self.img[5:85,5:55,:3]=[30,40,50];self.alpha=self.img[:,:,3]>0;buf=io.BytesIO();Image.fromarray(self.img).save(buf,format='PNG');self.raw=buf.getvalue()
 def test_valid_signed_image(self):self.assertEqual(verify_rgba(self.img,self.raw,hashlib.sha256(self.raw).hexdigest()).shape,(90,60))
 def test_bad_sha(self):
  with self.assertRaises(AuthorityHold):verify_rgba(self.img,self.raw,'a'*64)
 def test_incorrect_array_with_genuine_original_bytes(self):
  changed=self.img.copy();changed[20,22,:3]=[250,1,77]
  with self.assertRaises(AuthorityHold):verify_rgba(changed,self.raw,hashlib.sha256(self.raw).hexdigest())
 def test_wrong_source_channels(self):
  with self.assertRaises(AuthorityHold):verify_rgba(self.img[:,:,:3],self.raw,hashlib.sha256(self.raw).hexdigest())
 def test_same_predictor_consistent_not_semantic(self):
  r,a,b=flip_agreement(self.img,Constant(),features,self.alpha)
  self.assertEqual(r['flip_iou'],1);self.assertEqual(r['status'],'DIAGNOSTIC_CONSISTENT_NOT_SEMANTIC_PASS');self.assertFalse(r['semantic_quality_verified']);self.assertFalse(b.any());self.assertEqual(a.sum(),self.alpha.sum())
 def test_flip_sensitive_rejected(self):
  r,a,b=flip_agreement(self.img,LeftOnly(),features,self.alpha)
  self.assertEqual(r['status'],'ABSTAIN_UNSTABLE_OR_SPARSE');self.assertLess(r['flip_iou'],.1)
 def test_source_only(self):
  r,a,b=flip_agreement(self.img,Constant(),features,self.alpha)
  self.assertFalse((a&~self.alpha).any());self.assertFalse((b&~self.alpha).any());self.assertEqual(r['source_pixels_generated'],0)
 def test_mask_outside_alpha_refused(self):
  x=self.alpha.copy();x[0,0]=True
  with self.assertRaises(AuthorityHold):flip_agreement(self.img,Constant(),features,x)
 def test_nan_probabilities_rejected(self):
  with self.assertRaises(AuthorityHold):flip_agreement(self.img,Nan(),features,self.alpha)
 def test_empty_allowed_refused(self):
  with self.assertRaises(AuthorityHold):flip_agreement(self.img,Constant(),features,np.zeros_like(self.alpha))
 def test_threshold_guard(self):
  with self.assertRaises(AuthorityHold):flip_agreement(self.img,Constant(),features,self.alpha,threshold=1.1)
 def test_malformed_feature_rejected(self):
  with self.assertRaises(AuthorityHold):flip_agreement(self.img,Constant(),lambda s:np.zeros((4,6,2)),self.alpha)
 def test_no_false_quality_gate(self):
  r,_,_=flip_agreement(self.img,Constant(),features,self.alpha)
  self.assertEqual(r['production_release'],'NO_GO')
if __name__=='__main__':unittest.main()
