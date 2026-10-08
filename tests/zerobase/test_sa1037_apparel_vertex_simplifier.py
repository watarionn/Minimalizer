import unittest

import cv2
import numpy as np

from minimalizer_zerobase.reviewed_sa10.apparel_vertex_simplifier import (
    _simple_polygon, optimize_apparel_polygon_vertices,
)
from minimalizer_zerobase.reviewed_sa10.semantic_apparel_material_planes import (
    propose_source_uniform_panels, render_source_uniform_panels,
)


def fixture():
    source = np.full((120,120,3), [238,238,238], np.uint8)
    parent = np.zeros((120,120),bool)
    parent[20:110,5:95] = True
    source[parent] = [25,32,65]
    source[26:73,22:43] = [237,240,243]
    source[26:73,60:83] = [237,240,243]
    source[20:110,46:57] = [111,210,18]
    protected = np.zeros_like(parent)
    protected[103:109,7:15] = True
    original = propose_source_uniform_panels(
        source_rgb=source, parent_visible=parent,
        protected=protected, parent_primitive_id="existing-lowerbody",
    )
    if original is None:
        raise RuntimeError("synthetic source lacks necessary five apparel panels")
    baseline = np.full_like(source,[104,91,86])
    return source, parent, protected, original[0], baseline


class ApparelVertexSimplifierTests(unittest.TestCase):
    def test_source_color_and_protected_regions_stay_fixed(self):
        source,parent,protected,panels,baseline=fixture()
        before,_=render_source_uniform_panels(
            base_rgb=baseline,panels=panels,parent_visible=parent,protected=protected,
        )
        updated,rgb,evidence=optimize_apparel_polygon_vertices(
            original_panels=panels,source_rgb=source,baseline_rgb=baseline,
            owner_visible=parent,protected=protected,
        )
        self.assertEqual(len(updated),5)
        self.assertTrue(evidence["all_filled_polygons_simple"])
        self.assertLessEqual(evidence["candidate_total_vertices"],evidence["original_total_vertices"])
        self.assertEqual([p["material"] for p in panels],[p["material"] for p in updated])
        self.assertEqual([p["color_rgb_observed"] for p in panels],[p["color_rgb_observed"] for p in updated])
        self.assertTrue(np.array_equal(before[~parent],rgb[~parent]))
        self.assertTrue(np.array_equal(before[protected],rgb[protected]))
        self.assertTrue(evidence["source_color_nonregression_gate"])
        self.assertFalse(evidence["production_promotion_authorized"])
        self.assertTrue(all(_simple_polygon(p["points"]) for p in updated))

    def test_crossing_ring_is_detected_and_fixable_with_one_contour_point(self):
        right_dark=[
            [238.,250.],[222.,245.],[227.,266.],[212.,245.],
            [207.,276.],[180.,304.],[190.,339.],[220.,334.],
            [235.,289.],[207.,266.],[238.,276.],
        ]
        self.assertFalse(_simple_polygon(right_dark))
        self.assertTrue(_simple_polygon([p for i,p in enumerate(right_dark) if i!=9]))

    def test_no_bow_ties_or_collinear_self_touching_outlines(self):
        self.assertFalse(_simple_polygon([[0,0],[8,8],[0,8],[8,0]]))
        self.assertFalse(_simple_polygon([[0,0],[8,0],[8,8],[5,0],[0,8]]))
        self.assertTrue(_simple_polygon([[0,0],[8,0],[8,8],[0,8]]))

    def test_repeated_result_is_deterministic(self):
        source,parent,protected,panels,baseline=fixture()
        one=optimize_apparel_polygon_vertices(
            original_panels=panels,source_rgb=source,baseline_rgb=baseline,
            owner_visible=parent,protected=protected,
        )
        two=optimize_apparel_polygon_vertices(
            original_panels=panels,source_rgb=source,baseline_rgb=baseline,
            owner_visible=parent,protected=protected,
        )
        self.assertEqual(one[0],two[0])
        self.assertEqual(one[2],two[2])
        self.assertTrue(np.array_equal(one[1],two[1]))

    def test_invalid_geometry_limits_are_fail_closed(self):
        source,parent,protected,panels,baseline=fixture()
        for keyword,value in (
            ("allowed_lab_mse_increase",0.2),
            ("minimum_class_overlap_ratio",0.1),
            ("maximum_change_fraction",0.5),
            ("minimum_saved_vertices",0),
        ):
            with self.subTest(keyword=keyword),self.assertRaises(ValueError):
                optimize_apparel_polygon_vertices(
                    original_panels=panels,source_rgb=source,baseline_rgb=baseline,
                    owner_visible=parent,protected=protected,**{keyword:value},
                )

    def test_source_material_palette_must_still_be_observed(self):
        source,parent,protected,panels,baseline=fixture()
        fake=[dict(p) for p in panels]
        fake[0]["color_rgb_observed"]=[1,2,3]
        with self.assertRaises(ValueError):
            optimize_apparel_polygon_vertices(
                original_panels=fake,source_rgb=source,baseline_rgb=baseline,
                owner_visible=parent,protected=protected,
            )

    def test_face_arm_protected_mask_shape_is_required(self):
        source,parent,protected,panels,baseline=fixture()
        with self.assertRaises(ValueError):
            optimize_apparel_polygon_vertices(
                original_panels=panels,source_rgb=source,baseline_rgb=baseline,
                owner_visible=parent,protected=np.zeros((40,40),bool),
            )


if __name__=="__main__":
    unittest.main()
