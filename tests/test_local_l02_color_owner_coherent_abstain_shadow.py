"""Source-free safety tests; not proof of real-character quality."""
import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'research'))
from local_l02_color_owner_coherent_abstain_shadow import _largest_majority_veto

class CoherentVetoTests(unittest.TestCase):
    def test_majority_only(self):
        owner=np.ones((6,9),dtype=np.uint8)
        raw=owner.copy()
        raw[1:4,1:3]=0  # 6 connected
        raw[1:3,7:9]=0  # 4 connected
        result,n,largest=_largest_majority_veto(owner,raw)
        self.assertEqual((n,largest),(10,6))
        self.assertEqual(int(np.count_nonzero(result==0)),6)
        self.assertTrue(np.all(result[1:3,7:9]==1))
    def test_exact_half_rejects(self):
        owner=np.ones((6,9),dtype=np.uint8)
        raw=owner.copy();raw[1:3,1:3]=0;raw[1:3,7:9]=0
        result,n,largest=_largest_majority_veto(owner,raw)
        self.assertEqual((n,largest),(8,4))
        np.testing.assert_array_equal(result,owner)
    def test_no_change(self):
        owner=np.ones((5,5),dtype=np.uint8)
        result,n,largest=_largest_majority_veto(owner,owner.copy())
        self.assertEqual((n,largest),(0,0))
        np.testing.assert_array_equal(result,owner)
    def test_only_removes_original_owner(self):
        owner=np.array([[0,1,1,2,2,0],[0,1,1,2,2,0],[0,0,0,0,0,0]],dtype=np.uint8)
        raw=owner.copy();raw[0,1:3]=0;raw[1,1]=0
        result,_,_=_largest_majority_veto(owner,raw)
        self.assertTrue(np.all((result==0)|(result==owner)))
        self.assertTrue(np.all(result[owner==0]==0))

if __name__=='__main__':unittest.main()
