from __future__ import annotations

import copy

import numpy as np

from minimalizer_zerobase.composition.semantic import rasterize_primitive_candidate
from minimalizer_zerobase.simplification import (
    StyleSimplificationPolicy,
    simplify_composed_scene,
)


def _polygon(
    primitive_id: str,
    part: str,
    color: tuple[int, int, int],
    points: list[list[float]],
    *,
    order: int,
) -> dict:
    return {
        "primitive_id": primitive_id,
        "primitive_type": "polygon",
        "parameters": {"components": [points], "corner_radius_px": 0},
        "composition_part": part,
        "semantic_part_id": part,
        "binding_status": "bound",
        "palette_color_rgb": list(color),
        "phase8_action": "protect",
        "raster_index": order,
    }


def _payload() -> dict:
    primitives = [
        _polygon(
            "hair-main",
            "hair",
            (150, 80, 60),
            [[20, 10], [50, 8], [75, 18], [70, 40], [25, 42]],
            order=0,
        ),
        _polygon(
            "hair-dot",
            "hair",
            (150, 80, 60),
            [[76, 18], [78, 18], [78, 20], [76, 20]],
            order=1,
        ),
        _polygon(
            "face",
            "face",
            (230, 190, 170),
            [[35, 22], [60, 22], [64, 39], [56, 52], [38, 50], [31, 37]],
            order=2,
        ),
        _polygon(
            "torso",
            "torso",
            (70, 100, 180),
            [[28, 50], [67, 50], [75, 91], [20, 91]],
            order=3,
        ),
        _polygon(
            "left-arm",
            "left_arm",
            (70, 100, 180),
            [[17, 52], [28, 52], [24, 84], [10, 80]],
            order=4,
        ),
        _polygon(
            "right-arm",
            "right_arm",
            (70, 100, 180),
            [[67, 52], [78, 54], [90, 80], [75, 84]],
            order=5,
        ),
        _polygon(
            "tie",
            "accessory_or_held_object",
            (80, 180, 70),
            [[45, 52], [51, 52], [54, 76], [48, 84], [43, 75]],
            order=6,
        ),
    ]
    return {
        "coordinate_space": {
            "pixel_width": 100,
            "pixel_height": 100,
            "normalized_origin": "top-left",
            "normalized_range": [0.0, 1.0],
        },
        "primitives_back_to_front": primitives,
        "validation": {"pass": True},
    }


def test_phase12_reduces_micro_fragments_without_losing_critical_parts() -> None:
    result = simplify_composed_scene(_payload())
    assert result.validation["pass"] is True
    assert result.selected is not None
    assert len(result.selected.primitives) < len(result.baseline_primitives)
    assert result.selected.metrics["silhouette_iou"] >= 0.92
    assert result.selected.metrics["critical_part_failures"] == []
    assert result.selected.metrics["missing_visible_parts"] == []


def test_phase12_is_deterministic() -> None:
    first = simplify_composed_scene(_payload())
    second = simplify_composed_scene(copy.deepcopy(_payload()))
    assert first.to_dict() == second.to_dict()


def test_phase12_fails_closed_on_failed_phase11() -> None:
    payload = _payload()
    payload["validation"]["pass"] = False
    try:
        simplify_composed_scene(payload)
    except ValueError as exc:
        assert "passing Phase 11" in str(exc)
    else:
        raise AssertionError("expected Phase 12 to reject failed Phase 11")


def test_policy_declares_visual_gate() -> None:
    policy = StyleSimplificationPolicy().to_dict()
    assert policy["grouping"] == "composition-part-plus-rgb"
    assert policy["generated_pixels"] == "forbidden-outside-rasterized-deterministic-geometry"


