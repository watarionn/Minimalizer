import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "research"))

from local_l02_observer_capability_gate import (  # noqa: E402
    ObserverCapabilityHold,
    ObserverCapabilitySpec,
    REQUIRED_CAPABILITIES,
    assess_observer_capability,
    see_through_bodypart_spec,
)


class ObserverCapabilityGateTests(unittest.TestCase):
    def test_current_see_through_is_held_for_missing_semantic_boundaries(self):
        result = assess_observer_capability(
            see_through_bodypart_spec(weights_sha256="a" * 64)
        )
        self.assertEqual(result["status"], "CAPABILITY_HOLD")
        self.assertFalse(result["formal_probe_allowed"])
        self.assertEqual(
            result["missing_capabilities"],
            (
                "arm",
                "instance_grouping",
                "occlusion_garment_body",
                "occlusion_outerwear_underlayer",
                "occlusion_sleeve_arm",
                "outerwear",
                "sleeve",
                "underlayer",
            ),
        )

    def test_complete_contract_only_admits_research_probe(self):
        spec = ObserverCapabilitySpec(
            observer_id="test-observer",
            revision="rev-1",
            weights_sha256="b" * 64,
            output_contract=(
                "outerwear",
                "underlayer",
                "sleeve",
                "arm",
                "occlusion_outerwear_underlayer",
                "occlusion_sleeve_arm",
                "occlusion_garment_body",
                "instance_grouping",
            ),
        )
        result = assess_observer_capability(spec)
        self.assertEqual(result["status"], "CAPABILITY_PASS_RESEARCH_ONLY")
        self.assertTrue(result["formal_probe_allowed"])

    def test_unpinned_weights_are_rejected(self):
        spec = ObserverCapabilitySpec("x", "rev", "not-a-sha", ("outerwear",))
        with self.assertRaisesRegex(ObserverCapabilityHold, "UNSIGNED_OR_UNPINNED_WEIGHTS"):
            assess_observer_capability(spec)

    def test_non_source_only_observer_is_rejected(self):
        spec = ObserverCapabilitySpec(
            "x", "rev", "c" * 64, ("outerwear",), source_only=False
        )
        with self.assertRaisesRegex(ObserverCapabilityHold, "NON_SOURCE_ONLY_OBSERVER"):
            assess_observer_capability(spec)

    def test_human_labels_are_rejected_even_with_a_complete_contract(self):
        spec = ObserverCapabilitySpec(
            "x",
            "rev",
            "d" * 64,
            tuple(sorted(REQUIRED_CAPABILITIES)),
            human_labels_used_for_inference=True,
        )
        with self.assertRaisesRegex(ObserverCapabilityHold, "HUMAN_LABELS_IN_INFERENCE"):
            assess_observer_capability(spec)

    def test_unknown_policy_must_remain_separate_from_negative(self):
        spec = ObserverCapabilitySpec(
            "x",
            "rev",
            "e" * 64,
            tuple(sorted(REQUIRED_CAPABILITIES)),
            unknown_policy="unknown_is_negative",
        )
        with self.assertRaisesRegex(ObserverCapabilityHold, "UNKNOWN_NOT_SEPARATE_FROM_NEGATIVE"):
            assess_observer_capability(spec)

    def test_all_three_cases_are_required_for_same_config_claim(self):
        spec = ObserverCapabilitySpec(
            "x",
            "rev",
            "f" * 64,
            tuple(sorted(REQUIRED_CAPABILITIES)),
            same_config_cases=("H04", "H06"),
        )
        with self.assertRaisesRegex(ObserverCapabilityHold, "THREE_CASE_SAME_CONFIG_NOT_DECLARED"):
            assess_observer_capability(spec)


if __name__ == "__main__":
    unittest.main(verbosity=2)
