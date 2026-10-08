import re
import unittest

from minimalizer_zerobase.reviewed_sa10.browser_material_edge_calibration import (
    apply_material_edge_calibration,
)


def signed_svg():
    materials=[
        ("#202a54", "#202a54"),
        ("#202a55", "#202a55"),
        ("#ecf0f5", "#ecf0f5"),
        ("#ecf0f6", "#ecf0f6"),
        ("#85d323", "#85d323"),
    ]
    polygons="".join(
        f'<polygon points="{i},2 {i+3},2 {i+3},5 {i},5" fill="{color}" '
        f'stroke="{stroke}" stroke-width="1" stroke-linejoin="miter"/>'
        for i,(color,stroke) in enumerate(materials)
    )
    return (
        '<svg width="80" height="80">'
        '<defs><mask id="existing-owner"><path d="M 1 1 L 50 1 L 50 70 Z"/></mask></defs>'
        '<g mask="url(#existing-owner)">'+polygons+'</g></svg>'
    )


class BrowserMaterialEdgeCalibrationTests(unittest.TestCase):
    def test_changes_only_non_tie_paint_attributes_and_proves_unchanged_owner(self):
        original=signed_svg()
        updated,report=apply_material_edge_calibration(
            original,[
                {"index":0,"dx":-0.25},
                {"index":2,"stroke_width":1.1,"join":"round"},
            ],
        )
        self.assertIn('transform="translate(-0.25 0)"',updated)
        self.assertIn('stroke-width="1.1" stroke-linejoin="round"',updated)
        self.assertIn('<path d="M 1 1 L 50 1 L 50 70 Z"/>',updated)
        self.assertEqual(updated.count("<polygon "),5)
        self.assertTrue(report["green_necktie_tag_unchanged"])
        self.assertTrue(report["source_polygon_vertex_geometry_unchanged"])
        self.assertTrue(report["source_owner_mask_and_holes_unchanged"])
        self.assertEqual(report["added_svg_geometric_paths"],0)
        self.assertFalse(report["production_promotion_authorized"])
        self.assertEqual(updated.split('<polygon ')[-1],original.split('<polygon ')[-1])

    def test_green_tie_index_or_duplicate_material_calibration_rejected(self):
        for values in (
            [{"index":4,"dx":.25}],
            [{"index":0,"dx":.25},{"index":0,"dy":.25}],
            [{"index":-1,"stroke_width":1.1}],
            [{"index":True,"dx":.25}],
            [{"index":"1","dx":.25}],
        ):
            with self.subTest(values=values),self.assertRaises(ValueError):
                apply_material_edge_calibration(signed_svg(),values)

    def test_unsafe_render_offset_size_palette_and_untrusted_svg_rejected(self):
        for value in (
            {"index":0,"dx":.75},
            {"index":0,"dy":float("nan")},
            {"index":0,"stroke_width":2.5},
            {"index":0,"join":"script"},
            {"index":0,"shape_rendering":"fake"},
            {"index":0,"dx":.25,"new_polygon":"inject"},
            {"index":0},
        ):
            with self.subTest(value=value),self.assertRaises(ValueError):
                apply_material_edge_calibration(signed_svg(),[value])
        with self.assertRaises(ValueError):
            apply_material_edge_calibration(signed_svg().replace("</svg>","<image/> </svg>"),[{"index":0,"dx":.2}])

    def test_order_and_material_sequence_never_change(self):
        raw=signed_svg()
        first,one=apply_material_edge_calibration(raw,[{"index":3,"dy":.25}])
        second,two=apply_material_edge_calibration(raw,[{"index":3,"dy":.25}])
        self.assertEqual(first,second)
        self.assertEqual(one,two)
        values=re.findall(r'fill="(#[0-9a-f]{6})" stroke=',first)
        self.assertEqual(values,["#202a54","#202a55","#ecf0f5","#ecf0f6","#85d323"])


if __name__=="__main__":
    unittest.main()
