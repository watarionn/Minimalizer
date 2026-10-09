import unittest
import numpy as np
import cv2
from stage8_official_polygon_replay import official_mirror

def polygon(rings):
 return {"parameters":{"rings":rings}}
class CanonicalReplay(unittest.TestCase):
 def test_evenodd_hole_and_island(self):
  a=[dict(depth=0,role="fill",points=[[2,2],[18,2],[18,18],[2,18]]),
     dict(depth=1,role="hole",points=[[6,6],[11,6],[11,11],[6,11]]),
     dict(depth=0,role="fill",points=[[25,25]])]
  r=official_mirror(polygon(a))
  self.assertTrue(r[3,3]);self.assertFalse(r[8,8]);self.assertTrue(r[25,25])
 def test_role_depth_mismatch_fails(self):
  with self.assertRaises(ValueError):
   official_mirror(polygon([dict(depth=0,role="hole",points=[[1,1]])]))
 def test_alpha_guard_preserves_visible_evenodd_region(self):
  r=official_mirror(polygon([dict(depth=0,role="fill",points=[[2,2],[4,2],[4,4],[2,4]])]))
  alpha=np.ones((340,340),bool);alpha[3,3]=False
  self.assertFalse((r&alpha)[3,3]);self.assertTrue((r&alpha)[2,2])
if __name__=="__main__":unittest.main()
