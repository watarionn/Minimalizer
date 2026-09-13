import cv2
import numpy as np

from minimalize_engine.structure_first import build_structure_first_parts
from minimalize_engine.structure_first_color import build_structure_first_color_shapes
from minimalize_engine.structure_foreground import build_structure_foreground
from minimalize_engine.structure_face_locator import locate_structure_face
from minimalize_engine.structure_head_anchor import build_face_anchored_head


def _synthetic_pose() -> tuple[np.ndarray, np.ndarray]:
    rgb = np.full((256, 256, 3), 245, dtype=np.uint8)
    mask = np.zeros((256, 256), dtype=np.uint8)

    cv2.circle(mask, (128, 54), 34, 1, -1)
    cv2.rectangle(mask, (98, 82), (158, 205), 1, -1)
    cv2.fillPoly(mask, [np.asarray([(100, 94), (66, 80), (24, 42), (15, 58), (72, 124)])], 1)
    cv2.fillPoly(mask, [np.asarray([(156, 95), (185, 72), (225, 29), (242, 45), (190, 125)])], 1)

    rgb[mask > 0] = (80, 90, 110)
    cv2.circle(rgb, (128, 58), 20, (235, 198, 178), -1)
    return rgb, mask


def test_structure_first_extracts_macro_parts_from_silhouette():
    rgb, mask = _synthetic_pose()
    result = build_structure_first_parts(rgb, mask)
    assert result.enabled is True
    parts = {shape.character_part for shape in result.shapes}
    assert {"face", "hair", "torso", "left_arm", "right_arm"}.issubset(parts)
    assert result.neck_y is not None


def test_structure_first_preserves_non_rectangular_arm_contours():
    rgb, mask = _synthetic_pose()
    result = build_structure_first_parts(rgb, mask)
    arms = [shape for shape in result.shapes if shape.character_part in {"left_arm", "right_arm"}]
    assert len(arms) == 2
    assert all(len(shape.points) >= 4 for shape in arms)
    assert any(
        x0 != x1 and y0 != y1
        for shape in arms
        for (x0, y0), (x1, y1) in zip(shape.points, shape.points[1:] + shape.points[:1])
    )


def test_structure_first_rejects_tiny_foreground():
    rgb = np.full((160, 160, 3), 255, dtype=np.uint8)
    mask = np.zeros((160, 160), dtype=np.uint8)
    mask[70:80, 70:80] = 1
    result = build_structure_first_parts(rgb, mask)
    assert result.enabled is False
    assert result.reason == "foreground_area_gate"


def test_structure_first_rejects_mask_size_mismatch():
    rgb = np.full((160, 160, 3), 255, dtype=np.uint8)
    mask = np.zeros((120, 160), dtype=np.uint8)
    result = build_structure_first_parts(rgb, mask)
    assert result.enabled is False
    assert result.reason == "mask_shape_mismatch"


def _synthetic_raised_hand_pose() -> tuple[np.ndarray, np.ndarray]:
    rgb = np.full((256, 256, 3), 245, dtype=np.uint8)
    mask = np.zeros((256, 256), dtype=np.uint8)
    cv2.circle(mask, (128, 66), 34, 1, -1)
    cv2.rectangle(mask, (100, 94), (158, 220), 1, -1)
    cv2.fillPoly(mask, [np.asarray([(155, 112), (177, 99), (190, 72), (207, 39), (220, 48), (202, 89), (184, 132)])], 1)
    cv2.circle(mask, (211, 41), 12, 1, -1)
    cv2.fillPoly(mask, [np.asarray([(101, 112), (76, 104), (42, 90), (33, 105), (78, 138)])], 1)
    rgb[mask > 0] = (72, 78, 92)
    cv2.circle(rgb, (128, 68), 20, (236, 199, 180), -1)
    cv2.circle(rgb, (211, 41), 12, (236, 199, 180), -1)
    return rgb, mask


