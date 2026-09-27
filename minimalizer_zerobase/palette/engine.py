from __future__ import annotations
from dataclasses import dataclass, replace
from math import sqrt
from typing import Iterable
from minimalizer_zerobase.scene.models import Region, Scene

RGB = tuple[int, int, int]

def _rgb(value: Iterable[int]) -> RGB:
    out = tuple(int(x) for x in value)
    if len(out) != 3 or any(x < 0 or x > 255 for x in out):
        raise ValueError("RGB colors must contain three values in 0..255")
    return out  # type: ignore[return-value]

def _hex(color: RGB) -> str:
    return "#" + "".join(f"{x:02x}" for x in color)

def _distance(a: RGB, b: RGB) -> float:
    return sqrt(sum((x-y) ** 2 for x, y in zip(a, b)))

@dataclass(frozen=True)
class MaterialEvidence:
    region_id: str
    base_color: RGB
    illumination_colors: tuple[RGB, ...] = ()
    confidence: float = 1.0
    source: str = "canonical"

    def __post_init__(self):
        object.__setattr__(self, "base_color", _rgb(self.base_color))
        object.__setattr__(self, "illumination_colors", tuple(_rgb(c) for c in self.illumination_colors))
        if not 0 <= self.confidence <= 1:
            raise ValueError("material confidence must be in 0..1")

@dataclass(frozen=True)
class PalettePolicy:
    merge_distance: float = 36.0
    preserve_merge_distance: float = 24.0
    protect_merge_distance: float = 12.0
    max_colors: int = 8
    illumination_disposable: bool = True

    def __post_init__(self):
        if min(self.merge_distance, self.preserve_merge_distance, self.protect_merge_distance) < 0:
            raise ValueError("merge distances must be non-negative")
        if self.max_colors < 1:
            raise ValueError("max_colors must be positive")

@dataclass(frozen=True)
class MaterialAssignment:
    region_id: str
    base_color: str
    palette_color: str
    illumination_colors: tuple[str, ...]
    illumination_disposable: bool
    confidence: float
    importance_tier: str

class PaletteMaterialEngine:
    producer = "PaletteMaterialEngine"
    producer_version = "1.0"

    def __init__(self, policy: PalettePolicy | None = None):
        self.policy = policy or PalettePolicy()

    def assign(self, scene: Scene, evidence: Iterable[MaterialEvidence]) -> tuple[MaterialAssignment, ...]:
        items = sorted(evidence, key=lambda x: x.region_id)
        region_ids = {r.region_id for r in scene.regions}
        if len({x.region_id for x in items}) != len(items):
            raise ValueError("duplicate material evidence region_id")
        if any(x.region_id not in region_ids for x in items):
            raise ValueError("material evidence references unknown region")
        tiers = self._importance_tiers(scene)
        representatives: list[RGB] = []
        assignments = []
        for item in sorted(items, key=lambda x: (-self._tier_rank(tiers.get(x.region_id, "disposable")), x.region_id)):
            tier = tiers.get(item.region_id, "disposable")
            threshold = self._threshold(tier)
            nearest = min(representatives, key=lambda c: (_distance(item.base_color, c), c), default=None)
            selected = nearest if nearest is not None and _distance(item.base_color, nearest) <= threshold else item.base_color
            if selected == item.base_color and selected not in representatives:
                representatives.append(selected)
            assignments.append(MaterialAssignment(item.region_id, _hex(item.base_color), _hex(selected),
                tuple(_hex(c) for c in item.illumination_colors), self.policy.illumination_disposable,
                item.confidence, tier))

        if len(representatives) > self.policy.max_colors:
            assignments = self._cap(assignments, representatives, tiers)
        return tuple(sorted(assignments, key=lambda x: x.region_id))

    def apply(self, scene: Scene, evidence: Iterable[MaterialEvidence]) -> Scene:
        assignments = self.assign(scene, evidence)
        palette = tuple(sorted({x.palette_color for x in assignments}))
        provenance = dict(scene.provenance)
        provenance["palette_material"] = {
            "producer": self.producer, "producer_version": self.producer_version,
            "policy": {"merge_distance": self.policy.merge_distance,
                "preserve_merge_distance": self.policy.preserve_merge_distance,
                "protect_merge_distance": self.policy.protect_merge_distance,
                "max_colors": self.policy.max_colors,
                "illumination_disposable": self.policy.illumination_disposable},
            "assignments": [x.__dict__ for x in assignments],
        }
        return replace(scene, producer=self.producer, producer_version=self.producer_version,
                       palette=palette, provenance=provenance)

    def _importance_tiers(self, scene: Scene) -> dict[str, str]:
        data = scene.provenance.get("importance", {}).get("decisions", [])
        return {x["region_id"]: x["tier"] for x in data if "region_id" in x and "tier" in x}

    @staticmethod
    def _tier_rank(tier: str) -> int:
        return {"protect": 2, "preserve": 1}.get(tier, 0)

    def _threshold(self, tier: str) -> float:
        return {"protect": self.policy.protect_merge_distance,
                "preserve": self.policy.preserve_merge_distance}.get(tier, self.policy.merge_distance)

    def _cap(self, assignments, representatives, tiers):
        protected = [a for a in assignments if a.importance_tier == "protect"]
        keep = [_rgb(bytes.fromhex(a.palette_color[1:])) for a in protected]
        for color in representatives:
            if color not in keep and len(keep) < self.policy.max_colors:
                keep.append(color)
        if not keep:
            keep = representatives[:self.policy.max_colors]
        return [replace(a, palette_color=_hex(min(keep, key=lambda c: (_distance(_rgb(bytes.fromhex(a.base_color[1:])), c), c))))
                for a in assignments]
