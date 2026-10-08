import unittest

from tools.run_sa1033_crosscase_gate import aggregate_cases


def sample(sha_char="a", *, reproducible=True, anatomy="FAIL", drift=True):
    return {
        "schema": "sa10.33-phase7-full-scene-authority-v1",
        "provenance": {
            "source_hash": sha_char * 64,
            "selected_render_preview_pixel_equal": reproducible,
            "selected_serialized_records_equal": reproducible,
            "guard_changed_outside_face_pixels": 0,
        },
        "reproduction_pass": reproducible,
        "owner_audit": {"status": "OWNER_AUDIT_PASS"},
        "parts": {owner: {
            "raw_source_topology_pass": not drift,
            "source_to_render": {"iou": 0.99},
            "lost_source_components_in_render": {"fully_missing_below_threshold_pixels": 1},
        } for owner in ("face", "hair", "left_arm", "right_arm")},
        "global": {"global_anatomy_gate": {
            "gate": anatomy,
            "source_evidence": {"topology": [1, 1]},
            "candidate_evidence": {"topology": [2, 1]},
            "metrics": {"silhouette_iou": 0.99},
        }},
        "source_topology_drift_owners": ["hair"] if drift else [],
        "serialized_export_drift_owners": ["hair"] if drift else [],
    }


class Phase7CrossCaseTests(unittest.TestCase):
    def test_two_distinct_cases_can_finish_negative_assessment(self):
        result = aggregate_cases({"GC001": sample("a"), "Raden": sample("b")})
        self.assertEqual(result["crosscase_evidence_coverage"], "PASS")
        self.assertEqual(result["structural_quality"], "FAIL")
        self.assertEqual(result["status"], "RESEARCH_COMPLETE_NO_GO")
        self.assertFalse(result["promotion_authorized"])
        self.assertEqual(result["human_visual_review"], "PENDING")

    def test_duplicate_source_does_not_count(self):
        result = aggregate_cases({"One": sample("a"), "RenamedOne": sample("a")})
        self.assertEqual(result["distinct_source_count"], 1)
        self.assertEqual(result["duplicate_source_count"], 1)
        self.assertEqual(result["crosscase_evidence_coverage"], "FAIL")

    def test_nonreproduced_case_does_not_pass_coverage(self):
        result = aggregate_cases({"GC001": sample("a"), "Raden": sample("b", reproducible=False)})
        self.assertEqual(result["crosscase_evidence_coverage"], "FAIL")

    def test_future_quality_pass_still_not_automatically_promoted(self):
        result = aggregate_cases({"One": sample("a", anatomy="PASS", drift=False), "Two": sample("b", anatomy="PASS", drift=False)})
        self.assertEqual(result["structural_quality"], "PASS")
        self.assertFalse(result["promotion_authorized"])
        self.assertEqual(result["human_visual_review"], "PENDING")

    def test_malformed_report_fails_closed(self):
        with self.assertRaises(ValueError):
            aggregate_cases({"broken": {"schema": "x"}})


if __name__ == "__main__":
    unittest.main()
