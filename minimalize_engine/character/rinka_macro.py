from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from ..models import Shape
from .models import CharacterPartCandidate, CharacterStructure


@dataclass
class RinkaMacroReport:
    enabled: bool = False
    reason: str = "disabled"
    generated_shapes: int = 0
    retained_detail_shapes: int = 0
    part_shape_counts: dict[str, int] | None = None

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "generated_shapes": self.generated_shapes,
            "retained_detail_shapes": self.retained_detail_shapes,
            "part_shape_counts": dict(self.part_shape_counts or {}),
        }


def _part(structure: CharacterStructure, name: str) -> CharacterPartCandidate | None:
    return next((p for p in structure.parts if str(p.part_type) == name), None)


def _coarse_color_groups(
    image_rgb: np.ndarray,
    mask: np.ndarray,
    *,
    max_colors: int,
) -> list[tuple[tuple[int, int, int], np.ndarray, int]]:
    active = mask > 0
    pixels = image_rgb[active]
    if pixels.size == 0:
        return []
    bins = (pixels.astype(np.uint16) // 32).astype(np.int16)
    keys = bins[:, 0] * 64 + bins[:, 1] * 8 + bins[:, 2]
    values, counts = np.unique(keys, return_counts=True)
    order = np.argsort(counts)[::-1]
    groups: list[tuple[tuple[int, int, int], np.ndarray, int]] = []
    flat_active = np.flatnonzero(active)
    for idx in order[: max_colors * 3]:
        selected = keys == values[idx]
        count = int(selected.sum())
        if count < max(6, int(active.sum() * 0.035)):
            continue
        color = tuple(int(v) for v in np.median(pixels[selected], axis=0))
        group_mask = np.zeros(mask.shape, dtype=np.uint8)
        group_mask.flat[flat_active[selected]] = 1
        kernel = 3
        group_mask = cv2.morphologyEx(
            group_mask,
            cv2.MORPH_CLOSE,
            np.ones((kernel, kernel), np.uint8),
        )
        groups.append((color, group_mask, count))
        if len(groups) >= max_colors:
            break
    return groups


def _largest_contours(
    mask: np.ndarray,
    *,
    max_components: int,
    min_area: float,
) -> list[np.ndarray]:
    contours, _ = cv2.findContours(
        mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    usable = [c for c in contours if cv2.contourArea(c) >= min_area]
    usable.sort(key=cv2.contourArea, reverse=True)
    return usable[:max_components]


def _simplify_contour(contour: np.ndarray, max_vertices: int = 8) -> np.ndarray:
    perimeter = max(cv2.arcLength(contour, True), 1.0)
    epsilon = 0.018 * perimeter
    approx = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2)
    while len(approx) > max_vertices and epsilon < perimeter * 0.12:
        epsilon *= 1.25
        approx = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2)
    return approx


def _shape_from_contour(
    contour: np.ndarray,
    *,
    shape_id: int,
    color: tuple[int, int, int],
    z_index: int,
    semantic_type: str,
    character_part: str,
    source_role: str,
    layer_name: str,
) -> Shape | None:
    approx = _simplify_contour(contour)
    if len(approx) < 3:
        return None
    return Shape(
        id=shape_id,
        shape_type="polygon",
        fill_color=color,
        points=[(float(x), float(y)) for x, y in approx],
        z_index=z_index,
        importance=1.0,
        source_role=source_role,
        layer_name=layer_name,
        semantic_type=semantic_type,
        character_part=character_part,
        part_confidence=0.98,
    )


_PART_SPECS = {
    "hair": dict(max_colors=6, max_components=2, z=24200, accents=2),
    "left_leg": dict(max_colors=5, max_components=2, z=25000, accents=2),
    "right_leg": dict(max_colors=5, max_components=2, z=25020, accents=2),
    "outfit": dict(max_colors=8, max_components=2, z=26200, accents=3),
    "left_arm": dict(max_colors=5, max_components=2, z=27000, accents=2),
    "right_arm": dict(max_colors=5, max_components=2, z=27020, accents=2),
    "face": dict(max_colors=3, max_components=1, z=28200, accents=0),
}



def _macro_layer(part_name: str, *, accent: bool) -> str:
    if part_name == "hair":
        return "character_hair_detail" if accent else "character_hair_base"
    if part_name == "outfit":
        return "character_outfit_detail" if accent else "character_outfit_base"
    if part_name == "face":
        return "character_body_detail"
    return "character_body_detail" if accent else "character_body_base"

def _prioritize_outfit_groups(groups, face_ref):
    if len(groups) <= 1 or face_ref is None:
        return groups
    max_count = max((count for _, _, count in groups), default=1)
    ranked = []
    for group in groups:
        color, _, count = group
        rgb = np.asarray(color, dtype=np.uint8).reshape(1, 1, 3)
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0]
        contrast = min(1.0, float(np.linalg.norm(lab - face_ref)) / 42.0)
        chroma = min(1.0, float(np.std(np.asarray(color, dtype=np.float32))) / 60.0)
        usage = float(count) / max(float(max_count), 1.0)
        score = 0.35 * usage + 0.50 * contrast + 0.15 * chroma
        ranked.append((score, group))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [group for _, group in ranked]


