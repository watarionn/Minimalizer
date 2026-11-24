from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "research"))
from verify_local_l02_six_cap_dataset import IntakeError, audit_dataset


class SixCapDatasetIntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.image_path = self.root / "private-source-name.png"
        Image.new("RGBA", (32, 32), (90, 70, 55, 255)).save(self.image_path)
        self.source_bytes = self.image_path.read_bytes()
        self.source_sha = hashlib.sha256(self.source_bytes).hexdigest()
        self.doc = {
            "schema": "minimalizer/local-l02-six-cap-annotation/v1",
            "image": {"source_sha256": self.source_sha, "width": 32, "height": 32,
                      "coordinate_space": "source_image_pixels"},
            "subject_group_id": "private-character-group",
            "annotator_id": "private-reviewer",
            "regions": [
                {"region_id": "region-1", "object_id": "person-1", "person_id": "person-1",
                 "role": "person", "points": [{"x": 3, "y": 3}, {"x": 28, "y": 3},
                                               {"x": 28, "y": 29}, {"x": 3, "y": 29}]},
                {"region_id": "region-2", "object_id": "coat-1", "person_id": "person-1",
                 "role": "outerwear", "points": [{"x": 7, "y": 8}, {"x": 24, "y": 8},
                                                  {"x": 24, "y": 23}, {"x": 7, "y": 23}]},
                {"region_id": "region-3", "object_id": "arm-left-1", "person_id": "person-1",
                 "role": "arm_left", "points": [{"x": 4, "y": 9}, {"x": 6, "y": 9},
                                                 {"x": 6, "y": 20}, {"x": 4, "y": 20}]},
            ],
            "complete_for": ["person", "outerwear"],
            "occlusion_relations": [{"occluder_id": "coat-1", "occluded_id": "arm-left-1",
                                     "relation": "occludes"}],
            "occlusion_relations_complete": False,
            "unknown_policy": "unmarked pixels remain unknown; only complete_for permits class-specific known negatives",
        }
        (self.root / "labels.json").write_text(json.dumps(self.doc), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_accepts_source_bound_annotation_and_emits_no_private_ids_or_paths(self):
        report = audit_dataset(self.root)
        self.assertEqual(report["image_count"], 1)
        self.assertEqual(report["region_counts_by_role"]["outerwear"], 1)
        self.assertEqual(report["occlusion_edge_count"], 1)
        self.assertEqual(report["unknown_policy"], self.doc["unknown_policy"])
        self.assertFalse(report["minimum_cross_person_annotation_coverage_present"])
        serialized = json.dumps(report)
        for private_value in (self.image_path.name, "private-character-group", "private-reviewer"):
            self.assertNotIn(private_value, serialized)
        self.assertNotIn('"points"', serialized)

    def test_rejects_source_sha_mismatch(self):
        bad = copy.deepcopy(self.doc)
        bad["image"]["source_sha256"] = "0" * 64
        (self.root / "labels.json").write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(IntakeError):
            audit_dataset(self.root)

    def test_rejects_self_intersection(self):
        bad = copy.deepcopy(self.doc)
        bad["regions"][1]["points"] = [{"x": 7, "y": 8}, {"x": 24, "y": 23},
                                         {"x": 24, "y": 8}, {"x": 7, "y": 23}]
        (self.root / "labels.json").write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(IntakeError):
            audit_dataset(self.root)

    def test_rejects_missing_occlusion_object(self):
        bad = copy.deepcopy(self.doc)
        bad["occlusion_relations"][0]["occluded_id"] = "missing-object"
        (self.root / "labels.json").write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(IntakeError):
            audit_dataset(self.root)

    def test_rejects_duplicate_source_image(self):
        (self.root / "duplicate.png").write_bytes(self.source_bytes)
        with self.assertRaises(IntakeError):
            audit_dataset(self.root)

    def test_reports_minimum_cross_person_inputs_without_claiming_training(self):
        self.image_path.unlink()
        (self.root / "labels.json").unlink()
        roles = ("person", "outerwear", "underlayer", "sleeve_left", "sleeve_right", "arm_left", "arm_right")
        for index in range(3):
            image_path = self.root / f"source-{index}.png"
            Image.new("RGBA", (64, 64), (40 + index, 70, 90, 255)).save(image_path)
            raw = image_path.read_bytes()
            regions = []
            for n, role in enumerate(roles):
                x, y = 2 + (n % 3) * 18, 2 + (n // 3) * 18
                regions.append({"region_id": f"region-{n}", "object_id": f"object-{role}",
                                "person_id": "person-1", "role": role,
                                "points": [{"x": x, "y": y}, {"x": x + 10, "y": y},
                                           {"x": x + 10, "y": y + 10}, {"x": x, "y": y + 10}]})
            doc = {"schema": self.doc["schema"],
                   "image": {"source_sha256": hashlib.sha256(raw).hexdigest(), "width": 64, "height": 64,
                             "coordinate_space": "source_image_pixels"},
                   "subject_group_id": f"group-{index}", "regions": regions,
                   "complete_for": list(roles),
                   "occlusion_relations": [{"occluder_id": "object-outerwear", "occluded_id": "object-arm_left",
                                            "relation": "occludes"}],
                   "occlusion_relations_complete": True,
                   "unknown_policy": self.doc["unknown_policy"]}
            (self.root / f"labels-{index}.json").write_text(json.dumps(doc), encoding="utf-8")
        report = audit_dataset(self.root)
        self.assertTrue(report["minimum_cross_person_annotation_coverage_present"])
        self.assertEqual(report["subject_group_count"], 3)
        self.assertFalse(report["observer_trained"])


if __name__ == "__main__":
    unittest.main()
