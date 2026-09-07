from __future__ import annotations
from ..models import Region


def filter_regions(
    regions: list[Region],
    min_area_ratio: float,
    target_max_shapes: int,
    background_region_id: int | set[int] | None,
) -> list[Region]:
    if background_region_id is None:
        background_ids = set()
    elif isinstance(background_region_id, set):
        background_ids = background_region_id
    else:
        background_ids = {background_region_id}

    kept = []
    for r in regions:
        if r.id in background_ids:
            continue

        if r.role == "reflection":
            if r.is_accent or r.importance_score >= 0.72 or r.area_ratio >= min_area_ratio * 2.0:
                kept.append(r)
            continue

        if r.area_ratio >= min_area_ratio or r.is_accent or r.importance_score >= 0.58:
            kept.append(r)

    if len(kept) > target_max_shapes:
        accent_limit = min(12, max(4, target_max_shapes // 4))
        accents = sorted(
            (r for r in kept if r.is_accent or r.role == "vertical"),
            key=lambda r: (r.importance_score, r.area_ratio),
            reverse=True,
        )[:accent_limit]

        accent_ids = {r.id for r in accents}
        normal = [r for r in kept if r.id not in accent_ids]
        normal.sort(
            key=lambda r: (
                r.role == "structure",
                r.role == "boat",
                r.role == "water",
                r.area_ratio >= min_area_ratio * 4,
                r.importance_score,
                r.area_ratio,
            ),
            reverse=True,
        )
        room = max(0, target_max_shapes - len(accents))
        kept = accents + normal[:room]

    kept.sort(
        key=lambda r: (
            r.role == "structure",
            r.role == "boat",
            r.role == "water",
            r.area_ratio,
            r.importance_score,
        ),
        reverse=True,
    )
    return kept
