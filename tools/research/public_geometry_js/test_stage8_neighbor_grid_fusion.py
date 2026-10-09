import unittest
import numpy as np
from stage8_neighbor_grid_fusion import reduce
from stage8_official_polygon_replay import official_mirror

class NeighborGridTests(unittest.TestCase):
 def test_source_raster_exact_with_hole(self):
  p={"parameters":{"rings":[
   {"depth":0,"role":"fill","points":[[2,2],[5,2],[8,2],[12,2],[16,2],[16,16],[2,16]]},
   {"depth":1,"role":"hole","points":[[7,7],[10,7],[10,10],[7,10]]}]}}
  before=official_mirror(p)
  rings,evidence=reduce(p,limit=2000)
  after=official_mirror(dict(p,parameters=dict(p["parameters"],rings=rings)))
  self.assertTrue(np.array_equal(before,after))
  self.assertFalse(after[8,8])
  self.assertEqual(sum(map(lambda x:len(x["points"]),p["parameters"]["rings"]))-sum(map(lambda x:len(x["points"]),rings)),evidence["saved"])
if __name__=="__main__":unittest.main()
