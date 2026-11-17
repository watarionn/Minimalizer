import json
from hashlib import sha256

import pytest

from tools.research.import_live2d_training_catalog import (
    CATALOG_SCHEMA,
    REQUIRED_OCCLUSION_PAIRS,
    import_training_manifest,
)
from tools.research.verify_local_l02_phase4_receipt import SOURCE_SHA256


SHA = "a" * 64
ROLES = [
    "person_instance",
    "outerwear",
    "underlayer",
    "sleeve",
    "arm",
    "occlusion_outerwear_underlayer",
    "occlusion_sleeve_arm",
    "occlusion_garment_body",
    "unknown",
]


def _sample(sample_id, character_id, case_id, split):
    return {
        "sample_id": sample_id,
        "character_id": character_id,
        "case_id": case_id,
        "split": split,
        "source_sha256": SOURCE_SHA256.get(
            case_id, sha256(case_id.encode()).hexdigest()
        ),
        "source_signature_receipt_sha256": SHA,
        "source_uri": f"private://signed/{sample_id}.png",
        "annotation_sha256": SHA,
        "annotation_uri": f"private://annotations/{sample_id}.json",
        "annotation_roles": ROLES,
        "occlusion_pairs": sorted(REQUIRED_OCCLUSION_PAIRS),
        "instance_ids": [f"{character_id}:person-0"],
        "labels_in_inference_input": False,
    }


def _write_catalog(tmp_path, samples):
    path = tmp_path / "catalog.json"
    path.write_text(
        json.dumps(
            {
                "schema": CATALOG_SCHEMA,
                "source_artifacts_private": True,
                "human_labels_used_for_holdout_inference": False,
                "samples": samples,
            }
        ),
        encoding="utf-8",
    )
    return path


def _valid_samples():
    return [
        _sample("train-1", "char-train", "T1", "train"),
        _sample("validation-1", "char-validation", "V1", "validation"),
        _sample("h04", "char-h04", "H04", "holdout"),
        _sample("h06", "char-h06", "H06", "holdout"),
        _sample("h08", "char-h08", "H08", "holdout"),
    ]


def test_imports_six_capability_catalog_without_opening_private_artifacts(tmp_path):
    manifest, report = import_training_manifest(
        _write_catalog(tmp_path, _valid_samples())
    )
    assert report["status"] == "TRAINING_MANIFEST_PASS"
    assert report["six_capability_catalog"] is True
    assert report["inference_input_labels_used"] is False
    assert manifest.samples[0].annotation_roles == frozenset(ROLES)


def test_missing_source_signature_receipt_is_rejected(tmp_path):
    samples = _valid_samples()
    del samples[0]["source_signature_receipt_sha256"]
    with pytest.raises(ValueError, match="INVALID_SOURCE_SIGNATURE_RECEIPT_SHA256"):
        import_training_manifest(_write_catalog(tmp_path, samples))


def test_unknown_must_not_be_silently_used_as_inference_label(tmp_path):
    samples = _valid_samples()
    samples[0]["labels_in_inference_input"] = True
    with pytest.raises(ValueError, match="HUMAN_LABELS_IN_INFERENCE_INPUT"):
        import_training_manifest(_write_catalog(tmp_path, samples))


def test_all_three_occlusion_pairs_are_required(tmp_path):
    samples = _valid_samples()
    samples[0]["occlusion_pairs"] = ["sleeve_arm"]
    with pytest.raises(ValueError, match="INCOMPLETE_OCCLUSION_PAIRS"):
        import_training_manifest(_write_catalog(tmp_path, samples))


def test_holdout_source_cannot_be_relabelled_as_training(tmp_path):
    samples = _valid_samples()
    samples.append(_sample("alias", "other-character", "other", "train"))
    samples[-1]["source_sha256"] = SOURCE_SHA256["H06"]
    with pytest.raises(ValueError, match="HOLDOUT_SOURCE_IN_TRAINING_DATA"):
        import_training_manifest(_write_catalog(tmp_path, samples))
