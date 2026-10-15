"""Fast fail-closed tests; does not rely on private H04 example."""
import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parents[1]/'tools'/'research'))
from local_l02_manual_supervised_shadow import (PARTS, PROTECTED, AuthorityHold,
  validate_masks,eligible_region,source_features,auto_guard,inference,
  postprocess_jacket_evidence,score,spatial_fold_masks)

class FixedMock:
    def predict_proba(self,X):
        z=np.zeros((len(X),2),np.float32);z[:,1]=.8;z[:,0]=.2;return z

class TestShadow(unittest.TestCase):
  def setUp(self):
    self.src=np.zeros((100,50,4),np.uint8)
    self.src[8:90,5:45,:3]=[22,30,50];self.src[8:90,5:45,3]=255
    self.m={k:np.zeros((100,50),bool) for k in PARTS}
    self.m['hair'][8:50,5:45]=True
    self.m['head'][8:49,5:45]=True
    self.m['neck'][47:56,18:33]=True
    self.m['torso'][50:90,5:45]=True
    self.m['face'][15:23,19:28]=True
    self.m['left_arm'][61:81,5:12]=True
    self.m['right_arm'][61:81,38:45]=True
    self.m['major_clothing'][50:88,12:38]=True
  def test_signed_shapes(self):validate_masks(self.src,self.m)
  def test_source_features_shape(self):self.assertEqual(source_features(self.src).shape,(100,50,18))
  def test_human_mask_not_in_inference_api(self):self.assertNotIn('human_jacket',inference.__code__.co_varnames[:inference.__code__.co_argcount])
  def test_guard_no_unsupported(self):
    output=inference(self.src,self.m,FixedMock());self.assertFalse(np.any(output&~eligible_region(self.src,self.m)))
    self.assertFalse(np.any(output&(~auto_guard(self.src,self.m))))
  def test_missing_neck_refuses(self):
    m={k:v.copy() for k,v in self.m.items()};m['neck'][:]=False
    with self.assertRaises(AuthorityHold):auto_guard(self.src,m)
  def test_outside_foreground_refuses(self):
    m={k:v.copy() for k,v in self.m.items()};m['hair'][0,0]=True
    with self.assertRaises(AuthorityHold):validate_masks(self.src,m)
  def test_missing_parts_refuses(self):
    m=dict(self.m);del m['face']
    with self.assertRaises(AuthorityHold):validate_masks(self.src,m)
  def test_protected_reclassification_refuses(self):
    mask=np.zeros((100,50),bool);mask[18,23]=True
    with self.assertRaises(AuthorityHold):postprocess_jacket_evidence(self.src,self.m,mask)
  def test_nonopaque_reclassification_refuses(self):
    mask=np.zeros((100,50),bool);mask[2,2]=True
    with self.assertRaises(AuthorityHold):postprocess_jacket_evidence(self.src,self.m,mask)
  def test_non_destructive_relabel_preserves_all_other_parts(self):
    proposed=np.zeros((100,50),bool);proposed[63:85,16:30]=True
    old={k:v.copy() for k,v in self.m.items()}
    new,evidence=postprocess_jacket_evidence(self.src,self.m,proposed)
    self.assertTrue(evidence.any())
    for key in PARTS:
      if key!='major_clothing':self.assertTrue(np.array_equal(new[key],old[key]),key)
      self.assertTrue(np.array_equal(self.m[key],old[key]),key)
    union=lambda x:np.logical_or.reduce([x[k] for k in PARTS])
    self.assertTrue(np.array_equal(union(new),union(old)))
  def test_tiny_islands_erased(self):
    m=np.zeros((100,50),bool);m[60,15]=True;m[60:70,18:30]=True
    out,e=postprocess_jacket_evidence(self.src,self.m,m,median_kernel=1,min_island=15)
    self.assertFalse(e[60,15]);self.assertTrue(e[65,24])
  def test_no_missing_hair_after_soft_overlay(self):
    m=np.zeros((100,50),bool);m[56:80,12:33]=True
    out,_=postprocess_jacket_evidence(self.src,self.m,m)
    self.assertTrue(np.array_equal(out['hair'],self.m['hair']))
    self.assertTrue(np.array_equal(out['head'],self.m['head']))
  def test_bad_median_kernel_refuses(self):
    with self.assertRaises(AuthorityHold):postprocess_jacket_evidence(self.src,self.m,np.zeros((100,50),bool),median_kernel=2)
  def test_score_exact(self):
    yy=np.array([True,False,True],bool);pp=np.array([True,True,False],bool)
    z=score(yy,pp);self.assertEqual((z['tp'],z['fp'],z['fn']),(1,1,1))
  def test_spatial_splits(self):
    z=spatial_fold_masks(100,50);self.assertTrue(np.all(z['train_viewer_left']!=z['train_viewer_right']))
  def test_untrusted_nonbinary_source(self):
    with self.assertRaises(AuthorityHold):source_features(self.src[:,:,:3])

if __name__=='__main__':unittest.main()
