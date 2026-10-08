import unittest

from tools.run_sa1036_apparel_crosscase import aggregate_real_material_cases, EXPECTED


def example(tag: str, *, changed: bool) -> dict:
    common = {
        "schema": "sa10.36-uniform-material-benchmark-v1",
        "source_sha256": tag * 64,
        "stage04_mask_sha256_verified": True,
        "phase8_and_phase9_lineage_verified": True,
        "phase9_baseline_pixels_exact": True,
        "original_outer_silhouette_frozen": True,
        "original_outer_topology_pass": True,
        "face_and_both_arms_pixel_exact": True,
        "pixels_changed_outside_source_owner": 0,
        "original_outer_primitives_count": 11,
        "phase9_existing_subpaths": 3,
        "browser_svg_owner_clip_verified": False,
        "human_visual_review": "PENDING",
        "production_promotion_authorized": False,
        "baseline_image_sha256": "c" * 64,
    }
    if changed:
        return {
            **common,
            "research_status": "GRAY_BLOCK_REPLACED_RESEARCH_HOLD",
            "apparel_materials": EXPECTED,
            "material_subpaths_added": 5,
            "total_filled_geometric_element_estimate": 19,
            "lower_body_source_lab_mse_gain": .50,
            "gray_block_largest_connected_before_px": 12500,
            "gray_block_largest_connected_after_px": 500,
            "green_tie_panel_area_pixels": 1600,
            "source_green_tie_pixels": 1550,
            "material_extra_vertices": 38,
            "candidate_image_sha256": "d"*64,
        }
    return {
        **common,
        "research_status": "PATTERN_NOT_DETECTED_HOLD",
        "apparel_materials": [],
        "material_subpaths_added": 0,
        "total_filled_geometric_element_estimate": 14,
        "lower_body_source_lab_mse_gain": 0,
        "gray_block_largest_connected_before_px": 800,
        "gray_block_largest_connected_after_px": 800,
        "candidate_image_sha256": "c" * 64,
    }


class ApparelCrosscaseTests(unittest.TestCase):
    def test_corrected_image_and_safe_noop(self):
        r=aggregate_real_material_cases({"GC001": example("a", changed=True),
                                         "Raden": example("b",changed=False)})
        self.assertEqual(r["research_gate"],"PASS")
        self.assertFalse(r["production_promotion_authorized"])
        self.assertTrue(r["core_geometric_budget_still_failed"])

    def test_tie_expansion_out_of_bounds_is_rejected(self):
        changed=example("a",changed=True)
        changed["green_tie_panel_area_pixels"]=1900
        r=aggregate_real_material_cases({"GC001":changed,"Raden":example("b",changed=False)})
        self.assertEqual(r["research_gate"],"FAIL")

    def test_gray_blob_must_shrink(self):
        changed=example("a",changed=True)
        changed["gray_block_largest_connected_after_px"]=11000
        self.assertEqual(aggregate_real_material_cases({
            "GC001":changed,"Raden":example("b",changed=False),
        })["research_gate"],"FAIL")

    def test_nonmatching_character_cannot_be_repainted(self):
        skipped=example("b",changed=False)
        skipped["candidate_image_sha256"]="d"*64
        self.assertEqual(aggregate_real_material_cases({
            "GC001":example("a",changed=True),"Raden":skipped,
        })["research_gate"],"FAIL")

    def test_face_arm_protection_is_mandatory(self):
        changed=example("a",changed=True)
        changed["face_and_both_arms_pixel_exact"]=False
        self.assertEqual(aggregate_real_material_cases({
            "GC001":changed,"Raden":example("b",changed=False),
        })["research_gate"],"FAIL")

    def test_requires_two_different_source_hashes(self):
        with self.assertRaises(ValueError):
            aggregate_real_material_cases({"Only":example("a",changed=True)})
        with self.assertRaises(ValueError):
            aggregate_real_material_cases({"GC001":example("a",changed=True),
                                           "Raden":example("a",changed=False)})


if __name__=="__main__":
    unittest.main()
