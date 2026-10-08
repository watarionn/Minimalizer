import copy
import unittest

from tools.run_sa1041_full_scene_crosscase_gate import decide


def full_scene(*,raden=False):
    source="b"*64 if raden else "a"*64
    return {
        "schema":"sa10.41-source-signed-full-character-browser-research-v1",
        "original_source_sha256":source,
        "saved_stage9_candidate_pixel_equal":True,
        "saved_stage37_full_preview_pixel_equal":True,
        "source_stage8_owner_order_unchanged":True,
        "source_immutable_face_and_both_arms":True,
        "source_apparel_pixels_changed_outside_visible_lower_body":0,
        "source_raster_pixels_embedded":False,
        "original_face_feature_geometry_added":False,
        "all_generated_elements_geometric_svg":True,
        "svg_protected_mask_geometry_counted":True,
        "svg_flat_face_guard_original_stage04_mask_counted":True,
        "all_original_vertex_and_mask_complexity_counted":True,
        "production_promotion_authorized":False,
        "full_scene_chrome_executed":True,
        "real_chrome_full_character_execute_verified":True,
        "original_source_primitive_records":11,
        "source_owner_rendered_count":10,
        "full_scene_chrome_exact_rgb_parity":"FAIL",
        "original_source_ring_vertex_budget_pass":False,
        "combined_source_geometry_budget_pass":False,
        "screenshot_sha256":"c"*64,
        "chrome_executable_sha256":"d"*64,
        "svg_sha256":"e"*64,
        "html_sha256":"f"*64,
        "original_stage37_preview_sha256":"1"*64,
        "true_full_scene_browser_exact_RGB_parity":"FAIL",
        "full_character_face_and_arm_browser_parity":"FAIL",
        "full_scene_RGB_mismatched_pixels":2681 if raden else 3919,
        "full_scene_protected_semantic_parts":{
            "face":{"chrome_different_rgb_pixels_in_source_mask":122 if raden else 140},
            "left_arm":{"chrome_different_rgb_pixels_in_source_mask":237 if raden else 206},
            "right_arm":{"chrome_different_rgb_pixels_in_source_mask":255 if raden else 199},
        },
        "phase9_interior_filled_subpaths":1 if raden else 3,
        "phase37_apparel_filled_subpaths":0 if raden else 5,
        "phase37_apparel_polygon_vertices":0 if raden else 27,
        "stage37_no_apparel_negative_control":raden,
        "original_source_ring_vertices_including_support":2370 if raden else 3604,
        "original_source_ring_vertex_budget_limit":1412 if raden else 1887,
        "combined_mask_vector_source_vertex_occurrences_counted":2976 if raden else 4312,
        "source_topological_degenerate_ring_count":13 if raden else 110,
    }


class FullCharacterCrosscaseGateTests(unittest.TestCase):
    def test_real_full_character_study_pass_is_not_product_release(self):
        record=decide(gc001=full_scene(),raden=full_scene(raden=True))
        self.assertEqual(record["research_evidence_gate"],"PASS")
        self.assertEqual(record["GC001"]["full_scene_RGB_differing_pixels"],3919)
        self.assertEqual(record["Raden"]["full_scene_RGB_differing_pixels"],2681)
        self.assertEqual(record["full_character_browser_exact_RGB_parity_gate"],"FAIL")
        self.assertEqual(record["source_protected_face_left_right_arm_browser_gate"],"FAIL")
        self.assertEqual(record["original_and_combined_vertex_budget_gate"],"FAIL")
        self.assertFalse(record["production_promotion_authorized"])

    def test_no_embedding_invented_facial_parts_or_silhouette_recolor(self):
        for field,value in (
            ("source_raster_pixels_embedded",True),
            ("original_face_feature_geometry_added",True),
            ("source_immutable_face_and_both_arms",False),
            ("source_apparel_pixels_changed_outside_visible_lower_body",1),
            ("saved_stage37_full_preview_pixel_equal",False),
        ):
            bad=full_scene()
            bad[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                decide(gc001=bad,raden=full_scene(raden=True))

    def test_fake_browser_perfect_pass_or_protected_arm_errors_cannot_hide(self):
        for field,value in (
            ("real_chrome_full_character_execute_verified",False),
            ("full_scene_chrome_exact_rgb_parity","PASS"),
            ("full_character_face_and_arm_browser_parity","PASS"),
            ("full_scene_RGB_mismatched_pixels",0),
        ):
            bad=full_scene()
            bad[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                decide(gc001=bad,raden=full_scene(raden=True))

    def test_nonmatching_character_is_noop_and_sha_distinct(self):
        unrelated=full_scene(raden=True)
        unrelated["original_source_sha256"]="a"*64
        with self.assertRaises(ValueError):
            decide(gc001=full_scene(),raden=unrelated)
        unrelated=full_scene(raden=True)
        unrelated["phase37_apparel_filled_subpaths"]=5
        with self.assertRaises(ValueError):
            decide(gc001=full_scene(),raden=unrelated)

    def test_unaccounted_source_or_protected_svg_geometry_rejected(self):
        bad=full_scene()
        bad["combined_mask_vector_source_vertex_occurrences_counted"]=1000
        with self.assertRaises(ValueError):
            decide(gc001=bad,raden=full_scene(raden=True))
        bad=full_scene()
        bad["svg_flat_face_guard_original_stage04_mask_counted"]=False
        with self.assertRaises(ValueError):
            decide(gc001=bad,raden=full_scene(raden=True))


if __name__=="__main__":
    unittest.main()
