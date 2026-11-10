import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "research"))

from local_l02_observer_capability_gate import (  # noqa: E402
    ObserverCapabilityHold,
    ObserverCapabilitySpec,
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
            ("arm", "instance_grouping", "occlusion_relation", "outerwear", "sleeve", "underlayer"),
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
                "occlusion_relation",
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