def test_phase12_source_guided_lower_body_recovers_large_planes() -> None:
    payload = _payload()
    payload["primitives_back_to_front"].append(
        _polygon(
            "lower-body",
            "lower_body",
            (80, 80, 88),
            [[18, 45], [82, 45], [78, 98], [22, 98]],
            order=7,
        )
    )
    source = np.zeros((100, 100, 4), dtype=np.uint8)
    source[:, :, :3] = (20, 20, 24)
    source[:, :, 3] = 255
    source[48:68, 28:56, :3] = (135, 128, 136)
    source[60:96, 42:50, :3] = (220, 218, 226)
    source[60:92, 55:63, :3] = (214, 212, 222)
    result = simplify_composed_scene(payload, source_rgba=source)
    assert result.validation["pass"] is True
    assert result.selected is not None
    kinds = {
        item.get("source_guided_kind")
        for item in result.selected.primitives
        if item.get("composition_part") == "lower_body"
    }
    assert "lower-body-light-leg-plane" in kinds
    assert "lower-body-light-skirt-plane" in kinds
    dark = next(
        item
        for item in result.selected.primitives
        if item.get("source_guided_kind") == "lower-body-dark-plane"
    )
    assert tuple(dark["palette_color_rgb"]) == (20, 20, 24)


def test_phase12_drops_only_small_neutral_unbound_group() -> None:
    payload = _payload()
    neutral = _polygon(
        "neutral-unbound",
        "__unbound__",
        (116, 111, 110),
        [[82, 10], [88, 10], [88, 16], [82, 16]],
        order=7,
    )
    neutral["semantic_part_id"] = None
    neutral["binding_status"] = "unbound"
    skin = _polygon(
        "skin-unbound",
        "__unbound__",
        (236, 204, 203),
        [[82, 20], [88, 20], [88, 26], [82, 26]],
        order=8,
    )
    skin["semantic_part_id"] = None
    skin["binding_status"] = "unbound"
    payload["primitives_back_to_front"].extend([neutral, skin])

    policy = StyleSimplificationPolicy(
        unbound_neutral_micro_max_area_ratio=0.01,
        unbound_neutral_micro_max_channel_range=12,
    )
    result = simplify_composed_scene(payload, policy=policy)

    assert result.validation["pass"] is True
    assert result.selected is not None
    unbound_colors = {
        tuple(item["palette_color_rgb"])
        for item in result.selected.primitives
        if item.get("composition_part") == "__unbound__"
    }
    assert (116, 111, 110) not in unbound_colors
    assert (236, 204, 203) in unbound_colors


def test_phase12_splits_large_hair_highlight_into_face_side_planes() -> None:
    payload = _payload()
    payload["primitives_back_to_front"][0] = _polygon(
        "hair-main",
        "hair",
        (55, 50, 60),
        [[8, 6], [92, 6], [92, 94], [8, 94]],
        order=0,
    )
    source = np.zeros((100, 100, 4), dtype=np.uint8)
    source[:, :, :3] = (30, 28, 34)
    source[:, :, 3] = 255
    source[24:88, 18:29, :3] = (215, 204, 198)
    source[24:88, 70:81, :3] = (185, 174, 170)

    result = simplify_composed_scene(payload, source_rgba=source)

    assert result.validation["pass"] is True
    assert result.selected is not None
    kinds = {
        item.get("source_guided_kind")
        for item in result.selected.primitives
        if item.get("composition_part") == "hair"
    }
    assert "hair-light-left-plane" in kinds
    assert "hair-light-right-plane" in kinds
    assert "hair-dark-plane" in kinds
    left = next(
        item
        for item in result.selected.primitives
        if item.get("source_guided_kind") == "hair-light-left-plane"
    )
    right = next(
        item
        for item in result.selected.primitives
        if item.get("source_guided_kind") == "hair-light-right-plane"
    )
    assert left["palette_color_rgb"][0] > right["palette_color_rgb"][0]


