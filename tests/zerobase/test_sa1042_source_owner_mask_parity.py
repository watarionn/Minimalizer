"""SA10.42: deterministic source-owned mask and research release gates."""
from pathlib import Path
import sys
import unittest
import cv2
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'/'research'))
import sa1042_source_owner_mask_parity as stage


class SourceOwnerMaskParityTests(unittest.TestCase):
    def test_pixel_run_rectangles_preserve_holes_islands_and_exact_pixels(self):
        pixels=np.zeros((20,22),bool)
        pixels[2:15,2:12]=True
        pixels[7:11,5:9]=False
        pixels[0,0]=True
        pixels[16:19,18:21]=True
        rects=stage.merged_pixel_rectangles(pixels)
        reconstructed=np.zeros_like(pixels)
        for x,y,w,h in rects:reconstructed[y:y+h,x:x+w]=True
        self.assertTrue(np.array_equal(reconstructed,pixels))
        self.assertLess(len(rects),int(pixels.sum()))

    def test_original_cv2_hole_and_one_pixel_island_replayed(self):
        rings=[
            {'depth':0,'role':'fill','points':[[1,1],[17,1],[17,17],[1,17]]},
            {'depth':1,'role':'hole','points':[[5,5],[13,5],[13,13],[5,13]]},
            {'depth':0,'role':'fill','points':[[20,20]]}
        ]
        expected=np.zeros((25,25),np.uint8)
        contours=[np.asarray(r['points'],np.int32).reshape(-1,1,2) for r in rings]
        cv2.drawContours(expected,contours,-1,255,thickness=cv2.FILLED,lineType=cv2.LINE_8)
        mask=stage.source_ring_mask(rings,(25,25))
        self.assertTrue(np.array_equal(mask,expected>0))
        self.assertTrue(mask[20,20])
        with self.assertRaises(ValueError):
            stage.source_ring_mask([{**rings[0],'role':'hole'}],(25,25))

    def test_svg_mask_representation_counts_every_rectangle(self):
        import xml.etree.ElementTree as ET
        root=ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg"><defs>'
            '<mask id="signed" width="12" height="12"><rect width="12" height="12"/></mask>'
            '</defs></svg>')
        mask=np.zeros((12,12),bool)
        mask[3:9,2:10]=True
        count=stage.replace_signed_mask(root,'signed',mask,inverse=True)
        self.assertEqual(count,1)
        markup=ET.tostring(root,encoding='unicode')
        self.assertIn('#000000',markup)
        self.assertIn('#ffffff',markup)
        self.assertNotIn('<image',markup)
        with self.assertRaises(ValueError):
            stage.replace_signed_mask(root,'not-signed',mask)

    def test_bad_original_provenance_fail_closed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                stage.verify_inputs(Path(folder))

    def test_original_owned_rgb_metric_does_not_hide_global_issues(self):
        a=np.zeros((5,5,3),np.uint8)
        b=a.copy();b[0,0]=200
        mask=np.zeros((5,5),bool);mask[2:5,2:5]=True
        result=stage.rgb_mismatches(a,b,{'face':mask})
        self.assertEqual(result['full_scene'],1)
        self.assertEqual(result['protected_parts']['face'],0)

    def test_no_production_gate_and_vertex_budget_never_waived(self):
        source=Path(stage.__file__).read_text(encoding='utf-8')
        for statement in (
            "'production_changed':False", "'full_character_golden_pass':False",
            "'requires_budget_preserving_contour_compaction':True",
            "'original_vertex_budget':1412", "'generative_fill_used':False",
        ):
            self.assertIn(statement,source)


if __name__=='__main__':
    unittest.main()