def _synthetic_long_hair_pose() -> tuple[np.ndarray, np.ndarray]:
    rgb = np.full((256, 256, 3), 245, dtype=np.uint8)
    mask = np.zeros((256, 256), dtype=np.uint8)
    cv2.circle(mask, (128, 58), 38, 1, -1)
    cv2.rectangle(mask, (98, 88), (158, 220), 1, -1)
    cv2.fillPoly(mask, [np.asarray([(99, 72), (82, 76), (72, 178), (93, 188), (108, 92)])], 1)
    cv2.fillPoly(mask, [np.asarray([(157, 72), (174, 76), (184, 178), (163, 188), (148, 92)])], 1)
    rgb[mask > 0] = (70, 76, 94)
    cv2.circle(rgb, (128, 60), 20, (235, 198, 178), -1)
    return rgb, mask


def test_structure_first_recovers_raised_skin_hand_into_arm():
    rgb, mask = _synthetic_raised_hand_pose()
    result = build_structure_first_parts(rgb, mask)
    assert result.enabled is True
    assert result.recovery_stats["upper_gesture"]["right"] is True
    right_arm = result.masks["right_arm"]
    ys, xs = np.where(right_arm > 0)
    assert len(xs) > 0
    assert int(ys.min()) <= 55
    assert int(xs.max()) >= 205


def test_structure_first_expands_connected_long_hair_from_head_seed():
    rgb, mask = _synthetic_long_hair_pose()
    result = build_structure_first_parts(rgb, mask)
    assert result.enabled is True
    assert result.recovery_stats["long_hair"]["expanded"] is True
    hair = result.masks["hair"]
    ys, xs = np.where(hair > 0)
    assert len(xs) > 0
    assert int(ys.max()) >= 160
    assert int(xs.min()) <= 90
    assert int(xs.max()) >= 165


def test_structure_first_color_shapes_stay_coarse_and_part_scoped():
    rgb, mask = _synthetic_pose()
    # Force obvious second tones inside hair/torso without changing the structure mask.
    rgb[20:60, 96:128] = (40, 50, 70)
    rgb[60:96, 128:160] = (130, 140, 160)
    rgb[100:160, 98:128] = (30, 40, 50)
    rgb[100:160, 128:158] = (150, 160, 170)

    structure = build_structure_first_parts(rgb, mask)
    shapes = build_structure_first_color_shapes(rgb, structure)

    assert structure.enabled is True
    assert 5 <= len(shapes) <= 9
    parts = {shape.character_part for shape in shapes}
    assert {"face", "hair", "torso", "left_arm", "right_arm"}.issubset(parts)
    assert all(shape.source_role.startswith("phase17_structure_color_") for shape in shapes)


def test_structure_foreground_extracts_subject_from_flat_background():
    rgb, expected = _synthetic_pose()
    background = np.full_like(rgb, (246, 76, 142))
    background[expected > 0] = rgb[expected > 0]

    result = build_structure_foreground(background)

    assert result.enabled is True
    assert result.mask is not None
    overlap = np.logical_and(result.mask > 0, expected > 0).sum()
    recall = overlap / max(int((expected > 0).sum()), 1)
    assert recall >= 0.88
    assert result.foreground_area_ratio < 0.70


def test_structure_foreground_handles_two_plane_background():
    rgb, expected = _synthetic_pose()
    background = np.full_like(rgb, (242, 104, 82))
    cv2.fillPoly(
        background,
        [np.asarray([(0, 0), (256, 0), (256, 72), (0, 128)])],
        (228, 66, 130),
    )
    background[expected > 0] = rgb[expected > 0]

    result = build_structure_foreground(background)

    assert result.enabled is True
    overlap = np.logical_and(result.mask > 0, expected > 0).sum()
    recall = overlap / max(int((expected > 0).sum()), 1)
    assert recall >= 0.82


def test_structure_face_locator_finds_warm_face_inside_subject():
    rgb, subject = _synthetic_pose()
    result = locate_structure_face(rgb, subject)

    assert result.enabled is True
    assert result.mask is not None
    ys, xs = np.where(result.mask > 0)
    assert len(xs) > 0
    assert 105 <= int(np.median(xs)) <= 150
    assert 35 <= int(np.median(ys)) <= 90
    assert result.skin_density >= 0.12


