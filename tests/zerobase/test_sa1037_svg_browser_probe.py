import json
import tempfile
import unittest
from pathlib import Path

from tools.run_sa1037_browser_svg_probe import _points, _owner_ring_path, prepare_svg


def scene():
    p={
        "primitive_id":"source-bound-lowerbody",
        "source_mask_owner":"lower_body",
        "primitive_type":"polygon",
        "parameters":{
            "components":[[[1,1],[30,1],[30,30],[1,30]]],
            "rings":[
                {"depth":0,"role":"fill","points":[[1,1],[30,1],[30,30],[1,30]]},
                {"depth":1,"role":"hole","points":[[20,20]]},
            ],
            "hole_preservation":"contour-tree-even-odd",
        },
    }
    return {
        "coordinate_space":{"pixel_width":64,"pixel_height":64},
        "primitives_back_to_front":[p],
    }


def research_planes():
    return {
        "apparel_material_polygons":[
            {"parent_primitive_id":"source-bound-lowerbody",
             "points":[[2,2],[9,2],[9,9],[2,9]],
             "color_rgb_observed":c}
            for c in ([30,40,70],[31,40,70],[240,245,249],[242,244,249],[130,210,25])
        ],
    }


class SvgResearchProbeTests(unittest.TestCase):
    def test_svg_is_actual_vector_no_png_or_image_element(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            s=root/"scene.json"
            p=root/"panels.json"
            s.write_text(json.dumps(scene()),encoding="utf-8")
            p.write_text(json.dumps(research_planes()),encoding="utf-8")
            metrics=prepare_svg(scene_path=s,panels_path=p,output_dir=root/"output")
            svg=(root/"output"/"apparel_svg_browser_probe.svg").read_text("utf-8")
            self.assertIn("<clipPath",svg)
            self.assertIn('clip-rule="evenodd"',svg)
            self.assertIn("<polygon",svg)
            self.assertEqual(svg.count("<polygon"),5)
            self.assertNotIn("<image",svg)
            self.assertNotIn("base64",svg)
            self.assertEqual(metrics["unrepresentable_one_or_two_point_parent_rings"],1)
            self.assertFalse(metrics["svg_exact_parity_pass"])
            self.assertFalse(metrics["production_promotion_authorized"])

    def test_positive_half_pixel_shift_is_applied_to_both_clip_and_content(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            s=root/"scene.json"
            p=root/"panels.json"
            s.write_text(json.dumps(scene()),encoding="utf-8")
            p.write_text(json.dumps(research_planes()),encoding="utf-8")
            m=prepare_svg(scene_path=s,panels_path=p,output_dir=root/"output",
                          pixel_shift=.5,shape_rendering="crispEdges")
            svg=(root/"output"/"apparel_svg_browser_probe.svg").read_text("utf-8")
            self.assertIn("M 1.5 1.5",svg)
            self.assertIn("2.5,2.5",svg)
            self.assertEqual(m["svg_pixel_shift"],.5)

    def test_invalid_css_mode_or_coordinate_shift_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            s=root/"scene.json"
            p=root/"panels.json"
            s.write_text(json.dumps(scene()),encoding="utf-8")
            p.write_text(json.dumps(research_planes()),encoding="utf-8")
            for shift,shape in ((-3.,"crispEdges"),(.75,"crispEdges"),(0,"invented")):
                with self.subTest(shift=shift,shape=shape),self.assertRaises(ValueError):
                    prepare_svg(scene_path=s,panels_path=p,output_dir=root/"output",
                                pixel_shift=shift,shape_rendering=shape)

    def test_source_geometry_is_never_relabelled_from_another_owner(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            s=root/"scene.json"
            p=root/"panels.json"
            wrong=research_planes()
            wrong["apparel_material_polygons"][0]["parent_primitive_id"]="face"
            s.write_text(json.dumps(scene()),encoding="utf-8")
            p.write_text(json.dumps(wrong),encoding="utf-8")
            with self.assertRaises(ValueError):
                prepare_svg(scene_path=s,panels_path=p,output_dir=root/"output")


if __name__=="__main__":
    unittest.main()
