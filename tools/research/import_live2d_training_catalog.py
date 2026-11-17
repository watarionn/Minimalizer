"""Import a source-free, signed Live2D training catalog for the L02 observer.

The catalog is metadata only.  It does not load images, masks, model weights,
or human review files and it never creates inference input.  Private dataset
material is expected to remain outside the repository.  The importer binds
each sample to a source digest and a separate signature receipt, requires the
six observer capabilities, and delegates split/holdout checks to the shared
training-manifest validator.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping

from tools.research.local_l02_observer_training_manifest import (
    REQUIRED_ANNOTATION_ROLES,
    TrainingManifest,
    TrainingManifestHold,
    build_sample,
    validate_training_manifest,
)


CATALOG_SCHEMA = "minimalizer/l02/live2d_training_catalog/v1"
REQUIRED_OCCLUSION_PAIRS = frozenset(
    {
        "outerwear_underlayer",
        "sleeve_arm",
        "garment_body",
    }
)


@dataclass(frozen=True)
class CatalogSample:
    sample_id: str
    character_id: str
    case_id: str
    split: str
    source_sha256: str
    source_signature_receipt_sha256: str
    source_uri: str
    annotation_sha256: str
    annotation_uri: str
    annotation_roles: frozenset[str]
    occlusion_pairs: frozenset[str]
    instance_ids: tuple[str, ...]
    labels_in_inference_input: bool


def _sha(value: Any, field: str) -> str:
    if type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise TrainingManifestHold(f"INVALID_{field.upper()}_SHA256")
    return value


def _text(value: Any, field: str) -> str:
    if type(value) is not str or not value.strip():
        raise TrainingManifestHold(f"INVALID_{field.upper()}")
    return value


def _sample(raw: Mapping[str, Any], index: int) -> CatalogSample:
    if not isinstance(raw, Mapping):
        raise TrainingManifestHold(f"INVALID_CATALOG_SAMPLE:{index}")

    roles = raw.get("annotation_roles")
    if not isinstance(roles, list) or frozenset(roles) != REQUIRED_ANNOTATION_ROLES:
        raise TrainingManifestHold(f"INCOMPLETE_ANNOTATION_ROLES:{index}")

    pairs = raw.get("occlusion_pairs")
    if not isinstance(pairs, list) or frozenset(pairs) != REQUIRED_OCCLUSION_PAIRS:
        raise TrainingManifestHold(f"INCOMPLETE_OCCLUSION_PAIRS:{index}")

    instances = raw.get("instance_ids")
    if (
        not isinstance(instances, list)
        or not instances
        or any(type(value) is not str or not value.strip() for value in instances)
        or len(set(instances)) != len(instances)
    ):
        raise TrainingManifestHold(f"INVALID_INSTANCE_IDS:{index}")

    labels_in_inference_input = raw.get("labels_in_inference_input")
    if labels_in_inference_input is not False:
        raise TrainingManifestHold(f"HUMAN_LABELS_IN_INFERENCE_INPUT:{index}")

    return CatalogSample(
        sample_id=_text(raw.get("sample_id"), "sample_id"),
        character_id=_text(raw.get("character_id"), "character_id"),
        case_id=_text(raw.get("case_id"), "case_id"),
        split=_text(raw.get("split"), "split"),
        source_sha256=_sha(raw.get("source_sha256"), "source"),
        source_signature_receipt_sha256=_sha(
            raw.get("source_signature_receipt_sha256"),
            "source_signature_receipt",
        ),
        source_uri=_text(raw.get("source_uri"), "source_uri"),
        annotation_sha256=_sha(raw.get("annotation_sha256"), "annotation"),
        annotation_uri=_text(raw.get("annotation_uri"), "annotation_uri"),
        annotation_roles=frozenset(roles),
        occlusion_pairs=frozenset(pairs),
        instance_ids=tuple(instances),
        labels_in_inference_input=False,
    )


def load_catalog(path: str | Path) -> tuple[CatalogSample, ...]:
    """Read and validate catalog metadata; private artifacts are not opened."""
    catalog_path = Path(path)
    try:
        raw = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TrainingManifestHold(f"CATALOG_READ_FAILED:{type(exc).__name__}") from exc

    if not isinstance(raw, Mapping) or raw.get("schema") != CATALOG_SCHEMA:
        raise TrainingManifestHold("INVALID_CATALOG_SCHEMA")
    if raw.get("source_artifacts_private") is not True:
        raise TrainingManifestHold("SOURCE_ARTIFACTS_NOT_PRIVATE")
    if raw.get("human_labels_used_for_holdout_inference") is not False:
        raise TrainingManifestHold("HUMAN_LABELS_IN_HOLDOUT_INFERENCE")
    samples = raw.get("samples")
    if not isinstance(samples, list) or not samples:
        raise TrainingManifestHold("EMPTY_CATALOG_SAMPLES")
    return tuple(_sample(sample, index) for index, sample in enumerate(samples))


def import_training_manifest(path: str | Path) -> tuple[TrainingManifest, dict[str, object]]:
    """Convert a validated catalog to the shared source-bound manifest.

    This function only returns metadata and the validation report.  A caller
    still needs an explicitly reviewed training runner; this importer does not
    promote the observer to Phase4 or production authority.
    """
    samples = load_catalog(path)
    manifest = TrainingManifest(
        schema="minimalizer/l02/observer_training_manifest/v1",
        dataset_revision=Path(path).stem,
        unknown_policy="separate_from_negative",
        human_labels_used_for_holdout_inference=False,
        samples=tuple(
            build_sample(
                sample_id=sample.sample_id,
                character_id=sample.character_id,
                case_id=sample.case_id,
                split=sample.split,
                source_sha256=sample.source_sha256,
                annotation_sha256=sample.annotation_sha256,
                annotation_roles=sample.annotation_roles,
            )
            for sample in samples
        ),
    )
    report = validate_training_manifest(manifest)
    report.update(
        {
            "catalog_schema": CATALOG_SCHEMA,
            "six_capability_catalog": True,
            "signed_source_receipts": len(samples),
            "inference_input_labels_used": False,
            "phase4_or_production_authority": False,
        }
    )
    return manifest, report
