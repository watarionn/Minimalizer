from __future__ import annotations

import numpy as np

from minimalizer_zerobase.semantic_abstraction.geometry_reauthoring import (
    semantic_reauthor_scene,
)
from minimalizer_zerobase.semantic_abstraction.ir import (
    AbstractionPlan,
    AbstractionPolicy,
    SemanticPart,
)


def _fixture() -> tuple[np.ndarray, dict[str, np.ndarray], AbstractionPlan]:
    rgb = np.full((100, 80, 3), 230, dtype=np.uint8)
    masks = {}
    for name in (
        "head",
        "face",
        "hair",
        "torso",
        "left_arm",
        "right_arm",
        "lower_body",
        "major_clothing",
        "accessory_or_held_object",
    ):
        masks[name] = np.zeros((100, 80), dtype=np.uint8)
    masks["head"][8:30, 28:52] = 1
    masks["face"][13:27, 33:47] = 1
    masks["hair"][5:19, 25:55] = 1
    masks["torso"][30:63, 26:54] = 1
    masks["left_arm"][34:66, 14:27] = 1
    masks["right_arm"][34:66, 53:66] = 1
    masks["lower_body"][60:94, 28:52] = 1
    masks["major_clothing"][31:61, 27:53] = 1
    masks["accessory_or_held_object"][20:28, 50:58] = 1
    rgb[masks["hair"].astype(bool)] = (220, 90, 50)
    rgb[masks["face"].astype(bool)] = (230, 190, 165)
    rgb[masks["major_clothing"].astype(bool)] = (35, 45, 80)
    rgb[43:51, 39:43] = (35, 150, 80)

    parts = tuple(
        SemanticPart(
            id=name,
            category=name,
            abstraction_policy=AbstractionPolicy.SIMPLIFY,
        )
        for name in masks
    )
    return rgb, masks, AbstractionPlan(parts=parts)


def test_face_is_one_plain_surface_and_no_facial_feature_primitive() -> None:
    rgb, masks, plan = _fixture()
    scene = semantic_reauthor_scene(rgb, masks, plan)
    face = [p for p in scene.primitives if p.source_region_id == "face"]
    assert len(face) == 1
    assert face[0].primitive_type == "ellipse"
    assert all("eye" not in p.primitive_id and "mouth" not in p.primitive_id for p in scene.primitives)


def test_each_arm_uses_at_most_two_axis_primitives() -> None:
    rgb, masks, plan = _fixture()
    scene = semantic_reauthor_scene(rgb, masks, plan)
    for arm in ("left_arm", "right_arm"):
        rows = [p for p in scene.primitives if p.source_region_id == arm]
        assert 1 <= len(rows) <= 2
        assert all(p.primitive_type == "convex_polygon" for p in rows)


def test_hair_uses_at_most_three_coarse_masses() -> None:
    rgb, masks, plan = _fixture()
    scene = semantic_reauthor_scene(rgb, masks, plan)
    rows = [p for p in scene.primitives if p.source_region_id == "hair"]
    assert 1 <= len(rows) <= 3


def test_suppressed_part_has_no_geometry() -> None:
    rgb, masks, plan = _fixture()
    changed = AbstractionPlan(
        parts=tuple(
            SemanticPart(
                id=p.id,
                category=p.category,
                abstraction_policy=(
                    AbstractionPolicy.SUPPRESS
                    if p.id == "right_arm"
                    else p.abstraction_policy
                ),
            )
            for p in plan.parts
        )
    )
    scene = semantic_reauthor_scene(rgb, masks, changed)
    assert not [p for p in scene.primitives if p.source_region_id == "right_arm"]


def test_reauthoring_is_deterministic() -> None:
    rgb, masks, plan = _fixture()
    first = semantic_reauthor_scene(rgb, masks, plan).to_dict()
    second = semantic_reauthor_scene(rgb, masks, plan).to_dict()
    assert first == second


def test_scene_uses_small_primitive_budget() -> None:
    rgb, masks, plan = _fixture()
    scene = semantic_reauthor_scene(rgb, masks, plan)
    assert len(scene.primitives) <= 18
