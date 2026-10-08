import copy
import unittest

import numpy as np

from minimalizer_zerobase.reviewed_sa10.browser_material_edge_calibration import (
    apply_raster_neutral_vertex_nudge,
)


def setup_panels():
    names=["dark_uniform","dark_uniform","white_shirt","white_shirt","green_necktie"]
    cols=[[30,38,71],[29,36,73],[247,249,253],[251,252,253],[148,211,26]]
    panels=[]
    for i,(name,color) in enumerate(zip(names,cols)):
        x=8+i*8
        panels.append({
            "schema":"sa10.36-uniform-material-panel-v1",
            "material":name,"owner":"lower_body",
            "parent_primitive_id":"source-unchanged-lowerbody",
            "points":[[float(x),8.],[float(x+6),8.],[float(x+6),18.],[float(x),18.]],
            "color_rgb_observed":color,
        })
    polygons="".join(
        '<polygon points="'+
        " ".join(
            f'{x+0.5:g},{y+0.5:g}' for x,y in panel["points"]
        )+'" fill="#'+''.join(f'{c:02x}' for c in panel["color_rgb_observed"])+
        '" stroke="#'+''.join(f'{c:02x}' for c in panel["color_rgb_observed"])+
        '" stroke-width="1" stroke-linejoin="miter"/>'
        for panel in panels
    )
    svg=(
        '<svg width="64" height="64"><defs>'
        '<mask id="signed"><path d="M 0 0 L 60 0 L 60 60 Z"/></mask>'
        '</defs><g mask="url(#signed)">'+polygons+'</g></svg>'
    )
    return svg,panels,np.ones((64,64),bool)


class SourceRasterNeutralVertexTests(unittest.TestCase):
    def test_real_raster_neutral_half_pixel_offset_preserves_signed_material_pixels(self):
        svg,panels,mask=setup_panels()
        candidate,record=apply_raster_neutral_vertex_nudge(
            svg,original_material_panels=panels,
            material_index=1,vertex_index=1,axis=1,
            delta=.5,source_owner_mask=mask,
        )
        self.assertNotEqual(svg,candidate)
        self.assertIn('22.5,9',candidate)
        self.assertEqual(record["unclipped_canonical_cv2_material_mask_changed_pixels"],0)
        self.assertTrue(record["green_tie_polygon_unchanged"])
        self.assertTrue(record["source_stage37_material_geometry_modified"] is False)
        self.assertEqual(record["new_polygon_vertices"],0)
        self.assertEqual(record["original_material_vertex_count"],20)
        self.assertFalse(record["production_promotion_authorized"])
        self.assertEqual(candidate.split('<polygon ')[-1],svg.split('<polygon ')[-1])

    def test_unsafe_odd_pixel_rounding_rejected_even_when_limited_to_half_pixel(self):
        svg,panels,mask=setup_panels()
        # Existing signed source y=9 (odd) → +0.5 rounds to 10,
        # whereas source raster y=9 stays 9. Must not hide this difference.
        panels[1]["points"][1][1]=9.
        # Update SVG source vertex at the same stage37+0.5 coordinate.
        svg=svg.replace('22.5,8.5','22.5,9.5',1)
        with self.assertRaises(ValueError):
            apply_raster_neutral_vertex_nudge(
                svg,original_material_panels=panels,
                material_index=1,vertex_index=1,axis=1,
                delta=.5,source_owner_mask=mask,
            )

    def test_source_canvas_owner_palette_and_tie_are_signed(self):
        svg,panels,mask=setup_panels()
        for entry in (
            dict(material_index=4,vertex_index=1,axis=1,delta=.5),
            dict(material_index=1,vertex_index=200,axis=1,delta=.5),
            dict(material_index=1,vertex_index=1,axis=2,delta=.5),
            dict(material_index=1,vertex_index=1,axis=1,delta=2.),
            dict(material_index=-1,vertex_index=1,axis=1,delta=.5),
        ):
            with self.subTest(entry=entry),self.assertRaises(ValueError):
                apply_raster_neutral_vertex_nudge(
                    svg,original_material_panels=panels,
                    source_owner_mask=mask,**entry,
                )

    def test_svg_tampering_or_canvas_shape_mismatch_is_rejected(self):
        svg,panels,mask=setup_panels()
        with self.assertRaises(ValueError):
            apply_raster_neutral_vertex_nudge(
                svg.replace('22.5,8.5','24.5,8.5'),
                original_material_panels=panels,material_index=1,
                vertex_index=1,axis=1,delta=.5,source_owner_mask=mask,
            )
        with self.assertRaises(ValueError):
            apply_raster_neutral_vertex_nudge(
                svg,original_material_panels=panels,material_index=1,
                vertex_index=1,axis=1,delta=.5,
                source_owner_mask=np.zeros((64,64),bool),
            )

    def test_research_output_deterministic_source_untouched(self):
        svg,panels,mask=setup_panels()
        before=copy.deepcopy(panels)
        first=apply_raster_neutral_vertex_nudge(
            svg,original_material_panels=panels,material_index=1,
            vertex_index=1,axis=1,delta=.5,source_owner_mask=mask,
        )
        second=apply_raster_neutral_vertex_nudge(
            svg,original_material_panels=panels,material_index=1,
            vertex_index=1,axis=1,delta=.5,source_owner_mask=mask,
        )
        self.assertEqual(first,second)
        self.assertEqual(before,panels)


if __name__=="__main__":
    unittest.main()
