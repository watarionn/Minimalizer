import unittest
import numpy as np
from stage8_micro_ring_delete_trial import raster

class MicroReplayTests(unittest.TestCase):
 def test_singleton_is_visible_and_removal_changes_pixel(self):
  ring={"depth":0,"points":[[5,6]]}
  present=raster([ring])
  removed=raster([])
  self.assertEqual(int(present[6,5]),1)
  self.assertEqual(int(np.count_nonzero(present!=removed)),1)
 def test_two_point_ring_is_visible_and_removal_changes_pixel(self):
  ring={"depth":0,"points":[[5,6],[6,6]]}
  present=raster([ring])
  removed=raster([])
  self.assertGreater(int(np.count_nonzero(present!=removed)),0)
 def test_hole_is_not_an_authorization_to_remove_ring(self):
  outer={"depth":0,"points":[[2,2],[9,2],[9,9],[2,9]]}
  hole={"depth":1,"points":[[4,4],[6,4],[6,6],[4,6]]}
  baseline=raster([outer,hole])
  missing_hole=raster([outer])
  self.assertGreater(int(np.count_nonzero(baseline!=missing_hole)),0)
if __name__=="__main__":unittest.main()
