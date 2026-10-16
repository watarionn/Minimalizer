"""Source-only sleeve-color candidate safety gates. Research, not production."""
import inspect
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"research"))
from local_l02_sleeve_color_attachment_shadow import propose,score,ResearchHold,CASES,OWNER_IDS,SLEEVE_ID

class SleeveColorTests(unittest.TestCase):
    def fixture(self):
        rgba=np.zeros((28,28,4),np.uint8)
        rgba[:,:,:3]=(40,60,80)
        rgba[2:26,2:26,3]=255
        ids=np.zeros((28,28),np.uint8)
        ids[8:16,12:19]=5
        ids[10:22,10:12]=32
        return rgba,ids
    def test_inference_never_accepts_human_masks(self):
        self.assertEqual(list(inspect.signature(propose).parameters),["rgba","classids"])
    def test_three_sources_pinned(self):
        self.assertEqual(set(CASES),{"H04","H06","H08"})
        self.assertEqual(OWNER_IDS,(5,10))
        self.assertEqual(SLEEVE_ID,32)
    def test_connected_matching_sleeve_is_proposal_only(self):
        rgba,ids=self.fixture()
        pred,info=propose(rgba,ids)
        self.assertTrue(pred[12,10])
        self.assertFalse(info["owner_promotion_authorized"])
        self.assertFalse(pred[0,0])
    def test_nonmatching_color_abstains(self):
        rgba,ids=self.fixture()
        rgba[ids==32,:3]=(230,240,220)
        pred,info=propose(rgba,ids)
        self.assertFalse(pred[12,10])
    def test_absent_outerwear_abstains(self):
        rgba,ids=self.fixture();ids[ids==5]=0
        pred,info=propose(rgba,ids)
        self.assertFalse(pred.any())
        self.assertEqual(info["decision"],"ABSTAIN_NO_OUTERWEAR_SEED")
    def test_unattached_sleeve_is_not_assigned(self):
        rgba,ids=self.fixture();ids[18:25,21:24]=32
        pred,info=propose(rgba,ids)
        self.assertFalse(pred[20,22])
    def test_reject_bad_class_map(self):
        rgba,ids=self.fixture()
        with self.assertRaises(ResearchHold):propose(rgba,ids.astype("int32"))
        with self.assertRaises(ResearchHold):propose(rgba,ids[:-1])
        ids[0,0]=255
        with self.assertRaises(ResearchHold):propose(rgba,ids)
    def test_mask_outside_alpha_is_never_generated(self):
        rgba,ids=self.fixture();ids[0,0]=32
        pred,info=propose(rgba,ids)
        self.assertFalse(np.any(pred&(rgba[:,:,3]==0)))
    def test_unknown_not_known_negative(self):
        rgba,ids=self.fixture()
        pred,info=propose(rgba,ids)
        alpha=rgba[:,:,3]>0
        pos=np.zeros_like(alpha);neg=np.zeros_like(alpha)
        pos[12,13]=True
        unk=alpha&~(pos|neg)
        stats=score(alpha,pos,neg,unk,pred,neg,neg)
        self.assertEqual(stats["known_negative_fp_rate"],0)
        self.assertGreater(stats["unknown_predicted_pixels"],0)
    def test_wrong_unknown_authority_rejected(self):
        rgba,ids=self.fixture()
        pred,info=propose(rgba,ids)
        alpha=rgba[:,:,3]>0
        mask=np.zeros_like(alpha)
        with self.assertRaises(ResearchHold):score(alpha,mask,mask,mask,pred,mask,mask)

if __name__=="__main__":unittest.main()
