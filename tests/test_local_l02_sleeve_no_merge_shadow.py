"""Source-free topology regression, not semantic/Golden proof."""
import sys
from pathlib import Path
import unittest
import numpy as np
from scipy import ndimage
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'research'))
from local_l02_sleeve_no_merge_shadow import propose_sleeve_without_frozen_component_merges, SleeveNoMergeHold


def inputs(shape=(7,13)):
    owner=np.zeros(shape,dtype=np.uint8)
    cls=np.zeros(shape,dtype=np.uint8)
    anime=np.zeros(shape,dtype=np.uint8)
    alpha=np.full(shape,255,dtype=np.uint8)
    candidate=np.zeros(shape,dtype=bool)
    return cls,anime,alpha,candidate,owner


def call(args,conn=4):
    cls,anime,alpha,candidate,owner=args
    return propose_sleeve_without_frozen_component_merges(
        class_ids=cls,anime_classes=anime,source_alpha=alpha,
        frozen_candidate=candidate,frozen_owner=owner,connectivity=conn)


class SleeveNoMergeTests(unittest.TestCase):
    def test_bridge_rejected_but_most_eligible_sleeve_kept(self):
        a=inputs();cls,anime,alpha,cand,owner=a
        owner[3,1]=1;owner[3,11]=1;cls[3,1]=cls[3,11]=5
        cls[3,2:11]=32;anime[3,2:11]=10
        cand[3,1:12]=True
        out,meta=call(a)
        self.assertEqual(ndimage.label(out==1)[1],2)
        self.assertGreater(meta['safe_added_pixels'],0)
        self.assertLess(meta['safe_added_pixels'],9)
        np.testing.assert_array_equal(out[owner>0],owner[owner>0])
    def test_safe_single_seed_sleeve_kept(self):
        a=inputs();cls,anime,alpha,cand,owner=a
        owner[3,1]=1;cls[3,1]=5;cls[3,2:6]=32;anime[3,2:6]=10;cand[3,1:6]=True
        out,meta=call(a)
        self.assertEqual(meta['safe_added_pixels'],4)
        self.assertEqual(meta['removed_uncertain_additions'],0)
        self.assertEqual(ndimage.label(out==1)[1],1)
    def test_two_owners_never_reassigned(self):
        a=inputs();cls,anime,alpha,cand,owner=a
        owner[3,1]=1;owner[3,11]=2;cls[3,1]=5;cls[3,11]=10
        cls[3,2:11]=32;anime[3,2:11]=10;cand[3,1:12]=True
        out,meta=call(a)
        self.assertEqual(int(out[3,1]),1)
        self.assertEqual(int(out[3,11]),2)
        self.assertEqual(int(np.count_nonzero((out>0)&(owner==0))),meta['safe_added_pixels'])
    def test_diagonal_8_joins_are_cut(self):
        a=inputs((7,9));cls,anime,alpha,cand,owner=a
        owner[1,1]=1;owner[5,7]=1;cls[1,1]=cls[5,7]=5
        for y,x in [(2,2),(3,3),(4,4),(4,5),(5,6)]:
            cls[y,x]=32;anime[y,x]=10;cand[y,x]=True
        cand[owner>0]=True
        out,meta=call(a,8)
        self.assertEqual(ndimage.label(out==1,structure=np.ones((3,3)))[1],2)
        self.assertLess(meta['safe_added_pixels'],5)
    def test_invalid_alpha_rejected(self):
        a=inputs();cls,anime,alpha,cand,owner=a
        owner[3,1]=1;cls[3,1]=5;cand[3,1]=True;alpha[3,1]=0
        with self.assertRaises(Exception):call(a)
    def test_input_unchanged_and_deterministic(self):
        a=inputs();cls,anime,alpha,cand,owner=a
        owner[3,1]=1;owner[3,11]=1;cls[3,1]=cls[3,11]=5
        cls[3,2:11]=32;anime[3,2:11]=10;cand[3,1:12]=True
        snap=[x.copy() for x in a]
        x,m=call(a);y,n=call(a)
        np.testing.assert_array_equal(x,y);self.assertEqual(m,n)
        for p,q in zip(a,snap):np.testing.assert_array_equal(p,q)
        self.assertEqual(m['quality'],'FAIL')

if __name__=='__main__':unittest.main()
