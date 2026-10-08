import unittest

from tools.run_sa1032_gc001_owner_audit import audit_records, scene_records


class OwnerAuditTests(unittest.TestCase):
    def test_explicit_owners_pass(self):
        rows = [{"owner": o} for o in ("face", "hair", "left_arm", "right_arm")]
        self.assertEqual(audit_records(rows)["status"], "OWNER_AUDIT_PASS")

    def test_phase11_semantic_owner(self):
        rows = [{"semantic_part_id": o} for o in ("face", "hair", "left_arm", "right_arm")]
        self.assertEqual(audit_records(rows)["status"], "OWNER_AUDIT_PASS")

    def test_no_color_inference(self):
        rows = [{"color": "#ffffff"} for _ in range(4)]
        self.assertEqual(audit_records(rows)["status"], "HOLD_OWNER_PROVENANCE")

    def test_missing_arm_rejected(self):
        rows = [{"owner": "face"}, {"owner": "hair"}, {"owner": "left_arm"}]
        self.assertIn("right_arm", audit_records(rows)["missing_required_owners"])

    def test_unbound_is_not_reinterpreted(self):
        rows = [{"semantic_part_id": o, "composition_part": o} for o in ("face", "hair", "left_arm", "right_arm")]
        rows.append({"semantic_part_id": None, "composition_part": "__unbound__"})
        result = audit_records(rows)
        self.assertEqual(result["status"], "OWNER_AUDIT_PASS")
        self.assertEqual(result["unbound_primitive_count"], 1)
        self.assertNotIn("__unbound__", result["explicit_owner_counts"])

    def test_owner_disagreement_rejected(self):
        rows = [{"semantic_part_id": "face", "composition_part": "hair"}]
        self.assertEqual(audit_records(rows)["invalid_records"][0]["reason"], "conflicting_semantic_owner")

    def test_select_actual_phase12_candidate(self):
        selected = [{"semantic_part_id": o, "composition_part": o} for o in ("face", "hair", "left_arm", "right_arm")]
        scene = {"selected_name": "aggressive", "candidates": [{"name": "conservative", "primitives": []}, {"name": "aggressive", "primitives": selected}], "baseline": {"primitives": []}}
        self.assertEqual(scene_records(scene), selected)
        self.assertEqual(audit_records(scene_records(scene))["status"], "OWNER_AUDIT_PASS")
        self.assertEqual(scene_records(scene, "conservative"), [])
        self.assertEqual(scene_records(scene, "phase11"), [])

    def test_unknown_candidate_rejected(self):
        scene = {"selected_name": "missing", "candidates": []}
        with self.assertRaises(ValueError):
            scene_records(scene)
