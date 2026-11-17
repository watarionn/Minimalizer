"""Safety regressions for strict enclosure and owner-identity preservation."""
import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from local_l02_enclosed_class32_shadow import propose_enclosed_class32_shadow, EnclosedClass32Hold


class TestEnclosedClass32(unittest.TestCase):
    def setup_scene(self):
        # One owner ring, one class32 hole; no human labels enter the function.
        owner = np.zeros((9, 9), dtype=np.uint8)
        owner[2, 2:7] = owner[6, 2:7] = 2
        owner[2:7, 2] = owner[2:7, 6] = 2
        cls = np.full_like(owner, 10)
        cls[3:6, 3:6] = 32
        alpha = np.full_like(owner, 255)
        return dict(source_alpha=alpha, class_ids=cls,
                    original_owner=owner.copy(), baseline_owner=owner)

    def test_enclosed_source_supported_fill(self):
        scene = self.setup_scene()
        result, report = propose_enclosed_class32_shadow(**scene)
        self.assertEqual(report['source_only_added_px'], 9)
        self.assertTrue(np.all(result[3:6, 3:6] == 2))
        self.assertEqual(report['Phase4'], 'FAIL')

    def test_diagonal_background_escape_not_filled(self):
        scene = self.setup_scene()
        # Diagonal hole in boundary is open to the outside under 8-neighbour
        # background connectivity, even if a 4-neighbour fill would close it.
        scene['baseline_owner'][2, 2] = 0
        scene['original_owner'][2, 2] = 0
        scene['class_ids'][2, 2] = 32
        result, _ = propose_enclosed_class32_shadow(**scene)
        self.assertEqual(result[3, 3], 0)

    def test_existing_veto_not_resurrected(self):
        scene = self.setup_scene()
        scene['original_owner'][4, 4] = 1
        result, _ = propose_enclosed_class32_shadow(**scene)
        self.assertEqual(result[4, 4], 0)

    def test_non_class32_hole_not_filled(self):
        scene = self.setup_scene()
        scene['class_ids'][4, 4] = 0
        result, _ = propose_enclosed_class32_shadow(**scene)
        self.assertEqual(result[4, 4], 0)

    def test_alpha_zero_hole_not_filled(self):
        scene = self.setup_scene()
        scene['source_alpha'][4, 4] = 0
        result, _ = propose_enclosed_class32_shadow(**scene)
        self.assertEqual(result[4, 4], 0)

    def test_invalid_owner_domain_rejected(self):
        scene = self.setup_scene()
        scene['original_owner'][3, 3] = 3
        with self.assertRaisesRegex(EnclosedClass32Hold, 'INVALID_MODEL_OR_OWNER_DOMAIN'):
            propose_enclosed_class32_shadow(**scene)

    def test_original_owner_reassignment_rejected(self):
        scene = self.setup_scene()
        scene['original_owner'][2, 3] = 1
        with self.assertRaisesRegex(EnclosedClass32Hold, 'ORIGINAL_OWNER_REASSIGNED'):
            propose_enclosed_class32_shadow(**scene)


if __name__ == '__main__':
    unittest.main()
