"""Fast offline negative controls. No private originals or human polygon data."""
import unittest,sys,inspect
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'research'))
from benchmark_leave_character_out import sample_train,predict,score
from color_cluster_shadow import predict_outerwear_shadow
class AllClothes:
 def predict_proba(self,x):
  p=np.ones((x.shape[0],2),np.float32);p[:,0]=0
  return p
class NegativeControls(unittest.TestCase):
 def make(self,label):
  h=w=120
  pos=np.zeros((h,w),bool);pos[30:90,20:60]=True
  alpha=np.zeros((h,w),bool);alpha[10:110,10:110]=True
  features=np.zeros((h,w,18),np.float32)
  return {'case':label,'alpha':alpha,'positive':pos,'features':features,'negative':alpha&~pos,'known':alpha,'marked':alpha}
 def test_holdout_model_inference_does_not_accept_human_mask(self):
  self.assertEqual(list(inspect.signature(predict).parameters),['test','model'])
  self.assertEqual(list(inspect.signature(predict_outerwear_shadow).parameters),['rgba','classids'])
 def test_training_samples_have_both_classes(self):
  xs,ys,stat=sample_train([self.make('A'),self.make('B')],limit=700)
  self.assertEqual(len(ys),2800);self.assertEqual(int(np.count_nonzero(ys)),1400)
 def test_score_has_explicit_unknown_handling(self):
  d=self.make('A');p=d['alpha'].copy()
  d['known']=d['positive'];d['negative'][:]=False
  s=score(d,p)
  self.assertEqual(s['positive_recall'],1)
  self.assertGreater(s['unknown_predicted_px'],0)
 def test_predict_never_exits_signed_alpha(self):
  t=self.make('T');p=predict(t,AllClothes())
  self.assertFalse(np.any(p&~t['alpha']))
 def test_color_source_only_never_paints_transparent_pixels(self):
  a=np.zeros((120,120,4),np.uint8)
  a[10:110,10:110,3]=255
  yy,xx=np.indices((120,120));a[:,:,0]=xx*2;a[:,:,1]=yy*2;a[:,:,2]=100
  c=np.zeros((120,120),np.uint8);c[35:110,10:110]=10
  c[10:34,40:75]=2
  candidate,r=predict_outerwear_shadow(a,c)
  self.assertFalse(np.any(candidate&(a[:,:,3]==0)))
  self.assertEqual(r['source_pixels_generated'],0)
 def test_color_bad_dimensions_abstain(self):
  with self.assertRaises(ValueError):predict_outerwear_shadow(np.zeros((4,4,4),np.uint8),np.zeros((3,4),np.uint8))
if __name__=='__main__':unittest.main(verbosity=2)