def _keep_existing_detail(shape: Shape) -> bool:
    tags = " ".join(
        [
            str(shape.semantic_type or ""),
            str(shape.character_part or ""),
            str(shape.source_role or ""),
            str(shape.layer_name or ""),
        ]
    ).lower()
    return any(
        token in tags
        for token in (
            "prop",
            "sword",
            "staff",
            "hand",
            "accent",
        )
    )


def build_rinka_macro_partition(
    image_rgb: np.ndarray,
    structure: CharacterStructure,
    existing_shapes: list[Shape],
) -> tuple[list[Shape], RinkaMacroReport]:
    required = {"face", "hair", "outfit", "left_arm", "right_arm"}
    available = {str(p.part_type) for p in structure.parts}
    if not required.issubset(available):
        return existing_shapes, RinkaMacroReport(False, "part_gate")
    generated: list[Shape] = []
    counts: dict[str, int] = {}
    next_id = 795000
    image_lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    face_part = _part(structure, "face")
    hair_part = _part(structure, "hair")
    face_ref = None
    hair_ref = None
    if face_part is not None and np.any(face_part.mask):
        face_ref = np.median(image_lab[face_part.mask > 0], axis=0)
    if hair_part is not None and np.any(hair_part.mask):
        hair_ref = np.median(image_lab[hair_part.mask > 0], axis=0)
    for part_name, spec in _PART_SPECS.items():
        part = _part(structure, part_name)
        if part is None or part.mask is None or not np.any(part.mask):
            continue
        effective_mask = (part.mask > 0).astype(np.uint8)
        if part_name == "outfit":
            for exclusion_name in ("face", "hair", "left_arm", "right_arm"):
                exclusion = _part(structure, exclusion_name)
                if exclusion is not None and exclusion.mask is not None:
                    effective_mask[exclusion.mask > 0] = 0
            if face_ref is not None:
                skin_distance = np.linalg.norm(image_lab - face_ref[None, None, :], axis=2)
                effective_mask[skin_distance < 22.0] = 0
            if hair_ref is not None:
                hair_distance = np.linalg.norm(image_lab - hair_ref[None, None, :], axis=2)
                effective_mask[hair_distance < 15.0] = 0
        groups = _coarse_color_groups(
            image_rgb,
            effective_mask,
            max_colors=int(spec["max_colors"]),
        )
        if part_name == "outfit":
            groups = _prioritize_outfit_groups(groups, face_ref)
        part_count = 0
        part_area = max(float(np.count_nonzero(effective_mask)), 1.0)
        if not groups:
            counts[part_name] = 0
            continue
        base_color = groups[0][0]
        base_mask = np.zeros_like(effective_mask)
        for _, group_mask, _ in groups:
            base_mask = np.maximum(base_mask, group_mask)
        base_mask = cv2.morphologyEx(base_mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        base_contours = _largest_contours(
            base_mask,
            max_components=int(spec["max_components"]),
            min_area=max(8.0, part_area * 0.020),
        )
        for component_index, contour in enumerate(base_contours):
            shape = _shape_from_contour(
                contour,
                shape_id=next_id,
                color=base_color,
                z_index=int(spec["z"]) + component_index,
                semantic_type=f"rinka_macro_{part_name}",
                character_part=part_name,
                source_role=f"rinka_macro:{part_name}:base",
                layer_name=_macro_layer(part_name, accent=False),
            )
            next_id += 1
            if shape is not None:
                generated.append(shape)
                part_count += 1
        accent_limit = max(0, int(spec.get("accents", 0)))
        for group_index, (color, color_mask, _) in enumerate(groups[1 : 1 + accent_limit], start=1):
            contours = _largest_contours(
                color_mask,
                max_components=int(spec["max_components"]),
                min_area=max(8.0, part_area * 0.035),
            )
            for component_index, contour in enumerate(contours):
                shape = _shape_from_contour(
                    contour,
                    shape_id=next_id,
                    color=color,
                    z_index=int(spec["z"]) + 8 + group_index * 4 + component_index,
                    semantic_type=f"rinka_macro_{part_name}_accent",
                    character_part=part_name,
                    source_role=f"rinka_macro:{part_name}:accent",
                    layer_name=_macro_layer(part_name, accent=True),
                )
                next_id += 1
                if shape is not None:
                    generated.append(shape)
                    part_count += 1
        counts[part_name] = part_count

    if counts.get("face", 0) < 1 or counts.get("outfit", 0) < 1:
        return existing_shapes, RinkaMacroReport(False, "macro_gate", part_shape_counts=counts)
    retained = [shape for shape in existing_shapes if _keep_existing_detail(shape)]
    out = generated + retained
    out.sort(key=lambda shape: shape.z_index)
    return out, RinkaMacroReport(
        True,
        "accepted",
        generated_shapes=len(generated),
        retained_detail_shapes=len(retained),
        part_shape_counts=counts,
    )
