import unittest

from tools.run_sa1039_edge_research_gate import decide


def inputs():
    prior={
        "schema":"sa10.38-source-contour-vector-mask-browser-v1",
        "source_sha256":"a"*64,
        "outer_vector_sha256":"b"*64,
        "simplified_apparel_sha256":"c"*64,
        "signed_original_primitive_count":11,
        "svg_apparel_filled_subpath_count":5,
        "svg_apparel_polygon_vertices":27,
        "svg_mask_hole_boundary_stroke_paths":5,
        "chrome_execution_provenance_verified":True,
        "browser_screenshot_verified":True,
        "source_bitmap_or_base64_raster_embedded":False,
        "production_promotion_authorized":False,
        "isolated_material_layer_only_not_full_scene":True,
        "browser_mismatched_rgb_pixels":69,
        "browser_svg_gate":"FAIL",
    }
    current={
        **prior,
        "browser_mismatched_rgb_pixels":56,
        "svg_parent_outline_stroke_paint_passes":1,
        "svg_parent_outline_stroke_px":1.15,
        "svg_parent_outline_extra_stroke_counted":True,
        "svg_parent_outline_reused_ring_point_occurrences":152,
        "source_owner_svg_mask_ring_vertices":152,
        "degenerate_source_rings_proven_raster_neutral":True,
        "degenerate_removal_changed_owner_pixels":0,
        "added_hole_boundary_svg_stroke_paint_passes_are_counted":True,
    }
    audit={
        "schema":"sa10.39-signed-svg-residual-pixel-audit-v1",
        "source_sha256":"a"*64,
        "signed_outer_vector_sha256":"b"*64,
        "signed_material_scene_sha256":"c"*64,
        "actual_source_owner_boundary_immutable":True,
        "actual_five_material_subpaths_immutable":True,
        "chrome_executed_and_sha_attested":True,
        "new_svg_geometry_created":False,
        "production_promotion_authorized":False,
        "chrome_different_rgb_pixels":56,
        "source_owner_parent_boundary":{
            "owner_and_material_edge":25,
            "owner_edge_only":0,
            "material_edge_only":31,
            "outside_near_edge":0,
        },
        "occupancy_differences":50,
        "different_color_on_jointly_painted_pixels":6,
        "browser_svg_gate":"FAIL",
    }
    raden={
        "schema":"sa10.37-topology-locked-apparel-geometry-v1",
        "case_source_sha256":"d"*64,
        "status":"NONMATCHING_CASE_NO_OP",
        "Stage04_source_masks_verified":True,
        "Stage08_outer_sha_verified":True,
        "Stage36_material_provenance_verified":True,
        "face_left_right_arm_rgb_unchanged":True,
        "existing_outer_primitive_count":11,
        "apparel_subpaths_before":0,
        "apparel_subpaths_after":0,
        "candidate_preview_sha256":"e"*64,
        "baseline_source36_preview_sha256":"e"*64,
        "production_promotion_authorized":False,
    }
    return prior,current,audit,raden


class Sa1039ResearchGateTests(unittest.TestCase):
    def test_real_chrome_reduction_is_research_only(self):
        p,c,a,r=inputs()
        result=decide(prior=p,current=c,audit=a,raden=r)
        self.assertEqual(result["research_gate"],"PASS")
        self.assertEqual(result["real_chrome_browser_exact_pixel_gate"],"FAIL")
        self.assertEqual(result["signed_chrome_candidate_mismatch_pixels"],56)
        self.assertEqual(result["remaining_occupancy_boundary_errors"],50)
        self.assertEqual(result["additional_source_parent_outline_stroke_paint_passes"],1)
        self.assertFalse(result["production_promotion_authorized"])

    def test_unaccounted_outline_stroke_cannot_pass(self):
        p,c,a,r=inputs()
        for field,value in (
            ("svg_parent_outline_extra_stroke_counted",False),
            ("svg_parent_outline_reused_ring_point_occurrences",0),
            ("svg_parent_outline_stroke_paint_passes",0),
            ("svg_parent_outline_stroke_px",0),
        ):
            altered={**c,field:value}
            with self.subTest(field=field):
                self.assertEqual(decide(prior=p,current=altered,audit=a,raden=r)["research_gate"],"FAIL")

    def test_cross_character_or_source_ownership_drift_rejected(self):
        p,c,a,r=inputs()
        changed={**r,"candidate_preview_sha256":"x"*64}
        self.assertEqual(decide(prior=p,current=c,audit=a,raden=changed)["research_gate"],"FAIL")
        unsafe={**c,"outer_vector_sha256":"f"*64}
        self.assertEqual(decide(prior=p,current=unsafe,audit=a,raden=r)["research_gate"],"FAIL")
        duplicate={**r,"case_source_sha256":"a"*64}
        with self.assertRaises(ValueError):
            decide(prior=p,current=c,audit=a,raden=duplicate)

    def test_fake_browser_coverage_or_unverified_screenshot_rejected(self):
        p,c,a,r=inputs()
        forged={**a,"occupancy_differences":49}
        self.assertEqual(decide(prior=p,current=c,audit=forged,raden=r)["research_gate"],"FAIL")
        no_attest={**c,"chrome_execution_provenance_verified":False}
        with self.assertRaises(ValueError):
            decide(prior=p,current=no_attest,audit=a,raden=r)

    def test_unimproved_svg_rejected(self):
        p,c,a,r=inputs()
        bad={**c,"browser_mismatched_rgb_pixels":68}
        updated_audit={
            **a,
            "chrome_different_rgb_pixels":68,
            "occupancy_differences":62,
            "source_owner_parent_boundary":{
                **a["source_owner_parent_boundary"],
                "material_edge_only":43,
            },
        }
        self.assertEqual(
            decide(prior=p,current=bad,audit=updated_audit,raden=r)["research_gate"],
            "FAIL",
        )


if __name__=="__main__":
    unittest.main()
