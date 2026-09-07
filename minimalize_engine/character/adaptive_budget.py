from __future__ import annotations

from dataclasses import dataclass, asdict

from .models import CharacterShapeBudget, CharacterStructure
from .part_types import CharacterPartType, PART_PRIORITY


@dataclass
class AdaptiveBudgetReport:
    enabled: bool
    total: int
    before: dict[str, int]
    after: dict[str, int]
    released_slots: int
    redistributed_slots: int
    reasons: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _present(structure: CharacterStructure, part_type: CharacterPartType) -> bool:
    return structure.first_part(part_type) is not None


def _face_minimum(structure: CharacterStructure) -> int:
    validation = structure.metadata.get("face_validation") or {}
    if not bool(validation.get("accepted", False)):
        return 0
    eye_count = int(validation.get("eye_count", 0) or 0)
    mouth = validation.get("mouth") is not None
    # Face Identity Budget can later omit weak cues, so reserve only the
    # amount that can plausibly carry identity rather than a fixed 3+ slots.
    if eye_count >= 2 and mouth:
        return 4
    if eye_count >= 1 or mouth:
        return 2
    return 1


def rebalance_character_budget(
    budget: CharacterShapeBudget,
    structure: CharacterStructure,
    *,
    enabled: bool = True,
) -> tuple[CharacterShapeBudget, AdaptiveBudgetReport]:
    before = dict(budget.per_part)
    before_str = {str(k): int(v) for k, v in before.items()}
    if not enabled or not before:
        return budget, AdaptiveBudgetReport(
            enabled=False,
            total=budget.total,
            before=before_str,
            after=before_str,
            released_slots=0,
            redistributed_slots=0,
            reasons=[],
        )

    minima: dict[CharacterPartType, int] = {}
    for t in before:
        if not _present(structure, t):
            minima[t] = 0
        elif t == CharacterPartType.FACE:
            minima[t] = _face_minimum(structure)
        elif t == CharacterPartType.HAIR:
            part = structure.first_part(t)
            ratio = 0.0 if part is None else part.area / max(1, structure.subject_mask.size)
            minima[t] = 4 if ratio >= 0.18 else 3 if ratio >= 0.10 else 2
        elif t == CharacterPartType.OUTFIT:
            part = structure.first_part(t)
            ratio = 0.0 if part is None else part.area / max(1, structure.subject_mask.size)
            # Outfit is a major identity carrier. Adaptive budgeting may trim
            # over-reserved micro-details, but it must not collapse sleeves /
            # lower garment into a single torso symbol.
            desired = 5 if ratio >= 0.20 else 4 if ratio >= 0.08 else 3
            minima[t] = min(before.get(t, desired), desired)
        elif t == CharacterPartType.PROP:
            props = structure.get_parts(CharacterPartType.PROP)
            minima[t] = min(before.get(t, 0), min(2, max(1, len(props)))) if props else 0
        elif t in {
            CharacterPartType.TORSO,
            CharacterPartType.LEFT_ARM,
            CharacterPartType.RIGHT_ARM,
            CharacterPartType.LEFT_LEG,
            CharacterPartType.RIGHT_LEG,
        }:
            minima[t] = 1
        else:
            minima[t] = 1

    # Start from useful minima, then spend remaining slots according to
    # identity value rather than preserving legacy fixed reservations.
    after = {t: min(before.get(t, 0), max(0, minima.get(t, 0))) for t in before}
    used = sum(after.values())
    # Character details should not monopolize the entire global Shape budget.
    # Keep roughly 72% for dedicated parts and deliberately return the rest
    # to generic regions, which preserve costume panels / accents that the
    # semantic primitives do not own.
    detail_target = min(budget.total, max(used, int(round(budget.total * 0.80))))
    remaining = max(0, detail_target - used)

    importance_bonus = {
        CharacterPartType.FACE: 1.40,
        CharacterPartType.HAIR: 1.25,
        CharacterPartType.OUTFIT: 1.18,
        CharacterPartType.PROP: 1.28,
        CharacterPartType.TORSO: 1.12,
        CharacterPartType.LEFT_ARM: 1.02,
        CharacterPartType.RIGHT_ARM: 1.02,
        CharacterPartType.LEFT_LEG: 1.00,
        CharacterPartType.RIGHT_LEG: 1.00,
    }

    # Cap at the original dynamic allocation for most parts. Face can use the
    # identity-derived minimum even when the old allocation was lower.
    caps = {
        t: max(after[t], before.get(t, 0))
        for t in after
    }
    # Outfit and props are often the remaining identity carriers after face
    # simplification, so allow one extra slot when there is spare global budget.
    if CharacterPartType.OUTFIT in caps and _present(structure, CharacterPartType.OUTFIT):
        caps[CharacterPartType.OUTFIT] = min(caps[CharacterPartType.OUTFIT], before.get(CharacterPartType.OUTFIT, caps[CharacterPartType.OUTFIT]))
    if CharacterPartType.PROP in caps and _present(structure, CharacterPartType.PROP):
        caps[CharacterPartType.PROP] = min(caps[CharacterPartType.PROP], 3)

    while remaining > 0:
        candidates = [t for t in after if after[t] < caps[t]]
        if not candidates:
            break
        t = max(
            candidates,
            key=lambda x: (
                PART_PRIORITY.get(x, 1.0) * importance_bonus.get(x, 1.0),
                minima.get(x, 0),
                -after[x],
            ),
        )
        after[t] += 1
        remaining -= 1

    # Any still-unused budget is intentionally released to generic region
    # selection instead of being forced into character detail shapes.
    released = max(0, budget.total - sum(after.values()))
    redistributed = max(0, sum(max(0, after[t] - min(before.get(t, 0), minima.get(t, 0))) for t in after))

    # Preserve the historical invariant that per_part sums to total while
    # explicitly parking released capacity in UNKNOWN. Dedicated primitive
    # builders never consume this bucket, so it effectively returns those
    # slots to generic-region composition without breaking callers that
    # validate the budget total.
    if released > 0:
        after[CharacterPartType.UNKNOWN] = after.get(CharacterPartType.UNKNOWN, 0) + released

    budget.per_part = after
    budget.reserved_face = after.get(CharacterPartType.FACE, 0)
    budget.reserved_hair = after.get(CharacterPartType.HAIR, 0)
    budget.reserved_props = after.get(CharacterPartType.PROP, 0)
    budget.reserved_outfit = after.get(CharacterPartType.OUTFIT, 0)
    body_types = {
        CharacterPartType.TORSO,
        CharacterPartType.LEFT_ARM,
        CharacterPartType.RIGHT_ARM,
        CharacterPartType.LEFT_LEG,
        CharacterPartType.RIGHT_LEG,
    }
    budget.reserved_body = sum(1 for t in body_types if after.get(t, 0) > 0)
    for part in structure.parts:
        part.shape_budget = after.get(part.part_type, 0)

    reasons = []
    if budget.reserved_face < before.get(CharacterPartType.FACE, 0):
        reasons.append("released_face_overreservation")
    if budget.reserved_outfit > before.get(CharacterPartType.OUTFIT, 0):
        reasons.append("reinvested_in_outfit_identity")
    if budget.reserved_props > before.get(CharacterPartType.PROP, 0):
        reasons.append("reinvested_in_prop_identity")
    if released > 0:
        reasons.append("released_to_generic_regions")

    report = AdaptiveBudgetReport(
        enabled=True,
        total=budget.total,
        before=before_str,
        after={str(k): int(v) for k, v in after.items()},
        released_slots=int(released),
        redistributed_slots=int(redistributed),
        reasons=reasons,
    )
    budget.metadata = dict(budget.metadata)
    budget.metadata["adaptive"] = report.to_dict()
    return budget, report