def test_structure_face_locator_rejects_mask_shape_mismatch():
    rgb, _subject = _synthetic_pose()
    wrong = np.ones((120, 120), dtype=np.uint8)
    result = locate_structure_face(rgb, wrong)
    assert result.enabled is False
    assert result.reason == "mask_shape_mismatch"


def test_structure_face_accepts_relaxed_portrait_skin_window():
    rgb = np.full((240, 180, 3), (28, 32, 42), dtype=np.uint8)
    mask = np.zeros((240, 180), dtype=np.uint8)
    cv2.ellipse(mask, (90, 82), (38, 54), 0, 0, 360, 1, -1)
    cv2.rectangle(mask, (48, 118), (132, 228), 1, -1)
    rgb[mask > 0] = (90, 72, 68)
    cv2.ellipse(rgb, (90, 82), (24, 34), 0, 0, 360, (154, 118, 104), -1)
    cv2.circle(rgb, (82, 76), 3, (55, 44, 42), -1)
    cv2.circle(rgb, (98, 76), 3, (55, 44, 42), -1)

    result = locate_structure_face(rgb, mask)

    assert result.enabled is True
    assert result.bbox is not None


def test_structure_face_rejects_wide_skin_like_patch():
    rgb = np.full((220, 320, 3), (35, 40, 52), dtype=np.uint8)
    mask = np.zeros((220, 320), dtype=np.uint8)
    cv2.rectangle(mask, (42, 36), (280, 196), 1, -1)
    rgb[mask > 0] = (70, 76, 84)
    cv2.rectangle(rgb, (86, 70), (250, 112), (190, 148, 126), -1)

    result = locate_structure_face(rgb, mask)

    assert result.enabled is False


def test_face_anchored_head_wraps_face_inside_subject():
    rgb, mask = _synthetic_long_hair_pose()
    face = np.zeros_like(mask)
    cv2.ellipse(face, (128, 60), (20, 24), 0, 0, 360, 1, -1)

    result = build_face_anchored_head(rgb, mask, face)

    assert result.enabled is True
    assert result.head_mask is not None
    assert result.hair_mask is not None
    assert int((result.head_mask & face).sum()) > 0
    assert int(result.hair_mask.sum()) > int(face.sum())


def test_face_anchored_head_can_expand_long_hair():
    rgb, mask = _synthetic_long_hair_pose()
    face = np.zeros_like(mask)
    cv2.ellipse(face, (128, 60), (20, 24), 0, 0, 360, 1, -1)

    result = build_face_anchored_head(rgb, mask, face)

    assert result.enabled is True
    ys, _xs = np.where(result.hair_mask > 0)
    assert len(ys) > 0
    assert int(ys.max()) >= 150


def test_structure_mask_selector_prefers_low_leak_subject_mask():
    from minimalize_engine.structure_mask_selector import select_structure_mask

    rgb, subject = _synthetic_pose()
    leaky = np.ones_like(subject, dtype=np.uint8)
    selection = select_structure_mask(
        rgb,
        {"phase15_mask": leaky, "border_background": subject},
    )

    assert selection.enabled is True
    assert selection.source == "border_background"


def test_structure_mask_selector_prefers_face_valid_candidate():
    from minimalize_engine.structure_mask_selector import select_structure_mask

    rgb, subject = _synthetic_pose()
    bad = np.zeros_like(subject, dtype=np.uint8)
    cv2.rectangle(bad, (20, 120), (236, 220), 1, -1)
    selection = select_structure_mask(
        rgb,
        {"phase15_mask": bad, "border_background": subject},
    )

    assert selection.enabled is True
    assert selection.source == "border_background"


def test_structure_foreground_is_deterministic():
    rgb, expected = _synthetic_pose()
    background = np.full_like(rgb, (228, 88, 132))
    background[expected > 0] = rgb[expected > 0]

    first = build_structure_foreground(background)
    second = build_structure_foreground(background)

    assert first.enabled == second.enabled
    assert first.method == second.method
    assert first.mask is not None and second.mask is not None
    assert np.array_equal(first.mask, second.mask)


