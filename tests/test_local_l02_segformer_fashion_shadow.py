"""Deterministic source-free guards for noncommercial L02 SegFormer shadow."""
import io, json, sys, tempfile, unittest, inspect
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'research'))
from local_l02_segformer_fashion_shadow import (
 AuthorityHold,CLASSES,MODEL_REPO,REVISION,SOURCE_PINS,WEIGHTS_SHA,
 to_model_rgb,known_only_score,validate_model_dir,run,source_only_prediction
)

def fixture():
 a=np.zeros((12,16),np.uint8); a[2:10,3:13]=255
 rgba=np.zeros((12,16,4),np.uint8);rgba[:,:,:3]=[80,40,130];rgba[:,:,3]=a
 alpha=a>0
 pos=np.zeros_like(alpha);pos[3:7,4:8]=True
 neg=np.zeros_like(alpha);neg[6:9,9:12]=True
 return rgba,alpha,pos,neg

class ResearchGuards(unittest.TestCase):
 def test_pins_exact_three(self):
  self.assertEqual(set(SOURCE_PINS),{'H04','H06','H08'})
 def test_noncommercial_gate_always_fails_closed(self):
  with self.assertRaisesRegex(AuthorityHold,'NONCOMMERCIAL_RESEARCH_ONLY'):
   run(Path('unused'),Path('unused'),Path('unused'))
 def test_only_jacket_and_coat(self):
  self.assertEqual(CLASSES,{5:'jacket',10:'coat'})
 def test_source_transparency_cannot_generate_pixels(self):
  rgba,alpha,_,_=fixture()
  rgba[0,0,:3]=[200,100,10]
  rgb=to_model_rgb(rgba)
  self.assertEqual(tuple(rgb[0,0]),(255,255,255))
  self.assertEqual(tuple(rgb[3,5]),(80,40,130))
 def test_unknown_not_counted_as_negative(self):
  rgba,a,p,n=fixture();pred=p.copy();pred[3,9]=True
  s=known_only_score(a,p,n,pred)
  self.assertEqual(s['labelled_iou'],1.0)
  self.assertEqual(s['unknown_predicted_px'],1)
 def test_positive_and_negative_scored_only_if_labelled(self):
  _,a,p,n=fixture();pred=p|n
  s=known_only_score(a,p,n,pred)
  self.assertGreater(s['known_negative_fp_rate'],0.99)
  self.assertLess(s['labelled_iou'],1.0)
 def test_mask_overlap_rejected(self):
  _,a,p,n=fixture();n=p.copy()
  with self.assertRaisesRegex(AuthorityHold,'OVERLAPPING_HUMAN_LABELS'):
   known_only_score(a,p,n,np.zeros_like(a))
 def test_pixel_outside_original_rejected(self):
  _,a,p,n=fixture();out=p.copy();out[0,0]=True
  with self.assertRaisesRegex(AuthorityHold,'OUTSIDE_SIGNED_ALPHA'):
   known_only_score(a,p,n,out)
 def test_invalid_dtype_rejected(self):
  rgba,_,_,_=fixture()
  with self.assertRaisesRegex(AuthorityHold,'INVALID_RGBA'):
   to_model_rgb(rgba.astype(np.float32))
 def test_model_digest_missing_abstains(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(AuthorityHold,'PINNED_MODEL_FILES_MISSING'):
    validate_model_dir(Path(d))
 def test_source_only_inference_does_not_take_manual_labels(self):
  self.assertEqual(list(inspect.signature(source_only_prediction).parameters),['rgba','model','processor'])
 def test_frozen_model_authority(self):
  self.assertEqual(len(REVISION),40);self.assertEqual(len(WEIGHTS_SHA),64)
  self.assertEqual(MODEL_REPO,'sayeed99/segformer-b2-fashion')

if __name__=='__main__':unittest.main(verbosity=2)
