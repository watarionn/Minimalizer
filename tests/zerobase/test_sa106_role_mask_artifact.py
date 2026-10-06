from pathlib import Path

import numpy as np
import pytest

from minimalizer_zerobase.evaluation.role_mask_artifact import (
    read_role_mask_artifact,
    write_role_mask_artifact,
)


def test_role_mask_artifact_roundtrip_is_lossless(tmp_path: Path):
    hair = np.zeros((20, 30), bool); hair[2:8, 3:12] = True
    clothing = np.zeros((20, 30), bool); clothing[10:18, 5:25] = True
    manifest = write_role_mask_artifact(
        {"hair": hair, "major_clothing": clothing}, tmp_path
    )
    restored = read_role_mask_artifact(tmp_path)
    assert np.array_equal(restored["hair"], hair)
    assert np.array_equal(restored["major_clothing"], clothing)
    assert manifest["evaluation_only"] is True
    assert manifest["production_output_changed"] is False


def test_missing_role_fails_closed(tmp_path: Path):
    with pytest.raises(ValueError):
        write_role_mask_artifact({"hair": np.zeros((2, 2), bool)}, tmp_path)
