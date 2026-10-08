import unittest

from tools.run_sa1035_interior_crosscase import evaluate_crosscase


def evidence(sha: str) -> dict:
    return {
        "schema": "sa10.35-internal-color-evaluation-v1",
        "source_sha256": sha*64,
        "source_stage04_provenance_verified": True,
        "original_adaptive_preview_sha256_verified": True,
        "original_adaptive_preview_pixels_equal": True,
        "outer_raw_topology_gate": "PASS",
        "outer_silhouette_iou": 0.999,
        "external_geometry_changed": False,
        "face_and_both_arms_unchanged": True,
        "source_bitmap_painted": False,
        "observed_source_colors_only": True,
        "pixels_changed_outside_outer_silhouette": 0,
        "pixels_changed_outside_interior_subplanes": 0,
        "outer_primitive_count_before": 11,
        "outer_primitive_count_after": 11,
        "interior_subplane_count": 1,
        "new_geometric_subpaths_counted": 1,
        "interior_subplane_vertices": 12,
        "candidate_color_lab_mse_before": 2200.,
        "candidate_color_lab_mse_after": 1900.,
        "eligible_color_mse_improvement_ratio": 0.136,
        "planes": [{"owner": "hair"}],
        "production_promotion_authorized": False,
        "original_outer_vector_budget_pass": False,
    }


class InteriorCrossCaseTests(unittest.TestCase):
    def test_two_unique_cases_prove_research_not_production(self):
        result = evaluate_crosscase({"GC001": evidence("a"), "Raden": evidence("b")})
        self.assertEqual(result["reproducible_research_gate"], "PASS")
        self.assertFalse(result["promotion_authorized"])
        self.assertIn("BROWSER_SVG_CLIP_PARITY_UNVERIFIED", result["hard_blockers"])
        self.assertIn("ORIGINAL_OUTER_GEOMETRY_VERTEX_BUDGET_FAIL", result["hard_blockers"])

    def test_one_or_duplicate_source_cannot_pass(self):
        with self.assertRaises(ValueError):
            evaluate_crosscase({"GC001": evidence("a")})
        with self.assertRaises(ValueError):
            evaluate_crosscase({"GC001": evidence("a"), "OtherName": evidence("a")})

    def test_protected_pixel_change_rejected(self):
        changed = evidence("b")
        changed["face_and_both_arms_unchanged"] = False
        result = evaluate_crosscase({"GC001": evidence("a"), "Raden": changed})
        self.assertEqual(result["reproducible_research_gate"], "FAIL")
        self.assertFalse(result["promotion_authorized"])

    def test_added_geometry_must_be_counted(self):
        fake = evidence("b")
        fake["new_geometric_subpaths_counted"] = 0
        result = evaluate_crosscase({"GC001": evidence("a"), "Raden": fake})
        self.assertEqual(result["reproducible_research_gate"], "FAIL")

    def test_color_fit_worsening_rejected(self):
        fake = evidence("b")
        fake["candidate_color_lab_mse_after"] = 2500.0
        result = evaluate_crosscase({"GC001": evidence("a"), "Raden": fake})
        self.assertEqual(result["reproducible_research_gate"], "FAIL")


if __name__ == "__main__":
    unittest.main()