def test_structure_mask_selector_is_deterministic():
    from minimalize_engine.structure_mask_selector import select_structure_mask

    rgb, subject = _synthetic_pose()
    candidates = {"subject": subject, "leaky": np.ones_like(subject)}
    first = select_structure_mask(rgb, candidates)
    second = select_structure_mask(rgb, candidates)

    assert first.enabled == second.enabled
    assert first.source == second.source
    assert first.score == second.score


def test_face_seeded_completion_recovers_pale_upper_body():
    from minimalize_engine.structure_foreground_completion import complete_structure_foreground

    rgb = np.full((260, 260, 3), (232, 232, 236), dtype=np.uint8)
    expected = np.zeros((260, 260), dtype=np.uint8)
    cv2.circle(expected, (130, 64), 34, 1, -1)
    cv2.rectangle(expected, (88, 94), (172, 232), 1, -1)
    cv2.fillPoly(expected, [np.asarray([(90, 108), (48, 122), (25, 160), (42, 172), (104, 142)])], 1)
    cv2.fillPoly(expected, [np.asarray([(170, 108), (212, 122), (235, 160), (218, 172), (156, 142)])], 1)
    rgb[expected > 0] = (218, 219, 226)
    cv2.circle(rgb, (130, 64), 24, (236, 198, 178), -1)

    coarse = np.zeros_like(expected)
    cv2.circle(coarse, (130, 64), 36, 1, -1)
    cv2.rectangle(coarse, (112, 92), (148, 150), 1, -1)
    face = np.zeros_like(expected)
    cv2.ellipse(face, (130, 66), (20, 25), 0, 0, 360, 1, -1)
    result = complete_structure_foreground(rgb, coarse, face)

    assert result.enabled is True
    assert result.mask is not None
    recovered = int((result.mask & expected).sum())
    baseline = int((coarse & expected).sum())
    assert recovered > baseline * 1.35
    assert result.added_area_ratio > 0.01


def test_face_seeded_completion_is_deterministic():
    from minimalize_engine.structure_foreground_completion import complete_structure_foreground

    rgb, coarse = _synthetic_pose()
    face = np.zeros_like(coarse)
    cv2.ellipse(face, (128, 58), (18, 22), 0, 0, 360, 1, -1)
    first = complete_structure_foreground(rgb, coarse, face)
    second = complete_structure_foreground(rgb, coarse, face)

    assert first.enabled == second.enabled
    assert first.reason == second.reason
    assert first.mask is not None and second.mask is not None
    assert np.array_equal(first.mask, second.mask)


def test_completion_gate_accepts_large_low_leak_recovery():
    from minimalize_engine.structure_foreground_completion import (
        StructureForegroundCompletionResult,
        accept_structure_foreground_completion,
    )
    result = StructureForegroundCompletionResult(
        True,
        'ok',
        mask=np.ones((32, 32), dtype=np.uint8),
        original_area_ratio=0.20,
        completed_area_ratio=0.545,
        added_area_ratio=0.345,
        border_leak_ratio=0.011,
    )
    assert accept_structure_foreground_completion(result, 3.80, 3.79) is True


def test_completion_gate_rejects_large_leaky_recovery():
    from minimalize_engine.structure_foreground_completion import (
        StructureForegroundCompletionResult,
        accept_structure_foreground_completion,
    )
    result = StructureForegroundCompletionResult(
        True,
        'ok',
        mask=np.ones((32, 32), dtype=np.uint8),
        original_area_ratio=0.20,
        completed_area_ratio=0.609,
        added_area_ratio=0.409,
        border_leak_ratio=0.268,
    )
    assert accept_structure_foreground_completion(result, 3.80, 4.20) is False


