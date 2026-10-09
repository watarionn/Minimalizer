import unittest
import numpy as np
from stage8_large_ring_exact_reducer import reduce_owner
from stage8_official_polygon_replay import official_mirror

class ExactLargeRingReduction(unittest.TestCase):
 def test_reduction_keeps_all_source_owner_pixels(self):
  original={"parameters":{"rings":[{"depth":0,"role":"fill",
   "points":[[1,1],[4,1],[7,1],[10,1],[10,10],[1,10]]}]}}
  before=official_mirror(original)
  metrics,rings=reduce_owner(original,max_trials=100)
  after=official_mirror(dict(original,parameters=dict(original["parameters"],rings=rings)))
  self.assertTrue(np.array_equal(before,after))
  self.assertGreater(metrics["provenRemovable"],0)
  self.assertEqual(metrics["startVertices"]-metrics["endVertices"],metrics["provenRemovable"])
 def test_hole_does_not_get_silently_erased(self):
  p={"parameters":{"rings":[{"depth":0,"role":"fill","points":[[2,2],[20,2],[20,20],[2,20]]},
   {"depth":1,"role":"hole","points":[[8,8],[13,8],[13,13],[8,13]]}]}}
  before=official_mirror(p)
  _,rings=reduce_owner(p,max_trials=100)
  after=official_mirror(dict(p,parameters=dict(p["parameters"],rings=rings)))
  self.assertTrue(np.array_equal(before,after))
  self.assertFalse(after[10,10])
if __name__=="__main__":unittest.main()
