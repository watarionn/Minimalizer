import unittest
from tools.run_sa1032_gc001_owner_audit import audit_records

class OwnerAuditTests(unittest.TestCase):
    def test_explicit_owners_pass(self):
        rows = [{"owner": o} for o in ("face", "hair", "left_arm", "right_arm")]
        self.assertEqual(audit_records(rows)["status"], "OWNER_AUDIT_PASS")
    def test_no_color_inference(self):
        rows = [{"color": "#ffffff"} for _ in range(4)]
        self.assertEqual(audit_records(rows)["status"], "HOLD_OWNER_PROVENANCE")
    def test_missing_arm_rejected(self):
        rows = [{"owner": "face"}, {"owner": "hair"}, {"owner": "left_arm"}]
        self.assertIn("right_arm", audit_records(rows)["missing_required_owners"])