def test_sleeve_completion_recovers_pale_wide_sleeves():
    from minimalize_engine.structure_sleeve_completion import complete_structure_sleeves

    rgb = np.full((260, 300, 3), (238, 238, 242), dtype=np.uint8)
    subject = np.zeros((260, 300), dtype=np.uint8)
    cv2.circle(subject, (150, 62), 32, 1, -1)
    cv2.rectangle(subject, (116, 92), (184, 224), 1, -1)
    cv2.fillPoly(subject, [np.asarray([(118, 108), (72, 104), (22, 142), (42, 178), (124, 150)])], 1)
    cv2.fillPoly(subject, [np.asarray([(182, 108), (228, 104), (278, 142), (258, 178), (176, 150)])], 1)
    rgb[subject > 0] = (220, 222, 229)
    cv2.circle(rgb, (150, 64), 22, (236, 198, 178), -1)

    coarse = np.zeros_like(subject)
    cv2.circle(coarse, (150, 62), 34, 1, -1)
    cv2.rectangle(coarse, (124, 92), (176, 220), 1, -1)
    face = np.zeros_like(subject)
    cv2.ellipse(face, (150, 64), (19, 24), 0, 0, 360, 1, -1)

    result = complete_structure_sleeves(rgb, coarse, face)
    assert result.enabled is True
    assert result.left_added is True and result.right_added is True
    assert result.added_area_ratio >= 0.02


def test_structure_body_planes_are_coarse_and_zone_scoped():
    from minimalize_engine.structure_body_planes import build_structure_body_planes

    rgb, subject = _synthetic_pose()
    face = np.zeros_like(subject)
    cv2.ellipse(face, (128, 58), (20, 24), 0, 0, 360, 1, -1)
    head = np.zeros_like(subject)
    cv2.ellipse(head, (128, 56), (40, 42), 0, 0, 360, 1, -1)
    hair = head & (1 - face)

    result = build_structure_body_planes(
        rgb,
        subject,
        face_mask=face,
        head_mask=head,
        hair_mask=hair,
    )

    assert result.enabled is True
    assert 1 <= result.zone_count <= 3
    assert len(result.shapes) <= 5
    assert all(shape.character_part in {"arm", "torso"} for shape in result.shapes)


def test_phase17_adaptive_polygon_preserves_pose_silhouette():
    from minimalize_engine.structure_geometry import polygon_iou, simplify_mask_polygon

    _rgb, subject = _synthetic_pose()
    points = simplify_mask_polygon(subject, max_points=28, min_iou=0.90)

    assert points is not None
    polygon = np.asarray(points, dtype=np.int32)
    assert len(polygon) <= 28
    assert polygon_iou(subject, polygon) >= 0.90


def test_phase17_alpha_structure_uses_local_carrier_patches_only():
    from minimalize_engine.alpha_structure import build_alpha_structure_shapes

    rgb, mask = _synthetic_pose()
    face = locate_structure_face(rgb, mask)
    assert face.enabled and face.mask is not None
    head = build_face_anchored_head(rgb, mask, face.mask)
    assert head.enabled
    result = build_alpha_structure_shapes(
        rgb,
        mask,
        face_mask=face.mask,
        head_mask=head.head_mask,
        hair_mask=head.hair_mask,
    )
    assert result.enabled is True
    assert all(shape.source_role != "phase17_alpha_carrier" for shape in result.shapes)
    assert result.carrier_exposure_ratio <= 0.30
    assert result.carrier_patch_count <= 6


def test_structure_voronoi_partition_covers_body_without_overlap():
    from minimalize_engine.structure_body_partition import partition_body_by_structure_seeds

    _rgb, subject = _synthetic_pose()
    face = np.zeros_like(subject)
    cv2.ellipse(face, (128, 58), (20, 24), 0, 0, 360, 1, -1)
    left = np.zeros_like(subject)
    right = np.zeros_like(subject)
    cv2.line(left, (110, 92), (44, 122), 1, 9)
    cv2.line(right, (146, 92), (212, 122), 1, 9)

    result = partition_body_by_structure_seeds(subject, face, left, right)
    assert result.enabled is True
    assert result.torso is not None and result.left_arm is not None and result.right_arm is not None
    assert not np.any((result.torso > 0) & (result.left_arm > 0))
    assert not np.any((result.torso > 0) & (result.right_arm > 0))
    assert not np.any((result.left_arm > 0) & (result.right_arm > 0))
    union = (result.torso | result.left_arm | result.right_arm).astype(np.uint8)
    assert not np.any(union & (1 - subject.astype(np.uint8)))