def test_phase12_side_hair_planes_do_not_fire_on_uniform_hair() -> None:
    payload = _payload()
    payload["primitives_back_to_front"][0] = _polygon(
        "hair-main",
        "hair",
        (55, 50, 60),
        [[8, 6], [92, 6], [92, 94], [8, 94]],
        order=0,
    )
    source = np.zeros((100, 100, 4), dtype=np.uint8)
    source[:, :, :3] = (55, 50, 60)
    source[:, :, 3] = 255

    result = simplify_composed_scene(payload, source_rgba=source)

    assert result.validation["pass"] is True
    assert result.selected is not None
    kinds = {
        item.get("source_guided_kind")
        for item in result.selected.primitives
        if item.get("composition_part") == "hair"
    }
    assert "hair-light-left-plane" not in kinds
    assert "hair-light-right-plane" not in kinds


def test_phase12_small_single_side_hair_highlight_falls_back_to_generic() -> None:
    payload = _payload()
    payload["primitives_back_to_front"][0] = _polygon(
        "hair-main",
        "hair",
        (55, 50, 60),
        [[8, 6], [92, 6], [92, 94], [8, 94]],
        order=0,
    )
    source = np.zeros((100, 100, 4), dtype=np.uint8)
    source[:, :, :3] = (30, 28, 34)
    source[:, :, 3] = 255
    source[28:36, 20:23, :3] = (215, 204, 198)

    result = simplify_composed_scene(payload, source_rgba=source)

    assert result.validation["pass"] is True
    assert result.selected is not None
    kinds = {
        item.get("source_guided_kind")
        for item in result.selected.primitives
        if item.get("composition_part") == "hair"
    }
    assert "hair-light-left-plane" not in kinds
    assert "hair-light-right-plane" not in kinds


def test_phase12_side_hair_plane_drops_relatively_dark_false_highlight() -> None:
    payload = _payload()
    payload["primitives_back_to_front"][0] = _polygon(
        "hair-main",
        "hair",
        (55, 50, 60),
        [[8, 6], [92, 6], [92, 94], [8, 94]],
        order=0,
    )
    source = np.zeros((100, 100, 4), dtype=np.uint8)
    source[:, :, :3] = (30, 28, 34)
    source[:, :, 3] = 255

    # Left side is a true high-luminance strand occupying enough of the
    # owner to define the hair's upper luminance band.
    source[24:88, 18:36, :3] = (215, 204, 198)
    # Right side is locally brighter than the dark hair but should not be
    # promoted to a light plane relative to the owner's own distribution.
    source[24:88, 70:81, :3] = (160, 150, 148)

    result = simplify_composed_scene(payload, source_rgba=source)

    assert result.validation["pass"] is True
    assert result.selected is not None
    kinds = {
        item.get("source_guided_kind")
        for item in result.selected.primitives
        if item.get("composition_part") == "hair"
    }
    assert "hair-light-left-plane" in kinds
    assert "hair-light-right-plane" not in kinds
    assert "hair-dark-plane" in kinds


def test_phase12_preserves_small_accessory_components_but_drops_tiny_noise() -> None:
    payload = _payload()
    shoulder = _polygon(
        "shoulder-accent",
        "accessory_or_held_object",
        (60, 155, 55),
        [[80, 20], [84, 20], [84, 24], [80, 24]],
        order=7,
    )
    noise = _polygon(
        "accessory-noise",
        "accessory_or_held_object",
        (60, 155, 55),
        [[90, 10], [91, 10], [91, 11], [90, 11]],
        order=8,
    )
    payload["primitives_back_to_front"].extend([shoulder, noise])

    policy = StyleSimplificationPolicy(
        accessory_min_component_area_ratio=0.002,
    )
    result = simplify_composed_scene(payload, policy=policy)

    assert result.validation["pass"] is True
    assert result.selected is not None
    accessory = next(
        item
        for item in result.selected.primitives
        if item.get("composition_part") == "accessory_or_held_object"
    )
    assert len(accessory["parameters"]["components"]) == 2


