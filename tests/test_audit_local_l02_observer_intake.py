from __future__ import annotations

import hashlib
import json

from tools.research.audit_local_l02_observer_intake import (
    audit_checkpoint_input,
    audit_training_input,
)
from tools.research.import_live2d_training_catalog import (
    CATALOG_SCHEMA,
    REQUIRED_OCCLUSION_PAIRS,
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


def test_checkpoint_intake_checks_weight_sha_and_keeps_research_boundary(tmp_path):
    weights = tmp_path / "observer.bin"
    weights.write_bytes(b"fixed-checkpoint")
    weight_sha = hashlib.sha256(weights.read_bytes()).hexdigest()
    spec = tmp_path / "checkpoint.json"
    spec.write_text(
        json.dumps(
            {
                "schema": "minimalizer/l02/observer_checkpoint/v1",
                "observer_id": "six-capability-observer",
                "revision": "rev-1",
                "weights_sha256": weight_sha,
                "source_only": True,
                "human_labels_used_for_inference": False,
                "unknown_policy": "separate_from_negative",
                "same_config_cases": ["H04", "H06", "H08"],
                "output_contract": ROLES[1:5]
                + [
                    "occlusion_outerwear_underlayer",
                    "occlusion_sleeve_arm",
                    "occlusion_garment_body",
                    "instance_grouping",
                ],
            }
        ),
        encoding="utf-8",
    )

    result = audit_checkpoint_input(spec, weights)

    assert result["status"] == "CAPABILITY_PASS_RESEARCH_ONLY"
    assert result["weights_sha256"] == weight_sha
    assert result["same_config_cases"] == ("H04", "H06", "H08")
    assert result["phase4_or_production_authority"] is False


def test_checkpoint_intake_holds_when_a_pairwise_capability_is_missing(tmp_path):
    weights = tmp_path / "observer.bin"
    weights.write_bytes(b"fixed-checkpoint")
    spec = tmp_path / "checkpoint.json"
    spec.write_text(
        json.dumps(
            {
                "schema": "minimalizer/l02/observer_checkpoint/v1",
                "observer_id": "observer",
                "revision": "rev-1",
                "weights_sha256": hashlib.sha256(weights.read_bytes()).hexdigest(),
                "source_only": True,
                "human_labels_used_for_inference": False,
                "unknown_policy": "separate_from_negative",
                "same_config_cases": ["H04", "H06", "H08"],
                "output_contract": [
                    "outerwear",
                    "underlayer",
                    "sleeve",
                    "arm",
                    "occlusion_outerwear_underlayer",
                    "occlusion_sleeve_arm",
                    "instance_grouping",
                ],
            }
        ),
        encoding="utf-8",
    )

    result = audit_checkpoint_input(spec, weights)

    assert result["status"] == "CAPABILITY_HOLD"
    assert result["formal_probe_allowed"] is False
    assert "occlusion_garment_body" in result["missing_capabilities"]


def _catalog_sample(sample_id, character_id, case_id, split):
    return {
        "sample_id": sample_id,
        "character_id": character_id,
        "case_id": case_id,
        "split": split,
        "source_sha256": SOURCE_SHA256.get(
            case_id, hashlib.sha256(case_id.encode()).hexdigest()
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


def _write_catalog(path, samples):
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


def test_training_intake_reports_missing_sdk_without_promoting_catalog(tmp_path):
    catalog = tmp_path / "catalog.json"
    _write_catalog(
        catalog,
        [
            _catalog_sample("train", "train-person", "T1", "train"),
            _catalog_sample("validation", "validation-person", "V1", "validation"),
            _catalog_sample("h04", "h04-person", "H04", "holdout"),
            _catalog_sample("h06", "h06-person", "H06", "holdout"),
            _catalog_sample("h08", "h08-person", "H08", "holdout"),
        ],
    )

    result = audit_training_input(tmp_path / "missing-sdk", catalog)

    assert result["status"] == "TRAINING_INPUT_HOLD"
    assert any(item.startswith("SDK_FILE_MISSING:") for item in result["failures"])
    assert result["phase4_or_production_authority"] is False


def test_training_intake_requires_sdk_and_catalog_together(tmp_path):
    sdk = tmp_path / "sdk"
    (sdk / "Core/include").mkdir(parents=True)
    (sdk / "Core/lib/windows/x86_64").mkdir(parents=True)
    (sdk / "Samples/Common").mkdir(parents=True)
    (sdk / "Core/include/Live2DCubismCore.h").write_bytes(b"header")
    (sdk / "Core/lib/windows/x86_64/Live2DCubismCore.lib").write_bytes(b"library")

    result = audit_training_input(sdk, tmp_path / "missing-catalog.json")

    assert result["status"] == "TRAINING_INPUT_HOLD"
    assert "TRAINING_CATALOG_MISSING" in result["failures"]
    assert result["sdk"]["core_header"]["sha256"] == hashlib.sha256(b"header").hexdigest()
