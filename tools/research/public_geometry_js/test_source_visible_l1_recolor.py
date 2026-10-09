import unittest
import numpy as np
from pathlib import Path
from tempfile import TemporaryDirectory
from source_visible_l1_recolor import medoid_l1, literal_rgb, verify

class SignedVisibleRefitRegression(unittest.TestCase):
    def test_medoid_is_real_observed_color_and_optimal_l1(self):
        pixels=np.array([[[0,0,0],[0,0,0],[250,250,250],[255,255,255]]],np.uint8)
        result=medoid_l1(pixels,np.ones((1,4),bool))
        candidates={tuple(x) for x in pixels[0]}
        self.assertIn(result,candidates)
        measured=sum(abs(int(x[k])-result[k]) for x in pixels[0] for k in range(3))
        self.assertEqual(measured,min(sum(abs(int(x[k])-int(c[k])) for x in pixels[0] for k in range(3)) for c in candidates))
    def test_empty_region_cannot_invent_color(self):
        self.assertIsNone(medoid_l1(np.zeros((2,2,3),np.uint8),np.zeros((2,2),bool)))
    def test_literal_rgb_rejects_out_of_range_and_unsafe(self):
        for s in ("red","rgb(256,2,3)","rgb(-1,3,4)","rgb(1,2)"):
            with self.assertRaises(ValueError):literal_rgb(s)
        self.assertEqual(literal_rgb("rgb(15,90,255)"),(15,90,255))
    def test_checksum_contract_fails_closed(self):
        with TemporaryDirectory() as d:
            f=Path(d)/"source.png";f.write_bytes(b"not the signed source")
            with self.assertRaises(ValueError):verify(f,"a"*64)

if __name__=="__main__":
    unittest.main()
