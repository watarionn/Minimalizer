from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from minimalizer_zerobase.analyzers.contracts import Evidence
from minimalizer_zerobase.scene.models import Region, Relation, Scene, Subject

@dataclass(frozen=True)
class FusionPolicy:
    overlap_threshold: float = 0.55
    default_confidence: float = 0.5
    subject_labels: tuple[str, ...] = ("person", "subject", "foreground")

    def __post_init__(self) -> None:
        if not 0.0 <= self.overlap_threshold <= 1.0:
            raise ValueError("overlap_threshold must be 0..1")

class EvidenceFusion:
    producer = "EvidenceFusion"
    producer_version = "1.0"

    def __init__(self, policy: FusionPolicy | None = None):
        self.policy = policy or FusionPolicy()

    def fuse(self, evidence: Iterable[Evidence]) -> Scene:
        records = tuple(sorted(evidence, key=lambda e: e.evidence_id))
        if not records:
            raise ValueError("at least one Evidence record is required")
        self._validate(records)
        groups = self._groups(records)
        regions = tuple(self._region(i, group) for i, group in enumerate(groups))
        subjects = self._subjects(regions)
        relations = self._relations(regions)
        provenance = {"evidence_ids": [e.evidence_id for e in records],
                      "policy": {"overlap_threshold": self.policy.overlap_threshold,
                                 "default_confidence": self.policy.default_confidence}}
        return Scene(records[0].coordinate_space, self.producer, self.producer_version,
                     subjects, regions, relations, provenance=provenance)

    def _validate(self, records: tuple[Evidence, ...]) -> None:
        ids = [e.evidence_id for e in records]
        if len(ids) != len(set(ids)):
            raise ValueError("evidence_id values must be unique")
        space = records[0].coordinate_space
        if any(e.coordinate_space != space for e in records[1:]):
            raise ValueError("all Evidence must share one coordinate space")

    def _groups(self, records: tuple[Evidence, ...]) -> list[list[Evidence]]:
        groups: list[list[Evidence]] = []
        for record in records:
            bbox = self._bbox(record)
            target = None
            best = -1.0
            for index, group in enumerate(groups):
                score = max((self._overlap(bbox, self._bbox(x)) for x in group), default=0.0)
                if score >= self.policy.overlap_threshold and score > best:
                    target, best = index, score
            if target is None: groups.append([record])
            else: groups[target].append(record)
        return groups

    def _region(self, index: int, group: list[Evidence]) -> Region:
        ordered = sorted(group, key=self._rank)
        winner = ordered[0]
        labels = [e.semantic_label for e in ordered if e.semantic_label]
        role = labels[0] if labels else "unclassified"
        confidence = max(self._confidence(e) for e in group)
        geometry = {"bbox": self._union_bbox([self._bbox(e) for e in group])}
        return Region(f"region-{index:04d}", role,
                      tuple(sorted(e.evidence_id for e in group)), 0.0, confidence, geometry)

    def _subjects(self, regions: tuple[Region, ...]) -> tuple[Subject, ...]:
        selected = [r for r in regions if r.semantic_role in self.policy.subject_labels]
        return tuple(Subject(f"subject-{i:04d}", r.semantic_role, (r.region_id,),
                             confidence=r.confidence) for i, r in enumerate(selected))

    def _relations(self, regions: tuple[Region, ...]) -> tuple[Relation, ...]:
        out = []
        for i, left in enumerate(regions):
            for right in regions[i + 1:]:
                score = self._overlap(left.geometry["bbox"], right.geometry["bbox"])
                if score > 0:
                    out.append(Relation(left.region_id, right.region_id, "overlaps", score))
        return tuple(out)

    def _rank(self, evidence: Evidence) -> tuple[float, str, str]:
        return (-self._confidence(evidence), evidence.provenance.producer, evidence.evidence_id)

    def _confidence(self, evidence: Evidence) -> float:
        return self.policy.default_confidence if evidence.confidence is None else evidence.confidence

    @staticmethod
    def _bbox(evidence: Evidence) -> list[float]:
        bbox = evidence.geometry.get("bbox")
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            raise ValueError(f"Evidence {evidence.evidence_id} requires geometry.bbox")
        return [float(v) for v in bbox]

    @staticmethod
    def _overlap(a: list[float], b: list[float]) -> float:
        ax, ay, aw, ah = a; bx, by, bw, bh = b
        ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
        iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
        inter = ix * iy
        smaller = min(max(0.0, aw * ah), max(0.0, bw * bh))
        return 0.0 if smaller == 0 else inter / smaller

    @staticmethod
    def _union_bbox(boxes: list[list[float]]) -> list[float]:
        x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
        x1 = max(b[0] + b[2] for b in boxes); y1 = max(b[1] + b[3] for b in boxes)
        return [x0, y0, x1 - x0, y1 - y0]
