from __future__ import annotations

from dataclasses import dataclass
from ..models import Region
from .skeleton import CompositionSkeleton, region_side


LAYER_ORDER = {
    "water_base": 5,
    "skyline_base": 10,
    "subject_base": 15,
    "skyline": 20,
    "midground": 30,
    "character_body_base": 27,
    "character_body_detail": 29,
    "character_outfit_base": 31,
    "character_hair_base": 32,
    "character_outfit_detail": 33,
    "character_prop_base": 36,
    "character_face_base": 34,
    "character_hair_detail": 38,
    "water": 40,
    "foreground": 40,
    "accents": 50,
    "character_outfit_accessory": 52,
    "character_prop_detail": 54,
    "character_face_detail": 55,
    "lines": 60,
}


@dataclass(frozen=True)
class LayerBudget:
    skyline: int
    midground: int
    water: int
    foreground: int
    accents: int


def assign_composition_layers(regions: list[Region], image_shape) -> list[Region]:
    h, w = image_shape[:2]
    for r in regions:
        _, _, bw, bh = r.bbox
        cx, cy = r.centroid
        yr = cy / max(h, 1)

        if r.semantic_type.startswith("subject"):
            r.composition_layer = "midground"
        elif r.role in {"accent", "vertical"}:
            r.composition_layer = "accents"
        elif r.role in {"water", "reflection"}:
            r.composition_layer = "water"
        elif r.role == "boat":
            r.composition_layer = "foreground"
        elif r.role == "structure":
            r.composition_layer = "skyline" if yr < 0.57 else "midground"
        else:
            if yr < 0.48:
                r.composition_layer = "skyline"
            elif yr > 0.68:
                r.composition_layer = "foreground"
            else:
                r.composition_layer = "midground"
    return regions


def make_layer_budget(
    target_count: int,
    *,
    skyline_ratio: float,
    midground_ratio: float,
    water_ratio: float,
    foreground_ratio: float,
    accent_ratio: float,
) -> LayerBudget:
    target_count = max(5, int(target_count))
    ratios = {
        "skyline": max(0.0, skyline_ratio),
        "midground": max(0.0, midground_ratio),
        "water": max(0.0, water_ratio),
        "foreground": max(0.0, foreground_ratio),
        "accents": max(0.0, accent_ratio),
    }
    total = sum(ratios.values()) or 1.0
    raw = {k: target_count * v / total for k, v in ratios.items()}
    counts = {k: max(1, int(v)) for k, v in raw.items()}

    # Adjust exactly to target, favoring midground / skyline when adding slots.
    add_order = ["midground", "skyline", "foreground", "accents", "water"]
    remove_order = ["accents", "water", "foreground", "midground", "skyline"]
    while sum(counts.values()) < target_count:
        for k in add_order:
            if sum(counts.values()) >= target_count:
                break
            counts[k] += 1
    while sum(counts.values()) > target_count:
        changed = False
        for k in remove_order:
            if sum(counts.values()) <= target_count:
                break
            if counts[k] > 1:
                counts[k] -= 1
                changed = True
        if not changed:
            break

    return LayerBudget(**counts)


def _rank_layer_items(layer: str, items: list[Region]) -> list[Region]:
    if layer == "accents":
        items.sort(
            key=lambda r: (
                r.is_accent,
                r.role == "vertical",
                r.importance_score,
                r.area_ratio,
            ),
            reverse=True,
        )
    elif layer == "water":
        items.sort(
            key=lambda r: (
                r.role == "water",
                r.area_ratio,
                r.importance_score,
            ),
            reverse=True,
        )
    else:
        items.sort(
            key=lambda r: (
                r.area_ratio >= 0.006,
                r.importance_score,
                r.area_ratio,
            ),
            reverse=True,
        )
    return items


