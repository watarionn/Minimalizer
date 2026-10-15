"""Synthetic/no-private-byte negative gates for canonical silhouette-scale diagnostics."""
import unittest,sys,hashlib
from pathlib import Path
import numpy as np
import cv2
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'research'))
from local_l02_scale_stable_probe import (AuthorityHold,foreground_frame,normalize_source,
    normalize_mask,project_mask,normalized_overlap,predict_source_bound,release_guard)

SHA=hashlib.sha256(b'unittest-fixed-demo').hexdigest()
class Mock:
    def predict_proba(self,x):
        p=np.full(len(x),.8)
        return np.stack([1-p,p],axis=1)

def feats(image):
    return np.zeros((*image.shape[:2],18),dtype=np.float32)

class ScaleTests(unittest.TestCase):
    def setUp(self):
        a=np.zeros((600,500,4),np.uint8)
        a[40:500,150:370,:3]=[20,30,40];a[40:500,150:370,3]=255
        self.src=a
    def test_canonical_subject_size(self):
        f=foreground_frame(self.src,SHA)
        self.assertEqual(f.analysis_height,900)
        self.assertLess(f.analysis_width,900)
        self.assertEqual(normalize_source(self.src,f).shape,(f.analysis_height,f.analysis_width,4))
    def test_signed_foreground_geometry(self):
        f=foreground_frame(self.src,SHA)
        pred,_=predict_source_bound(self.src,f,Mock(),feats)
        out=project_mask(pred,f,self.src[:,:,3]>0)
        self.assertFalse(np.any(out&~(self.src[:,:,3]>0)))
        self.assertGreater(out.sum(),0)
    def test_double_resolution_consistency(self):
        up=cv2.resize(self.src,(1000,1200),interpolation=cv2.INTER_NEAREST)
        f1=foreground_frame(self.src,SHA);f2=foreground_frame(up,SHA)
        self.assertLessEqual(abs(f1.analysis_width-f2.analysis_width),1)
        self.assertEqual(f1.analysis_height,f2.analysis_height)
    def test_project_mask_original_shape(self):
        f=foreground_frame(self.src,SHA)
        m=np.zeros(self.src.shape[:2],bool);m[75:300,155:350]=True
        mm=normalize_mask(m,f)
        self.assertEqual(project_mask(mm,f,self.src[:,:,3]>0).shape,self.src.shape[:2])
    def test_no_opaque_background(self):
        x=self.src.copy();x[:,:,3]=255
        with self.assertRaises(AuthorityHold):foreground_frame(x,SHA)
    def test_no_border_opaque(self):
        x=self.src.copy();x[0,:,3]=255;x[-1,:,3]=255;x[:,0,3]=255;x[:,-1,3]=255
        with self.assertRaises(AuthorityHold):foreground_frame(x,SHA)
    def test_small_fg(self):
        x=np.zeros_like(self.src);x[1:11,1:10,3]=255
        with self.assertRaises(AuthorityHold):foreground_frame(x,SHA)
    def test_no_sha(self):
        with self.assertRaises(AuthorityHold):foreground_frame(self.src,'')
    def test_bad_rgba(self):
        with self.assertRaises(AuthorityHold):foreground_frame(self.src[:,:,:3],SHA)
    def test_bad_source_dims(self):
        f=foreground_frame(self.src,SHA)
        with self.assertRaises(AuthorityHold):normalize_source(self.src[:10],f)
    def test_bad_mask_dtype(self):
        f=foreground_frame(self.src,SHA)
        with self.assertRaises(AuthorityHold):normalize_mask(np.zeros(self.src.shape[:2],np.uint8),f)
    def test_mismatched_predictions(self):
        f=foreground_frame(self.src,SHA)
        with self.assertRaises(AuthorityHold):project_mask(np.zeros((3,5),bool),f,self.src[:,:,3]>0)
    def test_invalid_probabilities(self):
        class NanModel:
            def predict_proba(self,x):return np.full((len(x),2),np.nan)
        f=foreground_frame(self.src,SHA)
        with self.assertRaises(AuthorityHold):predict_source_bound(self.src,f,NanModel(),feats)
    def test_invalid_params(self):
        f=foreground_frame(self.src,SHA)
        with self.assertRaises(AuthorityHold):predict_source_bound(self.src,f,Mock(),feats,threshold=1)
    def test_cross_source_compare_rejects(self):
        f=foreground_frame(self.src,SHA);g=foreground_frame(self.src,'b'*64)
        aa=np.zeros((f.analysis_height,f.analysis_width),bool)
        bb=np.zeros((g.analysis_height,g.analysis_width),bool)
        with self.assertRaises(AuthorityHold):normalized_overlap(aa,f,bb,g,self.src[:,:,3]>0)
    def test_same_source_compare(self):
        f=foreground_frame(self.src,SHA)
        mask=np.zeros((f.analysis_height,f.analysis_width),bool);mask[40:100,30:100]=1
        self.assertEqual(normalized_overlap(mask,f,mask,f,self.src[:,:,3]>0)['iou'],1.0)
    def test_gate_holds(self):
        self.assertEqual(release_guard(independent_character_labels=0,semantic_iou=None)['production_release'],'NO_GO')
    def test_gate_refuses_fake_iou(self):
        with self.assertRaises(AuthorityHold):release_guard(independent_character_labels=0,semantic_iou=.99)
    def test_invalid_target_height(self):
        with self.assertRaises(AuthorityHold):foreground_frame(self.src,SHA,target_height=1)

if __name__=='__main__':unittest.main()
