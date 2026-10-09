import unittest
from pyclipper_owner_diagnostics import inspect_clip_geometry

class ClipperOwnerDiagnosticsTests(unittest.TestCase):
    def test_simple_rectangle_area(self):
        rings=[{"depth":0,"role":"fill","points":[[0,0],[10,0],[10,10],[0,10]]}]
        result=inspect_clip_geometry(rings)
        self.assertEqual(result["validPaths"],1)
        self.assertEqual(result["unionPathCount"],1)
        self.assertAlmostEqual(abs(result["netArea"]),100.0)
    def test_hole_evenodd_and_degenerate_rings(self):
        rings=[{"depth":0,"role":"fill","points":[[0,0],[10,0],[10,10],[0,10]]},
               {"depth":1,"role":"hole","points":[[2,2],[8,2],[8,8],[2,8]]},
               {"depth":0,"role":"fill","points":[[3,3]]}]
        result=inspect_clip_geometry(rings)
        self.assertEqual(result["validPaths"],2)
        self.assertEqual(result["skippedDegenerateRings"],1)
        self.assertEqual(result["unionPathCount"],2)
        self.assertAlmostEqual(abs(result["netArea"]),64.0)
if __name__=="__main__":unittest.main()
