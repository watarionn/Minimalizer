import unittest
import numpy as np
from stage8_multi_point_exact import optimize
from stage8_official_polygon_replay import official_mirror

class MultiPointRegression(unittest.TestCase):
 def test_polygon_reduction_has_exact_owner_raster(self):
  part={"parameters":{"rings":[{"depth":0,"role":"fill",
   "points":[[2,2],[4,2],[6,2],[8,2],[10,2],[12,2],[14,2],[14,14],[2,14]]}]}}
  before=official_mirror(part)
  stat,rings=optimize(part,max_trials=1000,max_span=5)
  after=official_mirror(dict(part,parameters=dict(part["parameters"],rings=rings)))
  self.assertTrue(np.array_equal(before,after))
  self.assertEqual(stat["originalVertices"]-stat["candidateVertices"],stat["removedVertices"])
 def test_hole_survives_all_accepted_moves(self):
  part={"parameters":{"rings":[
   {"depth":0,"role":"fill","points":[[1,1],[5,1],[9,1],[15,1],[15,15],[1,15]]},
   {"depth":1,"role":"hole","points":[[5,5],[10,5],[10,10],[5,10]]}]}}
  baseline=official_mirror(part)
  _,rings=optimize(part,max_trials=1000)
  output=official_mirror(dict(part,parameters=dict(part["parameters"],rings=rings)))
  self.assertTrue(np.array_equal(baseline,output))
  self.assertFalse(output[7,7])
if __name__=="__main__":unittest.main()
