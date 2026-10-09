import unittest
import numpy as np
from stage8_signed_owner_matrix import render, MODES

class SignedOwnerMatrixTests(unittest.TestCase):
 def test_hole_and_single_pixel_preserved_in_explicit_role(self):
  rings=[{"points":[[2,2],[10,2],[10,10],[2,10]],"depth":0,"role":"fill"},
         {"points":[[5,5],[7,5],[7,7],[5,7]],"depth":1,"role":"hole"},
         {"points":[[30,31]],"depth":0,"role":"fill"}]
  x=render(rings,"depthsorted_role")
  self.assertEqual(x[31,30],1)
  self.assertEqual(x[6,6],0)
  self.assertEqual(x[3,3],1)
 def test_reverse_order_can_change_hole_composition(self):
  rings=[{"points":[[2,2],[10,2],[10,10],[2,10]],"depth":0,"role":"fill"},
         {"points":[[5,5],[7,5],[7,7],[5,7]],"depth":1,"role":"hole"}]
  a=render(rings,"depthsorted_role")
  b=render(rings,"depthsorted_reverse_role")
  self.assertGreater(np.count_nonzero(a!=b),0)
 def test_strategies_do_not_return_release_decision(self):
  self.assertEqual(len(MODES),8)
  x=render([{"points":[[4,5]],"depth":0,"role":"fill"}],"original_role")
  self.assertEqual(int(np.count_nonzero(x)),1)

if __name__=="__main__":unittest.main()