def _balanced_side_take(
    items: list[Region],
    limit: int,
    skeleton: CompositionSkeleton,
) -> list[Region]:
    """
    Reserve composition capacity for both side masses.

    The center corridor can still contain bridge/boat/accent detail, but it
    should not consume most skyline/midground slots when a clear negative-space
    valley has been detected.
    """
    if limit <= 0 or not skeleton.active:
        return items[:limit]

    left = [r for r in items if region_side(r, skeleton) == "left"]
    right = [r for r in items if region_side(r, skeleton) == "right"]
    center = [r for r in items if region_side(r, skeleton) == "center"]

    side_quota = max(1, int(round(limit * 0.40)))
    center_quota = max(0, limit - side_quota * 2)

    chosen = left[:side_quota] + right[:side_quota] + center[:center_quota]
    chosen_ids = {id(r) for r in chosen}

    if len(chosen) < limit:
        leftovers = [r for r in items if id(r) not in chosen_ids]
        chosen.extend(leftovers[:limit - len(chosen)])

    return chosen[:limit]


def _rank_layer_items(layer: str, items: list[Region]) -> list[Region]:
    if layer == "accents":
        items.sort(key=lambda r:(r.is_accent,r.role=="vertical",r.importance_score,r.area_ratio),reverse=True)
    elif layer == "water":
        items.sort(key=lambda r:(r.role=="water",r.area_ratio,r.importance_score),reverse=True)
    else:
        items.sort(key=lambda r:(r.area_ratio>=0.006,r.importance_score,r.area_ratio),reverse=True)
    return items

def _balanced_side_take(items,limit,skeleton):
    if limit<=0 or not skeleton.active:return items[:limit]
    left=[r for r in items if region_side(r,skeleton)=="left"];right=[r for r in items if region_side(r,skeleton)=="right"];center=[r for r in items if region_side(r,skeleton)=="center"]
    q=max(1,int(round(limit*.4)));cq=max(0,limit-q*2);chosen=left[:q]+right[:q]+center[:cq];ids={id(r) for r in chosen}
    if len(chosen)<limit:chosen += [r for r in items if id(r) not in ids][:limit-len(chosen)]
    return chosen[:limit]

def select_regions_by_layer(regions,budget,skeleton=None,*,balance_sides=True):
    by={k:[] for k in ["skyline","midground","water","foreground","accents"]}
    for r in regions:by.setdefault(r.composition_layer,[]).append(r)
    limits={"skyline":budget.skyline,"midground":budget.midground,"water":budget.water,"foreground":budget.foreground,"accents":budget.accents}
    selected=[]
    for layer,items in by.items():
        if layer not in limits:continue
        items=_rank_layer_items(layer,items);limit=limits[layer]
        picked=_balanced_side_take(items,limit,skeleton) if balance_sides and skeleton is not None and skeleton.active and layer in {"skyline","midground"} else items[:limit]
        selected.extend(picked)
    target=sum(limits.values())
    if len(selected)<target:
        ids={id(r) for r in selected}; leftovers=[r for r in regions if id(r) not in ids]
        current=sum(1 for r in selected if r.composition_layer=="accents"); cap=limits["accents"]+2
        non=[r for r in leftovers if r.composition_layer!="accents"];acc=[r for r in leftovers if r.composition_layer=="accents"]
        key=lambda r:(r.semantic_type in {"subject_mass","subject_organic","organic","building","boat"},r.importance_score,r.multiscale_score,r.area_ratio)
        non.sort(key=key,reverse=True);acc.sort(key=key,reverse=True)
        need=target-len(selected);selected.extend(non[:need]);need=target-len(selected)
        if need>0 and current<cap:selected.extend(acc[:min(need,cap-current)])
    selected.sort(key=lambda r:(LAYER_ORDER.get(r.composition_layer,30),-r.area_ratio,-r.importance_score))
    return selected


def count_layers(regions: list[Region]) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in regions:
        out[r.composition_layer] = out.get(r.composition_layer, 0) + 1
    return out
