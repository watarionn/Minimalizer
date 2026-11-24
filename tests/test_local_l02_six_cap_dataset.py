from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "research"))
from verify_local_l02_six_cap_dataset import IntakeError, audit_dataset
from rasterize_local_l02_six_cap_annotations import (
    _assert_private_output,
    rasterize_dataset,
    rasterize_one,
)
from split_local_l02_six_cap_dataset import build_split, write_split


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

    def test_rasterizes_exclusive_owners_and_preserves_unknown_pixels(self):
        masks = rasterize_one(self.source_bytes, self.doc)
        owner = masks["owner_outerwear"].astype(bool)
        known_coat = masks["known_outerwear"].astype(bool)
        arm = masks["owner_arm_left"].astype(bool)
        known_arm = masks["known_arm_left"].astype(bool)
        person = masks["person_instance_map"] > 0
        known_person = masks["known_person"].astype(bool)
        objects = masks["object_instance_map"] > 0
        alpha = masks["source_alpha"].astype(bool)
        self.assertTrue(np.all(known_coat == alpha))
        self.assertTrue(np.all(known_arm == arm))
        self.assertFalse(np.any(owner & arm))
        self.assertTrue(np.all((masks["owner_outerwear"] + masks["owner_arm_left"]) <= 1))
        self.assertTrue(np.all(person <= alpha))
        self.assertTrue(np.all(known_person == alpha))
        self.assertTrue(np.all(objects <= alpha))
        self.assertFalse(known_arm[0, 0])
        metadata = json.loads(str(masks["metadata_json"]))
        entities = metadata["occlusion_entity_ids_in_edge_index_order"]
        edge = masks["occlusion_relation_edge_index"][0]
        self.assertEqual(entities[int(edge[0]) - 1], "coat-1")
        self.assertEqual(entities[int(edge[1]) - 1], "arm-left-1")
        self.assertIn("person-1", metadata["occlusion_entity_ids_in_edge_index_order"])
        self.assertEqual(masks["occlusion_relations_complete"].item(), 0)
        partial = copy.deepcopy(self.doc)
        partial["complete_for"] = ["outerwear"]
        partial_masks = rasterize_one(self.source_bytes, partial)
        self.assertTrue(np.array_equal(partial_masks["known_person"], partial_masks["person_instance_map"] > 0))

    def test_rejects_semantic_owner_overlap(self):
        bad = copy.deepcopy(self.doc)
        bad["regions"][2]["points"] = [{"x": 8, "y": 9}, {"x": 10, "y": 9},
                                         {"x": 10, "y": 11}, {"x": 8, "y": 11}]
        with self.assertRaisesRegex(IntakeError, "owner masks overlap"):
            rasterize_one(self.source_bytes, bad)

    def test_rejects_part_outside_person_instance(self):
        bad = copy.deepcopy(self.doc)
        bad["regions"][2]["points"] = [{"x": 1, "y": 9}, {"x": 4, "y": 9},
                                         {"x": 4, "y": 12}, {"x": 1, "y": 12}]
        with self.assertRaisesRegex(IntakeError, "outside its visible person"):
            rasterize_one(self.source_bytes, bad)

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
                if role == "person":
                    x, y, x2, y2 = 0, 0, 63, 63
                else:
                    x, y = 2 + (n % 3) * 18, 2 + (n // 3) * 18
                    x2, y2 = x + 10, y + 10
                regions.append({"region_id": f"region-{n}", "object_id": f"object-{role}",
                                "person_id": "person-1", "role": role,
                                "points": [{"x": x, "y": y}, {"x": x2, "y": y},
                                           {"x": x2, "y": y2}, {"x": x, "y": y2}]})
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
        split_manifest, split_summary = build_split(self.root)
        self.assertEqual(split_summary["group_counts_by_split"], {
            "train": 1, "validation": 1, "blind_test": 1,
        })
        self.assertFalse(split_summary["group_leakage"])
        self.assertTrue(split_manifest["blind_test_labels_must_remain_sealed_until_model_freeze"])
        self.assertEqual(build_split(self.root)[1]["split_manifest_sha256"], split_summary["split_manifest_sha256"])
        with tempfile.TemporaryDirectory() as split_dir:
            written = write_split(self.root, split_dir)
            self.assertEqual(written["split_manifest_sha256"], split_summary["split_manifest_sha256"])
            split_path = Path(split_dir) / "person-group-split.private.json"
            self.assertTrue(split_path.is_file())
            with self.assertRaisesRegex(IntakeError, "outside the input dataset"):
                write_split(self.root, self.root / "split-output")
            with tempfile.TemporaryDirectory() as private_masks:
                receipt = rasterize_dataset(self.root, private_masks, split_path)
                self.assertEqual(receipt["private_mask_files_written"], 2)
                self.assertEqual(receipt["selected_splits"], ["train", "validation"])
                self.assertFalse(receipt["observer_trained"])
                self.assertFalse(receipt["output_paths_emitted"])
                self.assertFalse(receipt["blind_test_masks_emitted"])
                self.assertFalse(receipt["blind_test_used_for_training_or_validation"])
                self.assertEqual(len(list(Path(private_masks).glob("mask-*.npz"))), 2)
                with np.load(next(Path(private_masks).glob("mask-*.npz"))) as masks:
                    self.assertIn("owner_sleeve_left", masks.files)
                    self.assertIn("known_arm_right", masks.files)
                blind_sha = next(
                    record["source_sha256"] for record in split_manifest["records"]
                    if record["split"] == "blind_test"
                )
                stale_blind_mask = Path(private_masks) / f"mask-{blind_sha}.npz"
                stale_blind_mask.touch()
                with self.assertRaisesRegex(IntakeError, "outside the selected split"):
                    rasterize_dataset(self.root, private_masks, split_path)
                stale_blind_mask.unlink()
                with self.assertRaisesRegex(IntakeError, "frozen model checkpoint file"):
                    rasterize_dataset(self.root, private_masks, split_path, split_name="blind_test")
            with tempfile.TemporaryDirectory() as blind_masks, tempfile.TemporaryDirectory() as model_dir:
                model_path = Path(model_dir) / "frozen-observer.pt"
                model_path.write_bytes(b"frozen model test fixture")
                blind_receipt = rasterize_dataset(
                    self.root, blind_masks, split_path, split_name="blind_test", frozen_model_path=model_path,
                )
                self.assertEqual(blind_receipt["private_mask_files_written"], 1)
                self.assertTrue(blind_receipt["blind_test_masks_emitted"])
                self.assertEqual(blind_receipt["frozen_model_sha256"], hashlib.sha256(model_path.read_bytes()).hexdigest())

    def test_refuses_output_inside_git_worktree(self):
        repository = Path(__file__).resolve().parents[1]
        target = repository / "tests" / ".private-mask-output-test"
        with self.assertRaisesRegex(IntakeError, "inside any Git working tree"):
            _assert_private_output(target)


if __name__ == "__main__":
    unittest.main()
