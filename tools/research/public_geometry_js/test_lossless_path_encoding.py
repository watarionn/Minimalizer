import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from xml.etree import ElementTree as ET
from lossless_path_encoding import encode_path, compact

class StrictPathEncoding(unittest.TestCase):
    def test_vertical_horizontal_vertices_preserved(self):
        output,n=encode_path("M0 0 L4 0 L4 5 L0 5 Z")
        self.assertEqual(n,4)
        self.assertEqual(output,"M0 0 H4 V5 H0 Z")
    def test_hole_and_island_rings_preserved(self):
        original="M0 0 L5 0 L5 5 L0 5 ZM1 1 L1 2 L2 2 L2 1 ZM8 8 L9 8 L9 9 L8 9 Z"
        compacted,n=encode_path(original)
        self.assertEqual(n,12)
        self.assertEqual(compacted.count("M"),3)
        self.assertEqual(compacted.count("Z"),3)
    def test_reject_unsafe_or_float_paths(self):
        for src in ("M0 0 Q1 1 3 3 Z", "M0.5 0 L1 0 Z", "M0 0 <image> Z", "M0 0"):
            with self.assertRaises(ValueError):encode_path(src)
    def test_full_scene_must_have_ten_paths_and_40_shapes(self):
        with TemporaryDirectory() as d:
            src=Path(d)/"x.svg";dst=Path(d)/"y.svg"
            src.write_text('<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 L4 0 L4 4 Z"/></svg>')
            with self.assertRaises(ValueError):compact(src,dst)

if __name__=="__main__":unittest.main()
