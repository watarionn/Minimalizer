from __future__ import annotations

import numpy as np

from minimalizer_zerobase.parts.decomposition import PART_NAMES
from minimalizer_zerobase.simplification.structural_source_repair import (
    apply_structural_source_repair,
)


def _source_masks() -> dict[str, np.ndarray]:
    shape = (160, 120)
    masks = {name: np.zeros(shape, dtype=bool) for name in PART_NAMES}
    masks["head"][12:58, 38:82] = True
    masks["face"][25:51, 48:72] = True
    masks["hair"][12:29, 38:82] = True
    masks["hair"][29:58, 38:48] = True
    masks["hair"][29:58, 72:82] = True
    masks["neck"][52:68, 54:66] = True
    masks["torso"][68:126, 38:82] = True
    masks["left_arm"][72:124, 82:103] = True
    masks["right_arm"][72:124, 17:38] = True
    masks["lower_body"][126:151, 42:78] = True
    masks["major_clothing"][72:126, 38:45] = True
    masks["accessory_or_held_object"][76:116, 57:63] = True
    return masks


def _groups(masks: dict[str, np.ndarray], *, drop_head=False, break_left_arm=False):
    groups = []
    order = 0
    for name in PART_NAMES:
        mask = masks[name]
        if not np.any(mask) or name == "unknown":
            continue
        if drop_head and name == "head":
            continue
        current = mask.copy()
        if break_left_arm and name == "left_arm":
            current[:] = False
            current[2:12, 2:6] = True
        groups.append(
            {
                "part": name,
                "color": (80, 100, 120),
                "mask": current,
                "source_ids": [f"primitive-{name}"],
                "source_actions": {"protect"},
                "first_order": order,
            }
        )
        order += 1
    return groups


def _source_rgba(shape=(160, 120)):
    image = np.zeros((*shape, 4), dtype=np.uint8)
    image[:, :, :3] = (100, 110, 120)
    image[:, :, 3] = 255
    return image


def _union(groups, part):
    found = [np.asarray(row["mask"]).astype(bool) for row in groups if row["part"] == part]
    return np.logical_or.reduce(found) if found else None


def test_structural_repair_restores_missing_head_and_broken_arm_from_source():
    masks = _source_masks()
    repaired, report = apply_structural_source_repair(
        _groups(masks, drop_head=True, break_left_arm=True),
        source_rgba=_source_rgba(),
        source_part_masks=masks,
        shape=(160, 120),
    )

    assert report["applied"] is True
    assert {"head", "left_arm"} <= set(report["repaired_parts"])
    assert report["missing_required_relations_after"] == []
    assert np.array_equal(_union(repaired, "head"), masks["head"])
    assert np.array_equal(_union(repaired, "left_arm"), masks["left_arm"])
    head = next(row for row in repaired if row["part"] == "head")
    assert head["source_guided_kind"] == "structural-source-repair-head"
    assert head["source_evidence_refs"] == ("phase04:part_masks/head.png",)


def test_structural_repair_does_not_touch_valid_structure():
    masks = _source_masks()
    groups = _groups(masks)
    repaired, report = apply_structural_source_repair(
        groups,
        source_rgba=_source_rgba(),
        source_part_masks=masks,
        shape=(160, 120),
    )

    assert report["applied"] is False
    assert report["repaired_parts"] == []
    assert len(repaired) == len(groups)
    for before, after in zip(groups, repaired):
        assert before["part"] == after["part"]
        assert np.array_equal(before["mask"], after["mask"])


def test_structural_support_only_is_not_visible_in_phase12_render():
    from minimalizer_zerobase.simplification.artifacts import _render

    shape = (20, 20)
    support = np.zeros(shape, dtype=bool)
    support[2:18, 2:18] = True
    visible = np.zeros(shape, dtype=bool)
    visible[8:12, 8:12] = True
    primitives = (
        {
            "primitive_id": "support",
            "palette_color_rgb": [255, 0, 0],
            "structural_support_only": True,
        },
        {
            "primitive_id": "visible",
            "palette_color_rgb": [10, 20, 30],
        },
    )
    rendered = _render(
        width=20,
        height=20,
        primitives=primitives,
        masks={"support": support, "visible": visible},
    )
    assert tuple(rendered[3, 3]) != (255, 0, 0)
    assert tuple(rendered[9, 9]) == (10, 20, 30)
