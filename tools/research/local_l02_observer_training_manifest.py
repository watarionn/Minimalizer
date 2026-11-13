"""Validate the source-free training boundary for the L02 observer.

This module validates metadata only.  It never loads an image, mask, review,
or owner array and it never creates inference input.  H04/H06/H08 are frozen
holdouts and cannot appear in training or validation samples.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


class TrainingManifestHold(ValueError):
    """Raised when the observer training manifest would contaminate holdout."""


HOLDOUT_CASES = frozenset({"H04", "H06", "H08"})
ALLOWED_SPLITS = frozenset({"train", "validation", "holdout"})
REQUIRED_ANNOTATION_ROLES = frozenset(
    {
        "person_instance",
        "outerwear",
        "underlayer",
        "sleeve",
        "arm",
        "occlusion_outerwear_underlayer",
        "occlusion_sleeve_arm",
        "occlusion_garment_body",
        "unknown",
    }
)


@dataclass(frozen=True)
class TrainingSample:
    sample_id: str
    character_id: str
    case_id: str
    split: str
    source_sha256: str
    annotation_sha256: str
    annotation_roles: frozenset[str]


@dataclass(frozen=True)
class TrainingManifest:
    schema: str
    dataset_revision: str
    unknown_policy: str
    human_labels_used_for_holdout_inference: bool
    samples: tuple[TrainingSample, ...]


def _sha(value: str, field: str) -> None:
    if type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise TrainingManifestHold(f"INVALID_{field.upper()}_SHA256")


def _sample(sample: TrainingSample) -> None:
    if not isinstance(sample, TrainingSample):
        raise TrainingManifestHold("INVALID_SAMPLE")
    if not all(
        type(value) is str and value
        for value in (sample.sample_id, sample.character_id, sample.case_id)
    ):
        raise TrainingManifestHold("INVALID_SAMPLE_IDENTITY")
    if sample.split not in ALLOWED_SPLITS:
        raise TrainingManifestHold("INVALID_SPLIT")
    _sha(sample.source_sha256, "SOURCE")
    _sha(sample.annotation_sha256, "ANNOTATION")
    if not isinstance(sample.annotation_roles, frozenset):
        raise TrainingManifestHold("INVALID_ANNOTATION_ROLES")
    if sample.annotation_roles != REQUIRED_ANNOTATION_ROLES:
        raise TrainingManifestHold("INCOMPLETE_ANNOTATION_ROLES")
    if sample.split == "holdout" and sample.case_id not in HOLDOUT_CASES:
        raise TrainingManifestHold("UNDECLARED_HOLDOUT_CASE")
    if sample.split != "holdout" and sample.case_id in HOLDOUT_CASES:
        raise TrainingManifestHold("HOLDOUT_IN_TRAINING_DATA")


def validate_training_manifest(manifest: TrainingManifest) -> dict[str, object]:
    """Validate split and annotation boundaries without reading data files."""
    if not isinstance(manifest, TrainingManifest):
        raise TrainingManifestHold("INVALID_MANIFEST")
    if manifest.schema != "minimalizer/l02/observer_training_manifest/v1":
        raise TrainingManifestHold("INVALID_SCHEMA")
    if type(manifest.dataset_revision) is not str or not manifest.dataset_revision:
        raise TrainingManifestHold("INVALID_DATASET_REVISION")
    if manifest.unknown_policy != "separate_from_negative":
        raise TrainingManifestHold("UNKNOWN_NOT_SEPARATE_FROM_NEGATIVE")
    if manifest.human_labels_used_for_holdout_inference is not False:
        raise TrainingManifestHold("HUMAN_LABELS_IN_HOLDOUT_INFERENCE")
    if not isinstance(manifest.samples, tuple) or not manifest.samples:
        raise TrainingManifestHold("EMPTY_SAMPLES")

    sample_ids: set[str] = set()
    split_characters: dict[str, set[str]] = {split: set() for split in ALLOWED_SPLITS}
    holdout_cases: set[str] = set()
    for sample in manifest.samples:
        _sample(sample)
        if sample.sample_id in sample_ids:
            raise TrainingManifestHold("DUPLICATE_SAMPLE_ID")
        sample_ids.add(sample.sample_id)
        split_characters[sample.split].add(sample.character_id)
        if sample.split == "holdout":
            holdout_cases.add(sample.case_id)

    if holdout_cases != HOLDOUT_CASES:
        raise TrainingManifestHold("INCOMPLETE_HOLDOUT_CASES")
    if split_characters["holdout"] & (
        split_characters["train"] | split_characters["validation"]
    ):
        raise TrainingManifestHold("CHARACTER_LEAK_INTO_HOLDOUT")
    if split_characters["train"] & split_characters["validation"]:
        raise TrainingManifestHold("CHARACTER_LEAK_TRAIN_VALIDATION")
    return {
        "status": "TRAINING_MANIFEST_PASS",
        "schema": manifest.schema,
        "dataset_revision": manifest.dataset_revision,
        "sample_count": len(manifest.samples),
        "holdout_cases": tuple(sorted(holdout_cases)),
        "unknown_policy": manifest.unknown_policy,
        "holdout_inference_labels_used": False,
    }


def build_sample(
    *,
    sample_id: str,
    character_id: str,
    case_id: str,
    split: str,
    source_sha256: str,
    annotation_sha256: str,
    annotation_roles: Iterable[str] = REQUIRED_ANNOTATION_ROLES,
) -> TrainingSample:
    """Small helper for manifest producers; it does not read referenced files."""
    return TrainingSample(
        sample_id=sample_id,
        character_id=character_id,
        case_id=case_id,
        split=split,
        source_sha256=source_sha256,
        annotation_sha256=annotation_sha256,
        annotation_roles=frozenset(annotation_roles),
    )