def test_phase12_face_color_uses_original_bright_support_not_closed_dark_features() -> None:
    payload = _payload()
    source = np.zeros((100, 100, 4), dtype=np.uint8)
    source[:, :, :3] = (28, 27, 32)
    source[:, :, 3] = 255

    source[20:55, 30:66, :3] = (246, 229, 226)
    source[30:35, 38:44, :3] = (55, 48, 52)
    source[30:35, 53:59, :3] = (55, 48, 52)
    source[43:47, 45:54, :3] = (90, 55, 58)

    result = simplify_composed_scene(payload, source_rgba=source)

    assert result.validation["pass"] is True
    assert result.selected is not None
    face = next(
        item
        for item in result.selected.primitives
        if item.get("composition_part") == "face"
    )
    assert face.get("source_guided_kind") == "face-light-plane"
    assert tuple(face["palette_color_rgb"]) == (246, 229, 226)


def test_hair_local_contrast_helper_keeps_only_medium_slender_streaks() -> None:
    import cv2

    from minimalizer_zerobase.simplification.style import (
        _hair_local_contrast_plane,
    )

    shape = (100, 100)
    base = np.zeros(shape, dtype=bool)
    base[8:94, 8:92] = True
    excluded = np.zeros(shape, dtype=bool)
    alpha = np.ones(shape, dtype=bool)
    rgb = np.full((*shape, 3), (55, 50, 60), dtype=np.uint8)

    valid = np.zeros(shape, dtype=bool)
    valid[30:70, 70:75] = True
    rgb[valid] = (160, 150, 148)

    too_large = np.zeros(shape, dtype=bool)
    too_large[40:65, 35:55] = True
    rgb[too_large] = (170, 160, 158)

    too_small = np.zeros(shape, dtype=bool)
    too_small[20:23, 60:64] = True
    rgb[too_small] = (170, 160, 158)

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    kept, color = _hair_local_contrast_plane(
        base,
        excluded,
        gray,
        rgb,
        alpha,
        shape,
        StyleSimplificationPolicy(),
    )

    assert np.count_nonzero(kept & valid) == np.count_nonzero(valid)
    assert not np.any(kept & too_large)
    assert not np.any(kept & too_small)
    assert color == (160, 150, 148)


def test_phase12_chromatic_hair_is_not_reinterpreted_as_achromatic_highlight() -> None:
    payload = _payload()
    payload["primitives_back_to_front"][0] = _polygon(
        "hair-main",
        "hair",
        (225, 123, 67),
        [[8, 6], [92, 6], [92, 94], [8, 94]],
        order=0,
    )
    source = np.zeros((100, 100, 4), dtype=np.uint8)
    source[:, :, :3] = (225, 123, 67)
    source[:, :, 3] = 255

    # Simulate a bright non-hair surface crossing the broad hair geometry.
    source[40:88, 35:78, :3] = (252, 250, 248)

    result = simplify_composed_scene(payload, source_rgba=source)

    assert result.validation["pass"] is True
    assert result.selected is not None
    hair = [
        item
        for item in result.selected.primitives
        if item.get("composition_part") == "hair"
    ]
    assert any(tuple(item["palette_color_rgb"]) == (225, 123, 67) for item in hair)
    assert not any(
        str(item.get("source_guided_kind") or "").startswith("hair-light")
        for item in hair
    )


def test_phase12_foot_openings_preserve_bright_shoe_cutouts_and_drop_tiny_noise() -> None:
    payload = _payload()
    payload["primitives_back_to_front"].append(
        _polygon(
            "lower-body-foot-case",
            "lower_body",
            (72, 72, 80),
            [[18, 45], [82, 45], [82, 98], [18, 98]],
            order=7,
        )
    )
    source = np.zeros((100, 100, 4), dtype=np.uint8)
    source[:, :, :3] = (20, 20, 24)
    source[:, :, 3] = 255

    # Dark skirt above, bright tights below.
    source[45:78, 18:82, :3] = (64, 62, 70)
    source[78:100, 18:83, :3] = (214, 212, 222)

    # Two dark shoes in the foot zone.
    source[79:100, 24:42, :3] = (28, 27, 31)
    source[79:100, 58:76, :3] = (30, 29, 33)

    # Meaningful elongated white openings in each shoe.
    source[84:96, 29:34, :3] = (220, 218, 228)
    source[82:95, 63:68, :3] = (218, 216, 226)

    # Tiny bright speck should not survive as an opening.
    source[91:93, 39:41, :3] = (222, 220, 230)

    result = simplify_composed_scene(payload, source_rgba=source)

    assert result.validation["pass"] is True
    assert result.selected is not None
    combined = [
        item
        for item in result.selected.primitives
        if item.get("source_guided_kind")
        == "lower-body-light-leg-and-foot-opening-plane"
    ]
    assert len(combined) == 1
    mask = rasterize_primitive_candidate(combined[0], width=100, height=100)
    assert mask[90, 31]
    assert mask[88, 65]
    assert not mask[91, 39]
    assert tuple(combined[0]["palette_color_rgb"]) == (214, 212, 222)


