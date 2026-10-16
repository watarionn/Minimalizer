import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'research'))
from local_l02_deepfashion2_shadow import preprocess_rgba,decode_source_only,ResearchHold
class DeepFashionShadowTests(unittest.TestCase):
 def fixture(self,cls=3,conf=.6):
  src=np.zeros((80,40,4),np.uint8);src[10:75,5:35,3]=255
  t,meta=preprocess_rgba(src)
  rows=np.zeros((300,38),np.float32);proto=np.zeros((32,104,104),np.float32)
  rows[0,:6]=[50,100,300,350,conf,cls];rows[0,6]=10
  proto[0,:,:]=1
  return src,t,meta,rows,proto
 def test_source_preprocess_fixed_and_aspect_preserved(self):
  s,t,m,r,p=self.fixture();self.assertEqual(t.shape,(1,3,416,416));self.assertEqual(m[2:],(208,416))
 def test_source_alpha_clip_even_inside_bbox(self):
  s,t,m,r,p=self.fixture();v,z=decode_source_only(r,p,m,s[:,:,3]>0)
  self.assertFalse(np.any(v&(s[:,:,3]==0)));self.assertGreater(v.sum(),0)
  self.assertFalse(z['owner_promotion_authorized'])
 def test_non_outerwear_never_promoted(self):
  s,t,m,r,p=self.fixture(cls=7);v,z=decode_source_only(r,p,m,s[:,:,3]>0)
  self.assertFalse(v.any());self.assertEqual(z['outwear_instances'],0)
 def test_low_confidence_rejected(self):
  s,t,m,r,p=self.fixture(conf=.49);v,z=decode_source_only(r,p,m,s[:,:,3]>0)
  self.assertFalse(v.any());self.assertEqual(z['outwear_instances'],0)
 def test_bad_output_shape_fail_closed(self):
  s,t,m,r,p=self.fixture()
  with self.assertRaises(ResearchHold):decode_source_only(r[:1],p,m,s[:,:,3]>0)
 def test_nonfinite_output_fail_closed(self):
  s,t,m,r,p=self.fixture();p[0,0,0]=np.nan
  with self.assertRaises(ResearchHold):decode_source_only(r,p,m,s[:,:,3]>0)
 def test_invalid_bbox_rejected(self):
  s,t,m,r,p=self.fixture();r[0,2]=10
  v,z=decode_source_only(r,p,m,s[:,:,3]>0)
  self.assertEqual(z['invalid_boxes'],1);self.assertFalse(v.any())
if __name__=='__main__':unittest.main(verbosity=2)
