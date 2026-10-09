"""SA10.44 source-owned mask reuse: fast unit gates and optional signed holdout."""
from pathlib import Path
from xml.etree import ElementTree as ET
import copy
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "research"))
import sa1044_shared_geometry as s


@pytest.fixture
def frozen():
    where = os.environ.get("SA1044_SIGNED_ROOT")
    if not where:
        pytest.skip("The private Raden source was not mounted: set SA1044_SIGNED_ROOT")
    return Path(where)


def test_signed_sources_and_authorized_aliases(frozen):
    masks, signed, right_delta = s.original_masks(frozen)
    assert right_delta == 2
    assert np.array_equal(masks["sa1041-owner-5"], signed["face"])
    assert np.array_equal(masks["sa1041-owner-3"], signed["left_arm"])
    assert not np.array_equal(masks["sa1041-owner-2"], signed["right_arm"])


def test_expanded_mask_budget_counts_references(frozen):
    masks, signed, _ = s.original_masks(frozen)
    root = ET.parse(frozen / "full_character_vector.svg").getroot()
    trial, result = s.compile_candidate(root, masks, signed, 0.5)
    assert result["unique_plus_stage9"] == 3510
    assert result["expanded_plus_stage9"] == 4086
    assert result["uses_expanded"] == 7
    assert result["reference_usages"][s.SHARED_ID["face"]] == 3
    assert result["reference_usages"][s.SHARED_ID["left_arm"]] == 2
    assert not result["expanded_under_budget"]
    assert "<image" not in s.svg_string(trial)


def test_stored_budget_must_not_be_promoted(frozen):
    masks, signed, _ = s.original_masks(frozen)
    root = ET.parse(frozen / "full_character_vector.svg").getroot()
    _, result = s.compile_candidate(root, masks, signed, 1.5)
    assert result["unique_plus_stage9"] == 1362
    assert result["expanded_plus_stage9"] == 1938
    assert result["unique_under_budget"] is True
    assert result["expanded_under_budget"] is False


def test_external_missing_or_cyclic_geometry_is_rejected(frozen):
    masks, signed, _ = s.original_masks(frozen)
    root = ET.parse(frozen / "full_character_vector.svg").getroot()
    svg, _ = s.compile_candidate(root, masks, signed, 0.5)
    broken = copy.deepcopy(svg)
    next(x for x in broken.iter() if x.tag == s.NS + "use").set("href", "#missing")
    with pytest.raises(ValueError, match="Broken"):
        s.count_expanded_and_stored(broken)
    with pytest.raises(ValueError, match="Nonlocal"):
        s.write_mask(ET.Element("mask"), 0, references=["https://example.com/geo.svg#x"])


def test_two_right_arm_masks_are_not_aliased(frozen):
    masks, signed, _ = s.original_masks(frozen)
    root = ET.parse(frozen / "full_character_vector.svg").getroot()
    svg, result = s.compile_candidate(root, masks, signed, 0.5)
    defs = svg.find(s.NS + "defs")
    owner = next(x for x in defs if x.get("id") == "sa1041-owner-2")
    protection = next(x for x in defs if x.get("id") == "sa1041-protected-clear")
    assert next(x for x in owner if x.tag == s.NS + "use").get("href") == "#" + s.SHARED_ID["right_arm_owner"]
    assert "#" + s.SHARED_ID["right_arm_signed"] in [
        x.get("href") for x in protection if x.tag == s.NS + "use"
    ]
    assert result["source_owner_right_vs_signed_pixels"] == 2


def test_path_accounting_rejects_bezier_notation():
    assert s.path_vertices("M 0 0 L 4 0 L 4 4 Z") == 3
    with pytest.raises(ValueError, match="Unexpected"):
        s.path_vertices("M 0 0 C 1 1 2 2 3 3 Z")


def test_missing_or_mismatched_source_mask_fails_closed():
    with pytest.raises(ValueError, match="Must give"):
        s.write_mask(ET.Element("mask"), 0)
    with pytest.raises(ValueError, match="Geometry/path"):
        s.write_mask(ET.Element("mask"), 5, path="M 0 0 L 1 0 L 1 1 Z")


def test_budget_and_provenance_invariants_remain_unchanged():
    assert s.BUDGET == 1412
    assert s.EXTRAS == 12
    assert len(s.prev.SHA) == 7
    assert set(s.SHARED_ID) == {
        "face", "left_arm", "right_arm_signed", "right_arm_owner"
    }
