import copy
import unittest

from tools.run_sa1040_two_source_material_gate import decide


def fixture():
    gc001={
        "schema":"sa10.40-signed-browser-material-vertex-correction-v1",
        "GC001_original_source_sha256":"a"*64,
        "baseline_attested_Chrome_mismatched_pixels":45,
        "candidate_attested_Chrome_mismatched_pixels":41,
        "strict_improvement_pixels":4,
        "signed_authoritative_source_material_canvas_changed_pixels":0,
        "original_canonical_CV2_raster_sha256":"b"*64,
        "candidate_canonical_CV2_raster_sha256":"b"*64,
        "source_material_vertex_count_unchanged":True,
        "new_geometric_paths_added":0,
        "source_owner_mask_exact_unchanged":True,
        "outside_owner_Chrome_RGB_byte_identical_to_prior":True,
        "outside_owner_Chrome_painted_pixels":3,
        "thin_green_necktie_rendered_pixels_byte_identical":True,
        "source_palette_and_existing_material_owner_unchanged":True,
        "new_face_eyes_nose_mouth_generated":False,
        "independent_signed_material_owner_audit":"PASS",
        "real_browser_source_and_artifact_SHA_attested":True,
        "browser_exact_pixel_parity":"FAIL",
        "production_promotion_authorized":False,
        "material_vertex_adjustment":{
            "material_index":1,"vertex_index":1,"axis":"y","delta_px":.5
        },
    }
    control={
        "schema":"sa10.37-topology-locked-apparel-geometry-v1",
        "case_source_sha256":"c"*64,
        "status":"NONMATCHING_CASE_NO_OP",
        "Stage04_source_masks_verified":True,
        "Stage08_outer_sha_verified":True,
        "Stage36_material_provenance_verified":True,
        "Stage36_original_RGB_pixel_replay_equal":True,
        "face_left_right_arm_rgb_unchanged":True,
        "existing_outer_primitive_count":11,
        "apparel_subpaths_before":0,
        "apparel_subpaths_after":0,
        "baseline_source36_preview_sha256":"d"*64,
        "candidate_preview_sha256":"d"*64,
        "production_promotion_authorized":False,
    }
    audit={
        "schema":"sa10.39-signed-svg-residual-pixel-audit-v1",
        "source_sha256":"a"*64,
        "chrome_different_rgb_pixels":41,
        "chrome_executed_and_sha_attested":True,
        "actual_source_owner_boundary_immutable":True,
        "actual_five_material_subpaths_immutable":True,
        "new_svg_geometry_created":False,
        "different_color_on_jointly_painted_pixels":6,
        "source_owner_parent_boundary":{
            "owner_and_material_edge":14,
            "owner_edge_only":0,
            "material_edge_only":27,
            "outside_near_edge":0,
        },
        "pixel_disagreement_outside_signed_owner":3,
        "browser_svg_gate":"FAIL",
        "production_promotion_authorized":False,
    }
    return gc001,control,audit


class Sa1040SourceControlResearchGateTests(unittest.TestCase):
    def test_exact_signed_chrome_and_distinct_unrelated_character_pass_research_only(self):
        a,b,c=fixture()
        result=decide(gc001=a,raden=b,audit=c)
        self.assertEqual(result["research_gate"],"PASS")
        self.assertEqual(result["before_chrome_mismatched_pixels"],45)
        self.assertEqual(result["after_chrome_mismatched_pixels"],41)
        self.assertEqual(result["material_only_edge_mismatches_after"],27)
        self.assertEqual(result["original_source_material_raster_changed_pixels"],0)
        self.assertEqual(result["SVG_browser_exact_pixel_parity"],"FAIL")
        self.assertFalse(result["production_promotion_authorized"])

    def test_guard_rejects_silhouette_and_tie_change(self):
        for key,value in (
            ("outside_owner_Chrome_RGB_byte_identical_to_prior",False),
            ("outside_owner_Chrome_painted_pixels",4),
            ("thin_green_necktie_rendered_pixels_byte_identical",False),
            ("signed_authoritative_source_material_canvas_changed_pixels",1),
            ("new_geometric_paths_added",1),
        ):
            a,b,c=fixture()
            a[key]=value
            with self.subTest(key=key):
                self.assertEqual(decide(gc001=a,raden=b,audit=c)["research_gate"],"FAIL")

    def test_source_raster_sha_and_real_Chrome_attestation_must_agree(self):
        for key,value in (
            ("candidate_canonical_CV2_raster_sha256","f"*64),
            ("real_browser_source_and_artifact_SHA_attested",False),
            ("source_material_vertex_count_unchanged",False),
            ("candidate_attested_Chrome_mismatched_pixels",44),
            ("material_vertex_adjustment",{"material_index":4,"vertex_index":1,"axis":"y","delta_px":.5}),
        ):
            a,b,c=fixture()
            a[key]=value
            with self.subTest(key=key):
                self.assertEqual(decide(gc001=a,raden=b,audit=c)["research_gate"],"FAIL")

    def test_two_distinct_images_and_frozen_nonmatching_control_required(self):
        a,b,c=fixture()
        b["case_source_sha256"]="a"*64
        with self.assertRaises(ValueError):
            decide(gc001=a,raden=b,audit=c)
        a,b,c=fixture()
        b["candidate_preview_sha256"]="f"*64
        self.assertEqual(decide(gc001=a,raden=b,audit=c)["research_gate"],"FAIL")

    def test_unauthenticated_or_inaccurate_residual_report_rejected(self):
        a,b,c=fixture()
        c["source_owner_parent_boundary"]["material_edge_only"]=32
        self.assertEqual(decide(gc001=a,raden=b,audit=c)["research_gate"],"FAIL")
        a,b,c=fixture()
        c["chrome_different_rgb_pixels"]=42
        self.assertEqual(decide(gc001=a,raden=b,audit=c)["research_gate"],"FAIL")


if __name__=="__main__":
    unittest.main()
