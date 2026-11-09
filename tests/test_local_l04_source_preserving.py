import importlib.util
from pathlib import Path

import numpy as np


SRC = (Path(__file__).resolve().parents[1] /
       "tools/research/local_l04_stage8_source_preserving.py")
spec = importlib.util.spec_from_file_location("local_l04_source_preserving", SRC)
source_preserving = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source_preserving)


def test_horizontal_corrections_merge_only_contiguous_same_owner_pixels():
    missing = np.array(
        [[True, True, True, True, False], [False, True, True, False, True]],
        dtype=bool,
    )
    owner_labels = np.array(
        [[1, 1, 1, 2, -1], [-1, 3, 3, -1, 3]],
        dtype=np.int16,
    )

    assert source_preserving._horizontal_corrections(missing, owner_labels) == [
        (0, 0, 3, "face"),
        (3, 0, 1, "hair"),
        (1, 1, 2, "head"),
        (4, 1, 1, "head"),
    ]


def test_horizontal_corrections_reject_shape_mismatch():
    with np.testing.assert_raises_regex(ValueError, "shape mismatch"):
        source_preserving._horizontal_corrections(
            np.zeros((1, 1), dtype=bool), np.zeros((1, 2), dtype=np.int16)
        )
