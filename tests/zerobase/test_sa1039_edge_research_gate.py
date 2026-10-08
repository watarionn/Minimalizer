import unittest

from tools.run_sa1039_edge_research_gate import decide


def evidence():
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
        "browser_mismatched_rgb_pixels":45,
        "svg_parent_outline_stroke_paint_passes":0,
        "svg_parent_outline_stroke_px":0.0,
        "svg_signed_top_edge_stroke_px":1.25,
        "svg_signed_top_edge_top_row_exact_replay_verified":True,
        "svg_signed_top_edge_count":2,
        "svg_signed_top_edge_reused_endpoint_occurrences":4,
        "svg_signed_top_edge_paint_passes_are_counted":True,
        "svg_signed_top_edge_source_segments":[[91.,230.,245.],[233.,238.,245.]],
        "degenerate_source_rings_proven_raster_neutral":True,
        "degenerate_removal_changed_owner_pixels":0,
        "added_hole_boundary_svg_stroke_paint_passes_are_counted":True,
    }
    prior_audit={
        "schema":"sa10.39-signed-svg-residual-pixel-audit-v1",
        "source_sha256":"a"*64,
        "signed_outer_vector_sha256":"b"*64,
        "signed_material_scene_sha256":"c"*64,
        "chrome_executed_and_sha_attested":True,
        "chrome_different_rgb_pixels":69,
        "pixel_disagreement_outside_signed_owner":3,
        "different_color_on_jointly_painted_pixels":6,
    }
    current_audit={
        **prior_audit,
        "chrome_different_rgb_pixels":45,
        "actual_source_owner_boundary_immutable":True,
        "actual_five_material_subpaths_immutable":True,
        "new_svg_geometry_created":False,
        "production_promotion_authorized":False,
        "source_owner_parent_boundary":{
            "owner_and_material_edge":14,
            "owner_edge_only":0,
            "material_edge_only":31,
            "outside_near_edge":0,
        },
        "occupancy_differences":39,
        "mismatch_y_row_245":0,
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
    return prior,prior_audit,current,current_audit,raden


class Sa1039ResearchGateTests(unittest.TestCase):
    def test_real_chrome_reduction_is_research_only(self):
        p,pa,c,a,r=evidence()
        result=decide(prior=p,prior_audit=pa,current=c,audit=a,raden=r)
        self.assertEqual(result["research_gate"],"PASS")
        self.assertEqual(result["full_browser_exact_pixel_parity"],"FAIL")
        self.assertEqual(result["current_browser_pixel_mismatch_count"],45)
        self.assertEqual(result["current_off_owner_mismatched_pixels"],3)
        self.assertEqual(result["existing_signed_top_edge_stroke_passes_counted"],2)
        self.assertFalse(result["production_promotion_authorized"])

    def test_56px_broad_stroke_overpaint_is_rejected(self):
        p,pa,c,a,r=evidence()
        bad={**c,"browser_mismatched_rgb_pixels":56,
             "svg_parent_outline_stroke_paint_passes":1,
             "svg_parent_outline_stroke_px":1.15,
             "svg_signed_top_edge_count":0,
             "svg_signed_top_edge_stroke_px":0}
        outside={**a,"chrome_different_rgb_pixels":56,
                 "pixel_disagreement_outside_signed_owner":22,
                 "occupancy_differences":50,
                 "source_owner_parent_boundary":{
                     "owner_and_material_edge":25,"owner_edge_only":0,
                     "material_edge_only":31,"outside_near_edge":0,
                 }}
        result=decide(prior=p,prior_audit=pa,current=bad,audit=outside,raden=r)
        self.assertEqual(result["research_gate"],"FAIL")
        self.assertFalse(result["source_silhouette_ownership_not_worsened"])
        self.assertFalse(result["production_promotion_authorized"])

    def test_extra_top_strokes_must_be_reused_counted_and_proven(self):
        p,pa,c,a,r=evidence()
        for field,value in (
            ("svg_signed_top_edge_count",0),
            ("svg_signed_top_edge_reused_endpoint_occurrences",0),
            ("svg_signed_top_edge_top_row_exact_replay_verified",False),
            ("svg_signed_top_edge_paint_passes_are_counted",False),
        ):
            bad={**c,field:value}
            with self.subTest(field=field):
                self.assertEqual(
                    decide(prior=p,prior_audit=pa,current=bad,audit=a,raden=r)["research_gate"],
                    "FAIL",
                )

    def test_control_and_source_identity_must_remain_unchanged(self):
        p,pa,c,a,r=evidence()
        altered={**r,"candidate_preview_sha256":"f"*64}
        self.assertEqual(
            decide(prior=p,prior_audit=pa,current=c,audit=a,raden=altered)["research_gate"],
            "FAIL",
        )
        bad={**c,"outer_vector_sha256":"z"*64}
        self.assertEqual(
            decide(prior=p,prior_audit=pa,current=bad,audit=a,raden=r)["research_gate"],
            "FAIL",
        )
        duplicate={**r,"case_source_sha256":"a"*64}
        with self.assertRaises(ValueError):
            decide(prior=p,prior_audit=pa,current=c,audit=a,raden=duplicate)

    def test_actual_chrome_audit_must_be_consistent_and_attested(self):
        p,pa,c,a,r=evidence()
        mismatched={**a,"occupancy_differences":40}
        self.assertEqual(
            decide(prior=p,prior_audit=pa,current=c,audit=mismatched,raden=r)["research_gate"],
            "FAIL",
        )
        unverified={**c,"chrome_execution_provenance_verified":False}
        with self.assertRaises(ValueError):
            decide(prior=p,prior_audit=pa,current=unverified,audit=a,raden=r)

    def test_slight_pixel_improvement_is_not_enough(self):
        p,pa,c,a,r=evidence()
        weak={**c,"browser_mismatched_rgb_pixels":68}
        diagnostic={**a,"chrome_different_rgb_pixels":68,
                    "occupancy_differences":62,
                    "source_owner_parent_boundary":{
                        "owner_and_material_edge":37,
                        "owner_edge_only":0,
                        "material_edge_only":31,
                        "outside_near_edge":0,
                    }}
        self.assertEqual(
            decide(prior=p,prior_audit=pa,current=weak,audit=diagnostic,raden=r)["research_gate"],
            "FAIL",
        )


if __name__=="__main__":
    unittest.main()
