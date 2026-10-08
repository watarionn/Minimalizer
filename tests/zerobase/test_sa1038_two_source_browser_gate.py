import unittest

from tools.run_sa1038_two_source_browser_gate import evaluate_research


def gc001():
    return {
        "schema":"sa10.38-source-contour-vector-mask-browser-v1",
        "source_sha256":"a"*64,
        "chrome_execution_provenance_verified":True,
        "browser_screenshot_verified":True,
        "degenerate_source_rings_proven_raster_neutral":True,
        "degenerate_removal_changed_owner_pixels":0,
        "source_bitmap_or_base64_raster_embedded":False,
        "svg_mask_hole_boundary_stroke_paths":5,
        "added_hole_boundary_svg_stroke_paint_passes_are_counted":True,
        "svg_apparel_filled_subpath_count":5,
        "svg_apparel_polygon_vertices":27,
        "signed_original_primitive_count":11,
        "isolated_material_layer_only_not_full_scene":True,
        "exact_browser_opencv_pixel_parity":False,
        "browser_svg_gate":"FAIL",
        "browser_mismatched_rgb_pixels":69,
        "browser_mismatched_rgb_pixels_strong_gt48":51,
        "production_promotion_authorized":False,
    }


def raden():
    return {
        "schema":"sa10.37-topology-locked-apparel-geometry-v1",
        "case_source_sha256":"b"*64,
        "status":"NONMATCHING_CASE_NO_OP",
        "Stage04_source_masks_verified":True,
        "Stage08_outer_sha_verified":True,
        "Stage36_material_provenance_verified":True,
        "Stage36_original_RGB_pixel_replay_equal":True,
        "face_left_right_arm_rgb_unchanged":True,
        "existing_outer_primitive_count":11,
        "apparel_subpaths_before":0,
        "apparel_subpaths_after":0,
        "candidate_preview_sha256":"c"*64,
        "baseline_source36_preview_sha256":"c"*64,
        "production_promotion_authorized":False,
    }


class RealBrowserGateTests(unittest.TestCase):
    def test_research_improvement_pass_does_not_authorize_release(self):
        result=evaluate_research(gc001=gc001(),raden=raden())
        self.assertEqual(result["research_gate"],"PASS")
        self.assertEqual(result["current_attested_chrome_differing_pixels"],69)
        self.assertGreater(result["browser_mismatch_reduction_ratio"],.86)
        self.assertEqual(result["isolated_apparel_svg_exact_pixel_parity"],"FAIL")
        self.assertFalse(result["production_promotion_authorized"])

    def test_fake_browser_screenshot_or_raster_embed_rejected(self):
        for prop,value in (
            ("chrome_execution_provenance_verified",False),
            ("source_bitmap_or_base64_raster_embedded",True),
            ("added_hole_boundary_svg_stroke_paint_passes_are_counted",False),
            ("degenerate_removal_changed_owner_pixels",1),
        ):
            fake=gc001()
            fake[prop]=value
            with self.subTest(prop=prop):
                self.assertEqual(
                    evaluate_research(gc001=fake,raden=raden())["research_gate"],
                    "FAIL",
                )

    def test_uncorrected_svg_pixels_cannot_pass_research_gate(self):
        fake=gc001()
        fake["browser_mismatched_rgb_pixels"]=300
        result=evaluate_research(gc001=fake,raden=raden())
        self.assertEqual(result["research_gate"],"FAIL")

    def test_control_image_must_reproduce_exactly(self):
        fake=raden()
        fake["candidate_preview_sha256"]="d"*64
        self.assertEqual(
            evaluate_research(gc001=gc001(),raden=fake)["research_gate"],
            "FAIL",
        )

    def test_duplicate_source_or_missing_pixel_measurement_rejected(self):
        bad=raden()
        bad["case_source_sha256"]="a"*64
        with self.assertRaises(ValueError):
            evaluate_research(gc001=gc001(),raden=bad)
        bad=gc001()
        bad["browser_mismatched_rgb_pixels"]=None
        with self.assertRaises(ValueError):
            evaluate_research(gc001=bad,raden=raden())


if __name__=="__main__":
    unittest.main()
