from __future__ import annotations

from dataclasses import dataclass

from .ir import AbstractionPlan, AbstractionPolicy, SemanticPart


_LIMB_IDS = {"left_arm", "right_arm", "lower_body"}
_LIMB_CATEGORIES = {"arm", "hand", "leg", "foot"}


@dataclass(frozen=True)
class AnatomyGuardResult:
    passed: bool
    missing_parts: tuple[str, ...]
    suppressed_parts: tuple[str, ...]
    missing_topology: tuple[str, ...]
    extreme_bbox_change: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "pass": self.passed,
            "missing_parts": list(self.missing_parts),
            "suppressed_parts": list(self.suppressed_parts),
            "missing_topology": list(self.missing_topology),
            "extreme_bbox_change": list(self.extreme_bbox_change),
        }


def _bbox_area(part: SemanticPart) -> float | None:
    if part.bbox is None:
        return None
    x0, y0, x1, y1 = part.bbox
    return max(x1 - x0, 0.0) * max(y1 - y0, 0.0)


def _is_anatomy_part(part: SemanticPart) -> bool:
    return (
        part.id in {"head", "torso", *_LIMB_IDS}
        or part.category in {"head", "torso", *_LIMB_CATEGORIES}
    )


def _is_limb(part: SemanticPart) -> bool:
    return part.id in _LIMB_IDS or part.category in _LIMB_CATEGORIES


def anatomy_integrity_gate(
    baseline: AbstractionPlan,
    candidate: AbstractionPlan,
    *,
    minimum_bbox_area_ratio: float = 0.35,
    maximum_bbox_area_ratio: float = 2.8,
) -> AnatomyGuardResult:
    baseline_by_id = {part.id: part for part in baseline.parts}
    candidate_by_id = {part.id: part for part in candidate.parts}

    required_ids = sorted(
        part.id for part in baseline.parts if _is_anatomy_part(part)
    )
    missing = tuple(
        part_id for part_id in required_ids if part_id not in candidate_by_id
    )
    suppressed = tuple(
        part_id
        for part_id in required_ids
        if part_id in candidate_by_id
        and candidate_by_id[part_id].abstraction_policy is AbstractionPolicy.SUPPRESS
    )

    missing_topology: list[str] = []
    for part_id in required_ids:
        before = baseline_by_id[part_id]
        after = candidate_by_id.get(part_id)
        if after is None:
            continue
        after_constraints = {
            (item.relation, item.target_part_id)
            for item in after.topology_constraints
            if item.required
        }
        for item in before.topology_constraints:
            if not item.required:
                continue
            key = (item.relation, item.target_part_id)
            if key not in after_constraints:
                missing_topology.append(
                    f"{part_id}:{item.relation}:{item.target_part_id}"
                )

    extreme: list[str] = []
    for part_id in required_ids:
        before = baseline_by_id[part_id]
        after = candidate_by_id.get(part_id)
        if after is None or not _is_limb(before):
            continue
        before_area = _bbox_area(before)
        after_area = _bbox_area(after)
        if before_area is None or after_area is None or before_area <= 0.0:
            continue
        ratio = after_area / before_area
        if ratio < minimum_bbox_area_ratio or ratio > maximum_bbox_area_ratio:
            extreme.append(part_id)

    failures = bool(missing or suppressed or missing_topology or extreme)
    return AnatomyGuardResult(
        passed=not failures,
        missing_parts=missing,
        suppressed_parts=suppressed,
        missing_topology=tuple(sorted(missing_topology)),
        extreme_bbox_change=tuple(sorted(extreme)),
    )


def anatomy_safe_or_fallback(
    baseline: AbstractionPlan,
    candidate: AbstractionPlan,
) -> AbstractionPlan:
    result = anatomy_integrity_gate(baseline, candidate)
    return candidate if result.passed else baseline
