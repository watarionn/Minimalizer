from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools.research.import_live2d_training_catalog import CATALOG_SCHEMA, REQUIRED_OCCLUSION_PAIRS
from tools.research.run_local_l02_observer_training import run_training
from tools.research.verify_local_l02_phase4_receipt import SOURCE_SHA256


ROLES = [
    "person_instance", "outerwear", "underlayer", "sleeve", "arm",
    "occlusion_outerwear_underlayer", "occlusion_sleeve_arm",
    "occlusion_garment_body", "unknown",
]
SHA = "a" * 64


def _sample(sample_id: str, character_id: str, case_id: str, split: str) -> dict[str, object]:
    return {
        "sample_id": sample_id,
        "character_id": character_id,
        "case_id": case_id,
        "split": split,
        "source_sha256": SOURCE_SHA256.get(case_id, hashlib.sha256(case_id.encode()).hexdigest()),
        "source_signature_receipt_sha256": SHA,
        "source_uri": f"private://signed/{sample_id}.png",
        "annotation_sha256": SHA,
        "annotation_uri": f"private://annotations/{sample_id}.json",
        "annotation_roles": ROLES,
        "occlusion_pairs": sorted(REQUIRED_OCCLUSION_PAIRS),
        "instance_ids": [f"{character_id}:person-0"],
        "labels_in_inference_input": False,
    }


def _write_catalog(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": CATALOG_SCHEMA,
                "source_artifacts_private": True,
                "human_labels_used_for_holdout_inference": False,
                "samples": [
                    _sample("train-1", "char-train", "T1", "train"),
                    _sample("validation-1", "char-validation", "V1", "validation"),
                    _sample("h04", "char-h04", "H04", "holdout"),
                    _sample("h06", "char-h06", "H06", "holdout"),
                    _sample("h08", "char-h08", "H08", "holdout"),
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_sdk(root: Path) -> None:
    (root / "Core/include").mkdir(parents=True)
    (root / "Core/lib/windows/x86_64").mkdir(parents=True)
    (root / "Samples/Common").mkdir(parents=True)
    (root / "Core/include/Live2DCubismCore.h").write_bytes(b"header")
    (root / "Core/lib/windows/x86_64/Live2DCubismCore.lib").write_bytes(b"library")


def _write_trainer(path: Path) -> None:
    path.write_text(
        """
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--sdk-root', required=True)
p.add_argument('--training-input', required=True)
p.add_argument('--output-spec', required=True)
p.add_argument('--output-weights', required=True)
a = p.parse_args()
feed = json.loads(Path(a.training_input).read_text(encoding='utf-8'))
assert feed['schema'] == 'minimalizer/local-l02/observer-training-input/v1'
assert all(item['case_id'] not in {'H04', 'H06', 'H08'} for item in feed['samples'])
weights = b'trained-six-capability-test-checkpoint'
Path(a.output_weights).write_bytes(weights)
spec = {
    'schema': 'minimalizer/l02/observer_checkpoint/v1',
    'observer_id': 'trained-test-observer',
    'revision': 'trained-test-revision',
    'weights_sha256': hashlib.sha256(weights).hexdigest(),
    'source_only': True,
    'human_labels_used_for_inference': False,
    'unknown_policy': 'separate_from_negative',
    'same_config_cases': ['H04', 'H06', 'H08'],
    'output_contract': [
        'outerwear', 'underlayer', 'sleeve', 'arm',
        'occlusion_outerwear_underlayer', 'occlusion_sleeve_arm',
        'occlusion_garment_body', 'instance_grouping',
    ],
}
Path(a.output_spec).write_text(json.dumps(spec), encoding='utf-8')
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_training_runner_excludes_holdout_and_freezes_checkpoint(tmp_path):
    sdk = tmp_path / "sdk"
    _write_sdk(sdk)
    catalog = tmp_path / "catalog.json"
    _write_catalog(catalog)
    trainer = tmp_path / "trainer.py"
    _write_trainer(trainer)

    output_dir = tmp_path / "private" / "checkpoint"
    receipt = tmp_path / "private" / "training-receipt.json"
    result = run_training(
        sdk_root=sdk,
        catalog=catalog,
        trainer=trainer,
        output_dir=output_dir,
        receipt=receipt,
        timeout_seconds=30,
    )

    assert result["status"] == "TRAINING_CHECKPOINT_FROZEN_RESEARCH_ONLY"
    assert result["holdout_excluded_from_trainer_feed"] == ["H04", "H06", "H08"]
    assert result["human_labels_used_for_holdout_inference"] is False
    assert (output_dir / "observer_spec.json").is_file()
    assert (output_dir / "observer_weights.bin").is_file()
    assert json.loads(receipt.read_text(encoding="utf-8"))["phase4"] == "HOLD"


def test_training_runner_refuses_existing_checkpoint(tmp_path):
    sdk = tmp_path / "sdk"
    _write_sdk(sdk)
    catalog = tmp_path / "catalog.json"
    _write_catalog(catalog)
    trainer = tmp_path / "trainer.py"
    _write_trainer(trainer)
    output_dir = tmp_path / "checkpoint"
    output_dir.mkdir()
    (output_dir / "observer_weights.bin").write_bytes(b"protected")

    with pytest.raises(ValueError, match="REFUSE_OVERWRITE_CHECKPOINT"):
        run_training(
            sdk_root=sdk,
            catalog=catalog,
            trainer=trainer,
            output_dir=output_dir,
            receipt=tmp_path / "receipt.json",
        )
