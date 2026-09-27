from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Mapping
from minimalizer_zerobase.scene.models import Region, Scene, Subject

@dataclass(frozen=True)
class ImportancePolicy:
    semantic_weights: Mapping[str, float] | None = None
    identity_roles: tuple[str, ...] = ("accessory", "identity_accent", "logo", "prop")
    semantic_weight: float = 0.30
    subject_weight: float = 0.20
    spatial_mass_weight: float = 0.20
    confidence_weight: float = 0.10
    identity_accent_weight: float = 0.20
    preserve_threshold: float = 0.55
    protect_threshold: float = 0.75

    def __post_init__(self) -> None:
        weights = (self.semantic_weight, self.subject_weight, self.spatial_mass_weight,
                   self.confidence_weight, self.identity_accent_weight)
        if any(w < 0 for w in weights) or sum(weights) <= 0:
            raise ValueError("importance weights must be non-negative with positive total")
        if not 0 <= self.preserve_threshold <= self.protect_threshold <= 1:
            raise ValueError("thresholds must satisfy 0 <= preserve <= protect <= 1")

@dataclass(frozen=True)
class ImportanceDecision:
    region_id: str
    semantic: float
    subject: float
    spatial_mass: float
    confidence: float
    identity_accent: float
    score: float
    tier: str
    rationale: tuple[str, ...]

class ImportanceEngine:
    producer = "ImportanceEngine"
    producer_version = "1.0"
    DEFAULT_SEMANTIC = {
        "person": 1.0, "face": 1.0, "skin": .9, "hair": .9,
        "shirt": .8, "coat": .8, "dress": .8, "pants": .7,
        "arm": .75, "hand": .7, "leg": .7, "shoe": .6,
        "accessory": .8, "identity_accent": 1.0, "prop": .75,
        "background": .1, "noise": 0.0,
    }

    def __init__(self, policy: ImportancePolicy | None = None):
        self.policy = policy or ImportancePolicy()

    def evaluate(self, scene: Scene) -> tuple[ImportanceDecision, ...]:
        subject_regions = {rid for s in scene.subjects for rid in s.region_ids}
        canvas_area = float(scene.coordinate_space.width * scene.coordinate_space.height)
        decisions = [self._decision(r, subject_regions, canvas_area) for r in scene.regions]
        return tuple(sorted(decisions, key=lambda d: (-d.score, d.region_id)))

    def apply(self, scene: Scene) -> Scene:
        decisions = self.evaluate(scene)
        by_id = {d.region_id: d for d in decisions}
        regions = tuple(replace(r, importance=by_id[r.region_id].score) for r in scene.regions)
        subject_scores = {s.subject_id: max((by_id[r].score for r in s.region_ids if r in by_id),
                                            default=0.0) for s in scene.subjects}
        subjects = tuple(replace(s, importance=subject_scores[s.subject_id]) for s in scene.subjects)
        provenance = dict(scene.provenance)
        provenance["importance"] = {
            "producer": self.producer, "producer_version": self.producer_version,
            "policy": self._policy_record(),
            "decisions": [self._record(d) for d in decisions],
        }
        return replace(scene, producer=self.producer, producer_version=self.producer_version,
                       regions=regions, subjects=subjects, provenance=provenance)

    def _decision(self, region: Region, subject_regions: set[str], canvas_area: float):
        semantic = self._semantic(region.semantic_role)
        subject = 1.0 if region.region_id in subject_regions else 0.0
        box = region.geometry.get("bbox")
        area = 0.0 if not isinstance(box, (list, tuple)) or len(box) != 4 else max(0.0, float(box[2]) * float(box[3]))
        spatial = min(1.0, area / canvas_area * 4.0) if canvas_area else 0.0
        confidence = min(1.0, max(0.0, float(region.confidence)))
        accent = 1.0 if region.semantic_role.lower() in {x.lower() for x in self.policy.identity_roles} else 0.0
        dims = (semantic, subject, spatial, confidence, accent)
        weights = (self.policy.semantic_weight, self.policy.subject_weight,
                   self.policy.spatial_mass_weight, self.policy.confidence_weight,
                   self.policy.identity_accent_weight)
        score = round(sum(v*w for v, w in zip(dims, weights)) / sum(weights), 6)
        tier = "protect" if score >= self.policy.protect_threshold else ("preserve" if score >= self.policy.preserve_threshold else "disposable")
        rationale = tuple(name for name, value in zip(("semantic", "subject", "spatial_mass", "confidence", "identity_accent"), dims) if value >= .75)
        return ImportanceDecision(region.region_id, *dims, score, tier, rationale)

    def _semantic(self, role: str) -> float:
        table = dict(self.DEFAULT_SEMANTIC)
        if self.policy.semantic_weights:
            table.update({str(k).lower(): float(v) for k, v in self.policy.semantic_weights.items()})
        return min(1.0, max(0.0, table.get(role.lower(), .5)))

    def _policy_record(self):
        return {
            "semantic_weights": dict(sorted((self.policy.semantic_weights or {}).items())),
            "identity_roles": sorted(self.policy.identity_roles),
            "weights": {
                "semantic": self.policy.semantic_weight, "subject": self.policy.subject_weight,
                "spatial_mass": self.policy.spatial_mass_weight, "confidence": self.policy.confidence_weight,
                "identity_accent": self.policy.identity_accent_weight,
            },
            "preserve_threshold": self.policy.preserve_threshold,
            "protect_threshold": self.policy.protect_threshold,
        }

    @staticmethod
    def _record(d: ImportanceDecision):
        return {
            "region_id": d.region_id,
            "dimensions": {"semantic": d.semantic, "subject": d.subject,
                           "spatial_mass": d.spatial_mass, "confidence": d.confidence,
                           "identity_accent": d.identity_accent},
            "score": d.score, "tier": d.tier, "rationale": list(d.rationale),
        }
