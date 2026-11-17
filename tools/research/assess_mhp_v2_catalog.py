"""Assess the locally available MHP v2 catalog without opening image data.

This is an intake preflight only.  It reads the catalog's URL and label
metadata, never image pixels or annotations, and cannot create observer
inference input.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


class MHPV2CatalogHold(ValueError):
    """Raised when the catalog metadata is malformed."""


MHP_V2_REQUIRED_KEYS = frozenset({"annotationURLs", "imageURLs", "labels"})
MHP_V2_LABELS = frozenset(
    {
        "left-arm",
        "right-arm",
        "bikini/bra",
        "jacket/windbreaker/hoodie",
        "tee shirt",
        "polo shirt",
        "sweater",
        "singlet",
        "coat",
        "dress",
        "robe",
        "jumpsuit",
        "other full body clothes",
        "other upper body clothes",
        "other lower body clothes",
    }
)


@dataclass(frozen=True)
class MHPV2CatalogAssessment:
    dataset_revision: str
    sample_count: int
    observed_labels: tuple[str, ...]
    available_capabilities: tuple[str, ...]
    missing_capabilities: tuple[str, ...]
    status: str
    image_data_read: bool
    holdout_data_read: bool


def assess_mhp_v2_catalog(
    catalog: Mapping[str, object], *, dataset_revision: str
) -> MHPV2CatalogAssessment:
    """Return a fail-closed capability assessment from MHP metadata only."""
    if not isinstance(catalog, Mapping):
        raise MHPV2CatalogHold("INVALID_CATALOG")
    if not isinstance(dataset_revision, str) or not dataset_revision:
        raise MHPV2CatalogHold("INVALID_DATASET_REVISION")
    if not MHP_V2_REQUIRED_KEYS.issubset(catalog):
        raise MHPV2CatalogHold("MISSING_CATALOG_KEYS")

    annotation_urls = catalog["annotationURLs"]
    image_urls = catalog["imageURLs"]
    labels = catalog["labels"]
    if not (
        isinstance(annotation_urls, Sequence)
        and not isinstance(annotation_urls, (str, bytes))
        and isinstance(image_urls, Sequence)
        and not isinstance(image_urls, (str, bytes))
        and isinstance(labels, Sequence)
        and not isinstance(labels, (str, bytes))
    ):
        raise MHPV2CatalogHold("INVALID_CATALOG_ARRAYS")
    if len(annotation_urls) != len(image_urls) or not annotation_urls:
        raise MHPV2CatalogHold("CATALOG_IMAGE_ANNOTATION_COUNT_MISMATCH")
    if not all(isinstance(value, str) and value for value in (*annotation_urls, *image_urls, *labels)):
        raise MHPV2CatalogHold("INVALID_CATALOG_ENTRY")

    observed = tuple(sorted(set(labels) & MHP_V2_LABELS))
    available: set[str] = set()
    if {"left-arm", "right-arm"}.issubset(observed):
        available.add("arm")
    if any(label in observed for label in ("jacket/windbreaker/hoodie", "coat", "dress", "robe", "jumpsuit", "other full body clothes")):
        available.add("outerwear")
    if any(label in observed for label in ("bikini/bra", "tee shirt", "polo shirt", "sweater", "singlet")):
        available.add("underlayer")

    required = {
        "outerwear",
        "underlayer",
        "sleeve",
        "arm",
        "occlusion_relation",
        "instance_grouping",
    }
    missing = tuple(sorted(required - available))
    return MHPV2CatalogAssessment(
        dataset_revision=dataset_revision,
        sample_count=len(image_urls),
        observed_labels=observed,
        available_capabilities=tuple(sorted(available)),
        missing_capabilities=missing,
        status="TRAINING_CANDIDATE_INCOMPLETE" if missing else "TRAINING_CANDIDATE_REVIEW",
        image_data_read=False,
        holdout_data_read=False,
    )
