"""Source-free negatives. No real source, human masks or coordinates."""
import importlib.util
from pathlib import Path
import numpy as np
import pytest
from scipy.ndimage import label, generate_binary_structure

SOURCE = Path(__file__).resolve().parents[1] / 'tools/research/local_l02_dark_seed_bright_island_shadow.py'
spec = importlib.util.spec_from_file_location('dark_seed', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
propose = module.propose_dark_seed_abstention


def frame(color=(20, 20, 30), n=96):
    rgba = np.zeros((n, n, 4), dtype=np.uint8)
    rgba[12:84, 12:84, :3] = color
    rgba[12:84, 12:84, 3] = 255
    owner = np.zeros((n, n), dtype=np.uint8)
    owner[12:84, 12:84] = 1
    cls = np.zeros((n, n), dtype=np.uint8)
    cls[12:84, 12:84] = 5
    return rgba, cls, owner


def test_dark_bright_island_does_not_create_or_reassign_owner():
    rgba, cls, owner = frame()
    rgba[32:63, 32:63, :3] = 240
    result = propose(rgba, cls, owner)
    assert np.count_nonzero((owner != 0) & (result == 0)) > 100
    assert np.all((result == 0) | (result == owner))
    for conn in (1, 2):
        st = generate_binary_structure(2, conn)
        assert label(result != 0, st)[1] == label(owner != 0, st)[1]


def test_light_garment_abstains():
    rgba, cls, owner = frame((200, 150, 130))
    rgba[32:63, 32:63, :3] = 250
    assert np.array_equal(propose(rgba, cls, owner), owner)


def test_no_seed_abstains():
    rgba, cls, owner = frame()
    cls[cls == 5] = 7
    assert np.array_equal(propose(rgba, cls, owner), owner)


def test_owner_cannot_exceed_alpha():
    rgba, cls, owner = frame()
    rgba[20, 20, 3] = 0
    with pytest.raises(ValueError):
        propose(rgba, cls, owner)


def test_invalid_shapes_fail_closed():
    rgba, cls, owner = frame()
    with pytest.raises(ValueError):
        propose(rgba, cls[:-1], owner)


def test_owner_ids_never_reassigned():
    rgba, cls, owner = frame()
    owner[12:48, 12:84] = 2
    rgba[32:63, 32:63, :3] = 240
    result = propose(rgba, cls, owner)
    assert np.all((result == 0) | (result == owner))
