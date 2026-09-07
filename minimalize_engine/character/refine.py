from __future__ import annotations

import cv2
import numpy as np

from ..models import Region
from .models import CharacterPartCandidate, CharacterStructure
from .part_types import CharacterPartType, PART_PRIORITY
from .heuristics import mask_overlap_ratio


def merge_duplicate_parts(
    parts: list[CharacterPartCandidate],
    *,
    overlap_threshold: float = 0.70,
) -> list[CharacterPartCandidate]:
    out: list[CharacterPartCandidate] = []
    for part in sorted(parts, key=lambda p: (p.confidence, p.area), reverse=True):
        duplicate = False
        for kept in out:
            if kept.part_type != part.part_type:
                continue
            a = mask_overlap_ratio(part.mask, kept.mask)
            b = mask_overlap_ratio(kept.mask, part.mask)
            if max(a, b) >= overlap_threshold:
                duplicate = True
                break
        if not duplicate:
            out.append(part)
    out.sort(key=lambda p: p.id)
    return out


def refine_head_face_hair(structure: CharacterStructure) -> CharacterStructure:
    face = structure.first_part(CharacterPartType.FACE)
    hair = structure.first_part(CharacterPartType.HAIR)
    head = structure.first_part(CharacterPartType.HEAD)

    if face is not None and hair is not None:
        # Hair should not own the central face mass.
        dilated_face = cv2.dilate(
            face.mask,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
        )
        hair.mask = cv2.bitwise_and(hair.mask, cv2.bitwise_not(dilated_face))
        hair.area = int(np.count_nonzero(hair.mask))
        if hair.area <= 0:
            hair.confidence *= 0.4

    if head is not None and face is not None:
        overlap = mask_overlap_ratio(face.mask, head.mask)
        if overlap < 0.70:
            face.confidence *= 0.80

    return structure


def refine_limb_parts(structure: CharacterStructure) -> CharacterStructure:
    torso = structure.first_part(CharacterPartType.TORSO)
    if torso is None:
        return structure

    for t in [
        CharacterPartType.LEFT_ARM,
        CharacterPartType.RIGHT_ARM,
        CharacterPartType.LEFT_LEG,
        CharacterPartType.RIGHT_LEG,
    ]:
        for part in structure.get_parts(t):
            if part.area_ratio < 0.0007:
                part.confidence *= 0.55
            # Keep a soft torso overlap. Completely detached masks are suspicious,
            # but poses with gloves/boots can legitimately have gaps.
            if mask_overlap_ratio(part.mask, torso.mask) == 0:
                part.metadata["detached_from_torso"] = True
    return structure


def refine_outfit_parts(structure: CharacterStructure) -> CharacterStructure:
    outfit = structure.first_part(CharacterPartType.OUTFIT)
    torso = structure.first_part(CharacterPartType.TORSO)
    if outfit is not None and torso is not None:
        overlap = mask_overlap_ratio(torso.mask, outfit.mask)
        outfit.confidence = max(outfit.confidence, min(0.78, 0.42 + overlap * 0.35))
    return structure


def protect_prop_parts(structure: CharacterStructure) -> CharacterStructure:
    for prop in structure.get_parts(CharacterPartType.PROP):
        prop.confidence = max(prop.confidence, 0.56)
        prop.metadata["protected"] = True
    return structure


def remove_implausible_parts(structure: CharacterStructure) -> CharacterStructure:
    keep = []
    for p in structure.parts:
        if p.part_type == CharacterPartType.SUBJECT:
            keep.append(p)
            continue
        if p.area <= 0:
            continue
        if p.confidence < 0.18:
            continue
        keep.append(p)
    structure.parts = keep
    return structure


def apply_character_part_hints(
    regions: list[Region],
    structure: CharacterStructure,
    *,
    importance_strength: float = 0.12,
) -> list[Region]:
    """
    Transfer part hypotheses back to regular Regions.

    The CharacterStructure stage can still feed the generic Shape generator. These hints make the
    existing selector reserve more attention for face/hair/torso/props before
    the dedicated Character Shape generator lands in later phases.
    """
    candidates = [
        p for p in structure.parts
        if p.part_type not in {CharacterPartType.SUBJECT, CharacterPartType.UNKNOWN}
    ]

    for region in regions:
        best = None
        best_overlap = 0.0
        rm = region.mask > 0
        denom = max(1, int(np.count_nonzero(rm)))

        for part in candidates:
            overlap = np.count_nonzero(rm & (part.mask > 0)) / denom
            weighted = overlap * part.confidence
            if weighted > best_overlap:
                best_overlap = weighted
                best = part

        if best is None or best_overlap < 0.10:
            continue

        region.character_part_hint = str(best.part_type)
        region.part_confidence = float(min(1.0, best_overlap))
        region.side_hint = best.side

        priority = PART_PRIORITY.get(best.part_type, 1.0)
        boost = importance_strength * max(0.0, priority - 0.65) * best.confidence
        region.importance_score = float(min(1.0, region.importance_score + boost))

    return regions


def refine_character_structure(
    structure: CharacterStructure,
    regions: list[Region],
    image_shape: tuple[int, ...],
) -> CharacterStructure:
    structure.parts = merge_duplicate_parts(structure.parts)
    refine_head_face_hair(structure)
    refine_limb_parts(structure)
    refine_outfit_parts(structure)
    protect_prop_parts(structure)
    remove_implausible_parts(structure)
    return structure
