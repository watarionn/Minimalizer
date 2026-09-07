from __future__ import annotations

from .models import CharacterShapeBudget, CharacterStructure, CharacterPartCandidate
from .part_types import (
    CharacterPartType,
    CharacterPreset,
    PART_DEFAULT_BUDGET,
    PART_PRIORITY,
)


def infer_character_preset(
    structure: CharacterStructure,
    image_shape: tuple[int, ...],
) -> CharacterPreset:
    if structure.preset != "auto":
        return structure.preset  # type: ignore[return-value]

    h, w = image_shape[:2]
    x, y, bw, bh = structure.subject_bbox
    aspect = bh / max(1.0, bw)
    coverage = bh / max(1.0, h)

    if aspect >= 1.75 and coverage >= 0.68:
        return "full_body"
    if aspect >= 1.20 and coverage >= 0.52:
        return "upper_body"
    if aspect <= 1.16:
        return "portrait"
    return "upper_body"


def get_part_complexity_score(part: CharacterPartCandidate) -> float:
    _, _, w, h = part.bbox
    aspect = max(w, h) / max(1.0, min(w, h))
    fill = part.area / max(1.0, w * h)
    irregularity = max(0.0, 1.0 - min(1.0, fill))
    return float(min(1.0, 0.45 * irregularity + 0.25 * min(aspect / 4.0, 1.0) + 0.30 * part.confidence))


def allocate_budget_by_priority(
    parts: list[CharacterPartCandidate],
    total_shapes: int,
    priorities: dict[CharacterPartType, float],
) -> dict[CharacterPartType, int]:
    present_types = []
    for p in parts:
        if p.part_type in {
            CharacterPartType.SUBJECT,
            CharacterPartType.HEAD,
            CharacterPartType.UNKNOWN,
        }:
            continue
        if p.part_type not in present_types:
            present_types.append(p.part_type)

    if not present_types or total_shapes <= 0:
        return {}

    weights = {}
    for t in present_types:
        candidates = [p for p in parts if p.part_type == t]
        complexity = max((get_part_complexity_score(p) for p in candidates), default=0.5)
        weights[t] = max(0.1, priorities.get(t, 1.0) * (0.75 + complexity * 0.50))

    total_weight = sum(weights.values())
    raw = {t: total_shapes * weights[t] / total_weight for t in present_types}
    allocated = {t: max(1, int(v)) for t, v in raw.items()}

    # Distribute remainder by fractional component / priority.
    while sum(allocated.values()) < total_shapes:
        t = max(
            present_types,
            key=lambda x: (raw[x] - int(raw[x]), priorities.get(x, 1.0)),
        )
        allocated[t] += 1
        raw[t] = float(int(raw[t]))

    while sum(allocated.values()) > total_shapes:
        candidates = [t for t in present_types if allocated[t] > 1]
        if not candidates:
            break
        t = min(candidates, key=lambda x: priorities.get(x, 1.0))
        allocated[t] -= 1

    return allocated


def reserve_critical_part_budget(
    budget: dict[CharacterPartType, int],
    total_shapes: int | None = None,
) -> dict[CharacterPartType, int]:
    minimums = {
        CharacterPartType.FACE: 3,
        CharacterPartType.HAIR: 3,
        CharacterPartType.TORSO: 2,
        CharacterPartType.OUTFIT: 4,
        CharacterPartType.PROP: 1,
    }
    for t, minimum in minimums.items():
        if t in budget:
            budget[t] = max(budget[t], minimum)

    if total_shapes is not None:
        while sum(budget.values()) > total_shapes:
            reducible = [
                t for t, n in budget.items()
                if n > minimums.get(t, 1)
            ]
            if not reducible:
                break
            t = min(reducible, key=lambda x: PART_PRIORITY.get(x, 1.0))
            budget[t] -= 1
    return budget


def make_character_shape_budget(
    structure: CharacterStructure,
    total_shapes: int,
    *,
    preset: CharacterPreset = "auto",
) -> CharacterShapeBudget:
    preset = infer_character_preset(structure, structure.subject_mask.shape)
    base = allocate_budget_by_priority(structure.parts, total_shapes, PART_PRIORITY)

    # Blend dynamic allocation with known-good default intent.
    for t, default in PART_DEFAULT_BUDGET.items():
        if t in base:
            if preset == "portrait" and t in {CharacterPartType.FACE, CharacterPartType.HAIR}:
                base[t] = max(base[t], default + 2)
            elif preset == "full_body" and t in {
                CharacterPartType.LEFT_LEG,
                CharacterPartType.RIGHT_LEG,
            }:
                base[t] = max(base[t], default)

    if CharacterPartType.OUTFIT in base:
        if preset == "full_body":
            base[CharacterPartType.OUTFIT] = max(base[CharacterPartType.OUTFIT], 6)
        elif preset == "upper_body":
            base[CharacterPartType.OUTFIT] = max(base[CharacterPartType.OUTFIT], 4)
        elif preset == "portrait":
            base[CharacterPartType.OUTFIT] = max(base[CharacterPartType.OUTFIT], 3)

    base = reserve_critical_part_budget(base, total_shapes)

    # If minimum reservations caused a deficit, add leftover to face/hair/torso.
    while sum(base.values()) < total_shapes and base:
        order = [
            CharacterPartType.FACE,
            CharacterPartType.HAIR,
            CharacterPartType.TORSO,
            CharacterPartType.PROP,
        ]
        target = next((t for t in order if t in base), max(base, key=base.get))
        base[target] += 1

    for part in structure.parts:
        part.shape_budget = base.get(part.part_type, 0)

    body_types = [
        CharacterPartType.TORSO,
        CharacterPartType.LEFT_ARM,
        CharacterPartType.RIGHT_ARM,
        CharacterPartType.LEFT_LEG,
        CharacterPartType.RIGHT_LEG,
    ]
    reserved_body = sum(
        1
        for t in body_types
        if structure.first_part(t) is not None and base.get(t, 0) > 0
    )

    return CharacterShapeBudget(
        total=total_shapes,
        per_part=base,
        reserved_face=base.get(CharacterPartType.FACE, 0),
        reserved_hair=base.get(CharacterPartType.HAIR, 0),
        reserved_props=base.get(CharacterPartType.PROP, 0),
        reserved_outfit=base.get(CharacterPartType.OUTFIT, 0),
        reserved_body=reserved_body,
        metadata={"preset": str(preset)},
    )