def test_structure_voronoi_requires_bilateral_arm_seeds():
    rgb, mask = _synthetic_raised_hand_pose()
    face = locate_structure_face(rgb, mask)
    assert face.enabled and face.mask is not None
    result = build_structure_first_parts(rgb, mask, face_anchor_mask=face.mask)
    stats = result.recovery_stats.get("body_partition", {})
    assert stats.get("accepted") is not True


def test_structure_voronoi_bilateral_skin_hands_obey_ratio_gate():
    rgb, mask = _synthetic_pose()
    cv2.circle(rgb, (23, 50), 9, (235, 198, 178), -1)
    cv2.circle(rgb, (233, 38), 9, (235, 198, 178), -1)
    face = locate_structure_face(rgb, mask)
    assert face.enabled and face.mask is not None
    result = build_structure_first_parts(rgb, mask, face_anchor_mask=face.mask)
    stats = result.recovery_stats.get("body_partition", {})
    assert stats.get("enabled") is True
    torso = float(stats.get("torso_ratio", 0.0))
    left = float(stats.get("left_arm_ratio", 0.0))
    right = float(stats.get("right_arm_ratio", 0.0))
    expected = 0.22 <= torso <= 0.55 and left >= 0.08 and right >= 0.08
    assert bool(stats.get("accepted")) is expected


def test_face_anchored_head_stays_compact_relative_to_subject():
    rgb, mask = _synthetic_pose()
    face = locate_structure_face(rgb, mask)
    assert face.enabled and face.mask is not None
    head = build_face_anchored_head(rgb, mask, face.mask)
    assert head.enabled and head.head_mask is not None
    subject_area = float(mask.sum())
    face_ratio = float(face.mask.sum()) / subject_area
    head_ratio = float(head.head_mask.sum()) / subject_area
    assert face_ratio <= 0.20
    assert face_ratio < head_ratio <= 0.35


def test_silhouette_head_caps_blank_face_against_real_head_area():
    from minimalize_engine.structure_head_silhouette import build_silhouette_head

    rgb, mask = _synthetic_long_hair_pose()
    face = locate_structure_face(rgb, mask)
    assert face.enabled and face.mask is not None
    result = build_silhouette_head(rgb, mask, face.mask)
    assert result.enabled is True
    assert result.head_mask is not None and result.face_mask is not None
    head_area = int(result.head_mask.sum())
    face_area = int(result.face_mask.sum())
    assert head_area > 0
    assert 0.12 <= face_area / head_area <= 0.30
    assert np.all(result.face_mask <= result.head_mask)


def test_phase17_hair_is_limited_to_three_coarse_planes():
    from minimalize_engine.alpha_structure import build_alpha_structure_shapes

    rgb, mask = _synthetic_long_hair_pose()
    face = locate_structure_face(rgb, mask)
    assert face.enabled and face.mask is not None
    head = build_face_anchored_head(rgb, mask, face.mask)
    assert head.enabled
    result = build_alpha_structure_shapes(
        rgb, mask, face_mask=face.mask,
        head_mask=head.head_mask, hair_mask=head.hair_mask,
    )
    hair = [s for s in result.shapes if s.character_part == "hair"]
    assert len(hair) <= 3
    assert all(len(shape.points) <= 8 for shape in hair)


def test_phase17_body_accent_is_torso_only_and_single():
    from minimalize_engine.structure_body_planes import build_structure_body_planes

    rgb, mask = _synthetic_pose()
    face = locate_structure_face(rgb, mask)
    assert face.enabled and face.mask is not None
    result = build_structure_body_planes(rgb, mask, face_mask=face.mask, max_accents=2)
    accents = [s for s in result.shapes if "phase17_body_accent_" in s.source_role]
    assert len(accents) <= 1
    assert all(s.source_role == "phase17_body_accent_torso" for s in accents)


