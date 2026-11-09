from __future__ import annotations

import hashlib
import io

import numpy as np
import pytest
from PIL import Image

from tools.research.local_l02_source_owner_reconstruction import (
    SourceOwnerReconstructionHold,
    assert_owner_assignment_is_separate,
    reconstruct_source_regions,
)


def _source_bytes() -> bytes:
    rgba = np.zeros((8, 9, 4), dtype=np.uint8)
    rgba[1:7, 2:7, :3] = (80, 120, 160)
    rgba[1:7, 2:7, 3] = 255
    rgba[3, 3, 3] = 0
    output = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(output, format="PNG")
    return output.getvalue()


def _run(class_ids: np.ndarray):
    source = _source_bytes()
    return reconstruct_source_regions(
        source_bytes=source,
        expected_source_sha256=hashlib.sha256(source).hexdigest(),
        class_ids=class_ids,
        expected_class_map_sha256=hashlib.sha256(class_ids.tobytes()).hexdigest(),
    )


def test_reconstructs_whole_semantic_regions_without_owner_input():
    classes = np.zeros((8, 9), dtype=np.uint8)
    classes[1:3, 2:4] = 23
    classes[3:5, 4:6] = 13
    classes[5:7, 5:7] = 7
    regions, evidence = _run(classes)

    assert evidence.source_only is True
    assert evidence.human_labels_used is False
    assert evidence.owner_arrays_used is False
    assert evidence.unknown_not_treated_as_negative is True
    assert evidence.garment_pixels == 8
    assert evidence.arm_pixels == 4
    assert evidence.owner_assignment == "ABSTAIN_UNTIL_INDEPENDENT_OWNER_AUTHORITY"
    assert np.array_equal(regions["garment"], regions["upper_clothing"] | regions["lower_clothing"])
    assert not np.any(regions["garment"] & regions["arm"])
    assert int(regions["unknown"].sum()) > 0
    assert_owner_assignment_is_separate(evidence)


def test_transparent_pixels_are_not_observations_or_unknown_negatives():
    classes = np.zeros((8, 9), dtype=np.uint8)
    classes[3, 3] = 23  # This coordinate is transparent in the signed source.
    regions, evidence = _run(classes)

    assert not regions["garment"][3, 3]
    assert not regions["unknown"][3, 3]
    assert evidence.garment_pixels == 0


def test_signed_source_and_class_map_are_bound():
    classes = np.zeros((8, 9), dtype=np.uint8)
    source = _source_bytes()
    with pytest.raises(SourceOwnerReconstructionHold, match="SIGNED_SOURCE_SHA_MISMATCH"):
        reconstruct_source_regions(
            source_bytes=source,
            expected_source_sha256="0" * 64,
            class_ids=classes,
            expected_class_map_sha256=hashlib.sha256(classes.tobytes()).hexdigest(),
        )
    with pytest.raises(SourceOwnerReconstructionHold, match="CLASS_MAP_SHA_MISMATCH"):
        reconstruct_source_regions(
            source_bytes=source,
            expected_source_sha256=hashlib.sha256(source).hexdigest(),
            class_ids=classes,
            expected_class_map_sha256="0" * 64,
        )
