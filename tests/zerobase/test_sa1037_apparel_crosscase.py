import unittest
from tools.run_sa1037_crosscase import aggregate_cases


def record(tag="a",*,repair=True):
    base={
        "schema":"sa10.37-topology-locked-apparel-geometry-v1",
        "case_source_sha256":tag*64,
        "Stage04_source_masks_verified":True,
        "Stage08_outer_sha_verified":True,
        "Stage36_material_provenance_verified":True,
        "Stage36_original_RGB_pixel_replay_equal":True,
        "face_left_right_arm_rgb_unchanged":True,
        "pixels_modified_outside_lower_body_owner":0,
        "existing_outer_primitive_count":11,
        "production_promotion_authorized":False,
        "baseline_source36_preview_sha256":"c"*64,
    }
    if repair:
        return {**base,
            "status":"RESEARCH_GEOMETRIC_VERTEX_REDUCTION_HOLD",
            "baseline_self_intersecting_panels":[1],
            "candidate_self_intersecting_panels":[],
            "all_filled_polygons_simple":True,
            "original_total_vertices":36,
            "candidate_total_vertices":27,
            "saved_vertices":9,
            "source_color_nonregression_gate":True,
            "material_precision_gate":True,
            "necktie_source_width_protected":True,
            "original_apparel_color_lab_mse":4606.6,
            "optimized_apparel_color_lab_mse":4533.6,
            "apparel_lab_mse_improvement_from_stage36":0.0158,
            "apparel_subpaths_before":5,
            "apparel_subpaths_after":5,
        }
    return {**base,
        "status":"NONMATCHING_CASE_NO_OP",
        "original_total_vertices":0,
        "candidate_total_vertices":0,
        "saved_vertices":0,
        "apparel_subpaths_before":0,
        "apparel_subpaths_after":0,
        "candidate_preview_sha256":"c"*64,
    }


class CrosscaseApparelVertexTests(unittest.TestCase):
    def test_real_case_repair_and_noop_can_pass_research_not_release(self):
        result=aggregate_cases({"GC001":record("a"),"Raden":record("b",repair=False)})
        self.assertEqual(result["research_gate"],"PASS")
        self.assertFalse(result["production_promotion_authorized"])
        self.assertIn("BROWSER_SVG_CLIPPING_AND_RASTER_PARITY_NOT_PASSED",
                      result["open_release_gates"])

    def test_unresolved_self_intersections_fail(self):
        broken=record("a")
        broken["candidate_self_intersecting_panels"]=[1]
        self.assertEqual(aggregate_cases({
            "GC001":broken,"Raden":record("b",repair=False),
        })["research_gate"],"FAIL")

    def test_fake_vertex_or_color_improvements_fail(self):
        bad=record("a")
        bad["candidate_total_vertices"]=35
        bad["saved_vertices"]=1
        self.assertEqual(aggregate_cases({
            "GC001":bad,"Raden":record("b",repair=False),
        })["research_gate"],"FAIL")
        bad=record("a")
        bad["optimized_apparel_color_lab_mse"]=5600
        self.assertEqual(aggregate_cases({
            "GC001":bad,"Raden":record("b",repair=False),
        })["research_gate"],"FAIL")

    def test_unrelated_character_must_be_byte_identical(self):
        nope=record("b",repair=False)
        nope["candidate_preview_sha256"]="d"*64
        self.assertEqual(aggregate_cases({
            "GC001":record("a"),"Raden":nope,
        })["research_gate"],"FAIL")

    def test_duplicate_sources_fail_closed(self):
        with self.assertRaises(ValueError):
            aggregate_cases({"GC001":record("a"),"Other":record("a",repair=False)})
        with self.assertRaises(ValueError):
            aggregate_cases({"Only":record("a")})


if __name__=="__main__":
    unittest.main()
