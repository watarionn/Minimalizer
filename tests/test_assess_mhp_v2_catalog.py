from __future__ import annotations

import pytest

from tools.research.assess_mhp_v2_catalog import (
    MHPV2CatalogHold,
    assess_mhp_v2_catalog,
)


def _catalog():
    return {
        "annotationURLs": ["data/annotations/0001.png", "data/annotations/0002.png"],
        "imageURLs": ["data/images/0001.jpg", "data/images/0002.jpg"],
        "labels": [
            "background",
            "left-arm",
            "right-arm",
            "jacket/windbreaker/hoodie",
            "bikini/bra",
        ],
    }


def test_mhp_metadata_is_rejected_as_incomplete_without_images():
    result = assess_mhp_v2_catalog(_catalog(), dataset_revision="mhp-v2-catalog-local")

    assert result.sample_count == 2
    assert result.available_capabilities == ("arm", "outerwear", "underlayer")
    assert result.missing_capabilities == (
        "instance_grouping",
        "occlusion_relation",
        "sleeve",
    )
    assert result.status == "TRAINING_CANDIDATE_INCOMPLETE"
    assert result.image_data_read is False
    assert result.holdout_data_read is False


def test_mhp_catalog_rejects_mismatched_urls():
    catalog = _catalog()
    catalog["imageURLs"] = ["data/images/0001.jpg"]

    with pytest.raises(MHPV2CatalogHold, match="COUNT_MISMATCH"):
        assess_mhp_v2_catalog(catalog, dataset_revision="mhp-v2-catalog-local")
