"""SA10.43 fail-closed and vertex accounting tests (no production changes)."""
import copy
from pathlib import Path
import sys
import unittest
from xml.etree import ElementTree as ET

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import sa1043_boundary_compaction as stage


class Stage1043Tests(unittest.TestCase):
    def test_holes_diagonal_islands_and_border_pixel_paths(self):
        mask=np.zeros((340,340),dtype=bool)
        mask[5:30,5:40]=True
        mask[10:20,10:20]=False
        mask[30,40]=True  # corner contact must not bridge blank diagonal
        mask[0,0]=True
        loops=stage.pixel_edge_loops(mask)
        self.assertGreaterEqual(len(loops),4)
        for loop in loops:
            self.assertGreaterEqual(len(loop),4)
            for x,y in loop:
                self.assertTrue(0<=x<=340 and 0<=y<=340)
        path,vertices=stage.boundary_path(loops,0.5)
        self.assertEqual(vertices,sum(len(x) for x in loops))
        self.assertGreaterEqual(path.count(' Z'),4)

    def test_approximation_always_counts_each_control_vertex(self):
        mask=np.zeros((340,340),dtype=bool)
        mask[10:40,10:70]=True
        loops=stage.pixel_edge_loops(mask)
        p,n=stage.boundary_path(loops,0.5)
        self.assertEqual(n,4)
        self.assertEqual(p.count(' L '),3)
        with self.assertRaises(ValueError):stage.boundary_path(loops,2.25)

    def test_source_contour_hierarchy_and_signatures_fail_closed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):stage.frozen(Path(d))
        with self.assertRaises(ValueError):
            stage.source_ring_mask([{'depth':0,'role':'hole','points':[[3,3]]}])

    def test_vertex_budget_optimizer_never_exceeds_limit(self):
        measured={'face':[{'epsilon':.5,'vertices':13,'binary_pixel_mismatch':0},
                          {'epsilon':1.,'vertices':4,'binary_pixel_mismatch':9}],
                  'other':[{'epsilon':.5,'vertices':12,'binary_pixel_mismatch':0},
                           {'epsilon':1.,'vertices':4,'binary_pixel_mismatch':3}]}
        selected=stage.choose_budgeted(measured,17)
        self.assertLessEqual(selected['mask_vertices'],17)
        self.assertEqual(selected['chosen_epsilons']['face'],.5)
        self.assertEqual(selected['chosen_epsilons']['other'],1.)
        with self.assertRaises(ValueError):stage.choose_budgeted(measured,7)

    def test_forbid_source_image_embedding_in_svg(self):
        source=ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg"><defs>'
          '<mask id="m" width="340" height="340"/></defs></svg>')
        stage.replace_svg_mask(source,'m','M 0 0 L 10 0 L 10 10 Z')
        self.assertNotIn('<image',ET.tostring(source,encoding='unicode'))
        with self.assertRaises(ValueError):stage.replace_svg_mask(source,'absent','M0 0')

    def test_canvas_and_primitive_accounting_hard_and_stable(self):
        self.assertEqual(stage.BUDGET,1412)
        self.assertEqual(stage.EXTRAS,12)
        self.assertEqual(len(stage.ORDER),11)
        self.assertEqual(stage.SIZE,(340,340))
        # The five exact critical masks already consume 1410 vertices, with
        # 12 stage9 vertices making the 1412 limit fail even if all other
        # owner masks were deleted. This is not a universal impossibility.
        self.assertGreater(636+138+198+300+138+stage.EXTRAS,stage.BUDGET)


if __name__=='__main__':unittest.main()
