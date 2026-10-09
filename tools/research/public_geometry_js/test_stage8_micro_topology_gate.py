import unittest
import numpy as np,cv2
from stage8_official_polygon_replay import official_mirror

class MicroTopologyRegression(unittest.TestCase):
 def test_bit_exact_raster_implies_component_and_hierarchy_parity(self):
  p={"parameters":{"rings":[
   {"depth":0,"role":"fill","points":[[2,2],[19,2],[19,19],[2,19]]},
   {"depth":1,"role":"hole","points":[[7,7],[12,7],[12,12],[7,12]]},
   {"depth":0,"role":"fill","points":[[30,30]]}
  ]}}
  source=official_mirror(p)
  current=official_mirror(p)
  self.assertTrue(np.array_equal(source,current))
  n1,_=cv2.connectedComponents(source.astype(np.uint8),8)
  n2,_=cv2.connectedComponents(current.astype(np.uint8),8)
  self.assertEqual(n1,n2)
  h1=cv2.findContours(source.astype(np.uint8),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)[1]
  h2=cv2.findContours(current.astype(np.uint8),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)[1]
  self.assertTrue(np.array_equal(h1,h2))
 def test_hole_removed_changes_source_raster(self):
  rings=[{"depth":0,"role":"fill","points":[[2,2],[19,2],[19,19],[2,19]]},
         {"depth":1,"role":"hole","points":[[7,7],[12,7],[12,12],[7,12]]}]
  all_owner=official_mirror({"parameters":{"rings":rings}})
  minus_hole=official_mirror({"parameters":{"rings":rings[:1]}})
  self.assertGreater(np.count_nonzero(all_owner!=minus_hole),0)
if __name__=="__main__":unittest.main()
