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
    # A class32 sleeve is valid owner=1 provenance but has no class5 seed.
    cls[cls == 5] = 32
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
    # The coat region must be class10, not a class5 jacket in disguise.
    cls[12:48, 12:84] = 10
    rgba[32:63, 32:63, :3] = 240
    result = propose(rgba, cls, owner)
    assert np.all((result == 0) | (result == owner))

def test_non_outerwear_owner_map_fails_closed_before_erosion():
    """A full-body owner map must never be treated as outerwear-only."""
    rgba, cls, owner = frame()
    owner[20:40, 20:40] = 3  # separate underlayer/skin owner, not garment
    rgba[32:63, 32:63, :3] = 240
    with pytest.raises(ValueError, match="UNSUPPORTED_OWNER_IDS"):
        propose(rgba, cls, owner)


def test_swapped_jacket_coat_seed_fails_closed():
    """Owner=2 cannot claim a class5 jacket seed as coat material."""
    rgba, cls, owner = frame()
    owner[20:40, 20:40] = 2
    with pytest.raises(ValueError, match="OWNER_CLASS_PROVENANCE_MISMATCH"):
        propose(rgba, cls, owner)


def test_non_garment_class_inside_valid_owner_id_fails_closed():
    """An ID in 0/1/2 is not sufficient evidence of garment provenance."""
    rgba, cls, owner = frame()
    cls[20:40, 20:40] = 7
    with pytest.raises(ValueError, match="OWNER_CLASS_PROVENANCE_MISMATCH"):
        propose(rgba, cls, owner)