def test_phase12_torso_color_uses_brighter_half_for_dark_textured_material() -> None:
    payload = _payload()
    source = np.zeros((100, 100, 4), dtype=np.uint8)
    source[:, :, :3] = (20, 20, 24)
    source[:, :, 3] = 255

    torso_primitive = next(
        item
        for item in payload["primitives_back_to_front"]
        if item.get("composition_part") == "torso"
    )
    torso_mask = rasterize_primitive_candidate(
        torso_primitive, width=100, height=100
    )
    source[torso_mask, :3] = (40, 40, 45)
    ys, xs = np.where(torso_mask)
    order = np.argsort(ys * 100 + xs)
    split = len(order) // 2
    source[ys[order[split:]], xs[order[split:]], :3] = (70, 70, 75)

    result = simplify_composed_scene(payload, source_rgba=source)

    assert result.validation["pass"] is True
    assert result.selected is not None
    torso = next(
        item
        for item in result.selected.primitives
        if item.get("composition_part") == "torso"
    )
    assert torso.get("source_guided_kind") == "torso-source-midplane-color"
    assert tuple(torso["palette_color_rgb"]) == (70, 70, 75)


def test_phase12_wrist_skin_merges_existing_unbound_and_arm_skin_without_new_primitive() -> None:
    payload = _payload()
    existing_skin = _polygon(
        "existing-wrist-skin",
        "__unbound__",
        (236, 207, 203),
        [[11, 72], [13, 72], [13, 74], [11, 74]],
        order=7,
    )
    payload["primitives_back_to_front"].append(existing_skin)

    source = np.zeros((100, 100, 4), dtype=np.uint8)
    source[:, :, :3] = (24, 24, 28)
    source[:, :, 3] = 255

    for item in payload["primitives_back_to_front"]:
        mask = rasterize_primitive_candidate(item, width=100, height=100)
        part = item.get("composition_part")
        if part == "face":
            source[mask, :3] = (244, 224, 219)
        elif part in {"left_arm", "right_arm"}:
            source[mask, :3] = (52, 60, 74)
        elif part == "__unbound__":
            source[mask, :3] = (236, 207, 203)

    source[70:74, 78:80, :3] = (242, 211, 206)
    source[58:62, 72:76, :3] = (122, 126, 132)

    result = simplify_composed_scene(payload, source_rgba=source)

    assert result.validation["pass"] is True
    assert result.selected is not None
    overlays = [
        item
        for item in result.selected.primitives
        if item.get("source_guided_kind") == "wrist-skin-overlay"
    ]
    assert len(overlays) == 1
    mask = rasterize_primitive_candidate(overlays[0], width=100, height=100)
    assert mask[73, 12]
    assert mask[71, 79]
    assert not mask[59, 73]


def test_phase12_selection_prefers_silhouette_before_vertex_count_at_same_primitive_count() -> None:
    result = simplify_composed_scene(_payload())

    passing = [item for item in result.candidates if item.passed]
    assert passing
    expected = min(
        passing,
        key=lambda item: (
            int(item.metrics["primitive_count"]),
            -float(item.metrics["silhouette_iou"]),
            int(item.metrics["vertex_count"]),
        ),
    )
    assert result.selected is not None
    assert result.selected.name == expected.name
