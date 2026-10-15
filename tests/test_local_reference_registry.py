"""Synthetic-only negative and success-path tests, no private images."""
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "qa"))
from verify_local_reference_registry import (AuthorityError, load_registry, verify_approved78,
                                             verify_h04_private, git_blob_sha, sha256)

SHA = "a" * 64


def registry():
    cases = [{"id": i, "source_sha256": v, "human_golden": "HOLD",
              "actual_signed_original_rehashed_this_run": False}
             for i, v in zip(("H04", "GC001", "Raden"), ("a"*64, "b"*64, "c"*64))]
    cases[0].update(phase4_stage_sha256=SHA, part_mask_count=11,
                    run107_zip_sha256=SHA, run122_zip_sha256=SHA)
    return {"schema": "minimalizer-local-golden-input-registry/v1",
            "purpose": "evaluation_preparation_only", "signed_cases": cases,
            "golden_criteria": ["faceless_and_no_skin_plate", "hair_and_head", "clothing_and_accessories",
                                 "both_arms_and_pose", "silhouette_and_identity", "source_only_no_generated_detail"],
            "manual_reference": {"id":"KYOKO_MANUAL_REFERENCE_V1", "underlay_sha256": "d" * 64,
                                 "pixel_aligned_to_signed_gc001": False},
            "approved78": {"count": 78, "approved18_prefix_count":18, "git_blob_sha":"e"*40},
            "local_release_authorized": False, "production_changed": False}


class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.reg = registry()
        self.regpath = self.root / "registry.json"

    def load(self):
        self.regpath.write_text(json.dumps(self.reg))
        return load_registry(self.regpath)

    def test_good_registry(self):
        self.assertEqual(len(self.load()["signed_cases"]), 3)

    def test_no_forged_approval(self):
        self.reg["signed_cases"][0]["human_golden"] = "PASS"
        with self.assertRaisesRegex(AuthorityError, "Golden"): self.load()

    def test_unsupported_schema(self):
        self.reg["schema"] = "untrusted"
        with self.assertRaisesRegex(AuthorityError, "schema"): self.load()

    def test_duplicate_source(self):
        self.reg["signed_cases"][1]["source_sha256"] = "a"*64
        with self.assertRaisesRegex(AuthorityError, "duplicate"): self.load()

    def test_manual_identity_must_not_be_signed_gc001(self):
        self.reg["manual_reference"]["underlay_sha256"] = "b"*64
        with self.assertRaisesRegex(AuthorityError, "aligned"): self.load()

    def test_original_unverified_flag_cannot_be_true(self):
        self.reg["signed_cases"][2]["actual_signed_original_rehashed_this_run"] = True
        with self.assertRaisesRegex(AuthorityError, "byte verified"): self.load()

    def test_no_release_promotion(self):
        self.reg["local_release_authorized"] = True
        with self.assertRaisesRegex(AuthorityError, "release approval"): self.load()

    def test_golden_criteria_cannot_disappear(self):
        self.reg["golden_criteria"].pop()
        with self.assertRaisesRegex(AuthorityError, "criteria"): self.load()

    def test_approved78_frozen_manifest_and_duplicate_rejected(self):
        items = [{"index": i, "reference_filename": f"{i:02d}_fixture.png",
                  "scene_artifact": f"scenes/{i}", "candidate_artifact": f"candidates/{i}"}
                 for i in range(1, 79)]
        manifest = self.root / "Approved78.json"
        manifest.write_text(json.dumps({"corpus_id": "Approved-78", "references": items}))
        self.reg["approved78"]["git_blob_sha"] = git_blob_sha(manifest.read_bytes())
        self.assertEqual(verify_approved78(self.load(), manifest)["approved18_prefix_entries"], 18)
        items[4]["index"] = 4
        manifest.write_text(json.dumps({"corpus_id": "Approved-78", "references": items}))
        self.reg["approved78"]["git_blob_sha"] = git_blob_sha(manifest.read_bytes())
        with self.assertRaisesRegex(AuthorityError, "index"): verify_approved78(self.load(), manifest)

    def test_approved78_content_tamper_rejected(self):
        manifest = self.root / "Approved78.json"
        manifest.write_text("{}")
        with self.assertRaisesRegex(AuthorityError, "content differs"): verify_approved78(self.load(), manifest)

    def fake_archive_pair(self):
        masks = {f"part_masks/{name}.png": bytes([i, 5, 6]) for i, name in enumerate(sorted(
            ("accessory_or_held_object", "face", "hair", "head", "left_arm", "lower_body",
             "major_clothing", "neck", "right_arm", "torso", "unknown")), start=1)}
        stage = b"{\"schema\": \"synthetic phase4\"}"
        a = self.root / "122.zip"; b = self.root / "107.zip"
        with zipfile.ZipFile(a, "w") as z:
            for k, v in masks.items(): z.writestr(k, v)
            z.writestr("phase4_stage.json", stage)
            z.writestr("05_structure_graph.json", b"graph")
            z.writestr("phase5_stage.json", b"stage5")
        with zipfile.ZipFile(b, "w") as z:
            for k, v in masks.items(): z.writestr("phase_04/"+k, v)
            z.writestr("phase_04/stage.json", stage)
            z.writestr("phase_05/05_structure_graph.json", b"graph")
            z.writestr("phase_05/stage.json", b"stage5")
        self.reg["signed_cases"][0].update(
            phase4_stage_sha256=sha256(stage), run122_zip_sha256=sha256(a.read_bytes()),
            run107_zip_sha256=sha256(b.read_bytes()))
        return a, b

    def test_private_11_mask_replay(self):
        a,b=self.fake_archive_pair()
        self.assertEqual(verify_h04_private(self.load(),a,b)["signed_part_masks_byte_identical"],11)

    def test_private_archive_tamper_rejected(self):
        a,b=self.fake_archive_pair()
        with a.open("ab") as fp: fp.write(b"tamper")
        with self.assertRaisesRegex(AuthorityError, "archive SHA mismatch"): verify_h04_private(self.load(),a,b)


if __name__ == "__main__": unittest.main()
