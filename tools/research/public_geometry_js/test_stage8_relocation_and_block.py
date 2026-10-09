import unittest
import numpy as np
from stage8_vertex_relocation import optimize as relocate
from stage8_block_replacement import optimize as block
from stage8_official_polygon_replay import official_mirror

class Stage8RelocationRegression(unittest.TestCase):
 def fixture(self):
  return {"parameters":{"rings":[
   {"depth":0,"role":"fill","points":[[2,2],[4,2],[6,2],[8,2],[10,2],[12,2],[14,2],[16,2],[16,16],[2,16]]},
   {"depth":1,"role":"hole","points":[[6,6],[11,6],[11,11],[6,11]]}]}}
 def test_two_to_one_exact(self):
  owner=self.fixture();before=official_mirror(owner)
  rings,_=relocate(owner,limit=1000)
  after=official_mirror(dict(owner,parameters=dict(owner["parameters"],rings=rings)))
  self.assertTrue(np.array_equal(before,after))
  self.assertFalse(after[8,8])
 def test_three_to_six_exact(self):
  owner=self.fixture();before=official_mirror(owner)
  rings,_=block(owner,budget=1000)
  after=official_mirror(dict(owner,parameters=dict(owner["parameters"],rings=rings)))
  self.assertTrue(np.array_equal(before,after))
  self.assertFalse(after[8,8])
if __name__=="__main__":unittest.main()