def test_geometric_hair_split_uses_structural_roles_only():
    from minimalize_engine.alpha_structure import _split_hair_regions

    hair = np.zeros((180, 180), dtype=np.uint8)
    face = np.zeros_like(hair)
    head = np.zeros_like(hair)
    cv2.ellipse(face, (90, 70), (22, 28), 0, 0, 360, 1, -1)
    cv2.ellipse(head, (90, 66), (44, 52), 0, 0, 360, 1, -1)
    cv2.rectangle(hair, (42, 32), (138, 126), 1, -1)
    hair &= (1 - face)

    regions = _split_hair_regions(hair, face, head)
    roles = [role for role, _mask in regions]
    assert 1 <= len(regions) <= 3
    assert set(roles) <= {"front", "left", "right", "back"}
    assert len(roles) == len(set(roles))


def test_geometric_hair_split_does_not_cross_face_center_for_wings():
    from minimalize_engine.alpha_structure import _split_hair_regions

    hair = np.zeros((180, 180), dtype=np.uint8)
    face = np.zeros_like(hair)
    head = np.zeros_like(hair)
    cv2.ellipse(face, (90, 70), (20, 26), 0, 0, 360, 1, -1)
    cv2.ellipse(head, (90, 64), (42, 50), 0, 0, 360, 1, -1)
    cv2.rectangle(hair, (30, 38), (150, 142), 1, -1)
    hair &= (1 - face)

    regions = dict(_split_hair_regions(hair, face, head))
    xx = np.indices(hair.shape)[1]
    if "left" in regions:
        assert not np.any((regions["left"] > 0) & (xx >= 90))
    if "right" in regions:
        assert not np.any((regions["right"] > 0) & (xx < 90))


def _gate_shape(shape_id: int, role: str) -> "Shape":
    from minimalize_engine.models import Shape

    return Shape(
        id=shape_id,
        shape_type="polygon",
        fill_color=(120, 120, 120),
        points=[(0.0, 0.0), (4.0, 0.0), (4.0, 4.0)],
        source_role=role,
    )


def test_phase17_candidate_gate_accepts_coarse_complete_structure():
    from minimalize_engine.structure_candidate_gate import evaluate_structure_candidate

    shapes = (
        _gate_shape(1, "phase17_body_zone_left_sleeve"),
        _gate_shape(2, "phase17_body_zone_torso"),
        _gate_shape(3, "phase17_body_zone_right_sleeve"),
        _gate_shape(4, "phase17_alpha_hair_front"),
        _gate_shape(5, "phase17_alpha_hair_left"),
        _gate_shape(6, "phase17_alpha_blank_face"),
    )
    result = evaluate_structure_candidate(
        structure_enabled=True,
        face_enabled=True,
        head_enabled=True,
        alpha_enabled=True,
        shapes=shapes,
        carrier_exposure_ratio=0.12,
        carrier_patch_count=2,
    )
    assert result.passed is True
    assert result.hair_count == 2
    assert result.face_count == 1
    assert result.body_zone_count == 3


def test_phase17_candidate_gate_rejects_overfragmented_or_exposed_structure():
    from minimalize_engine.structure_candidate_gate import evaluate_structure_candidate

    shapes = tuple(
        [_gate_shape(i, f"phase17_alpha_hair_{i}") for i in range(1, 5)]
        + [_gate_shape(10, "phase17_body_zone_torso"), _gate_shape(11, "phase17_alpha_blank_face")]
    )
    result = evaluate_structure_candidate(
        structure_enabled=True,
        face_enabled=True,
        head_enabled=True,
        alpha_enabled=True,
        shapes=shapes,
        carrier_exposure_ratio=0.34,
        carrier_patch_count=7,
    )
    assert result.passed is False
    assert "hair_count_gate" in result.reasons
    assert "body_zone_gate" in result.reasons
    assert "carrier_exposure_gate" in result.reasons
    assert "carrier_patch_gate" in result.reasons
