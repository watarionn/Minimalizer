from __future__ import annotations
from dataclasses import dataclass
from minimalizer_zerobase.scene.models import Region, Relation, Scene, Subject

@dataclass(frozen=True)
class ReconstructionPolicy:
    merge_overlap_threshold: float = 0.75
    split_components: bool = True
    clip_to_canvas: bool = True

    def __post_init__(self) -> None:
        if not 0.0 <= self.merge_overlap_threshold <= 1.0:
            raise ValueError("merge_overlap_threshold must be 0..1")

class RegionReconstructor:
    producer = "RegionReconstructor"
    producer_version = "1.0"

    def __init__(self, policy: ReconstructionPolicy | None = None):
        self.policy = policy or ReconstructionPolicy()

    def reconstruct(self, scene: Scene) -> Scene:
        staged: list[tuple[Region, tuple[str, ...]]] = []
        for source in sorted(scene.regions, key=lambda r: r.region_id):
            staged.extend(self._normalize(source, scene.coordinate_space.width,
                                          scene.coordinate_space.height))
        merged = self._merge(staged)
        regions, remap = self._finalize(merged)
        subjects = self._subjects(scene.subjects, remap)
        relations = self._relations(regions)
        provenance = dict(scene.provenance)
        provenance["region_reconstruction"] = {
            "producer": self.producer, "producer_version": self.producer_version,
            "source_region_ids": sorted(r.region_id for r in scene.regions),
            "merge_overlap_threshold": self.policy.merge_overlap_threshold,
            "split_components": self.policy.split_components,
            "clip_to_canvas": self.policy.clip_to_canvas,
        }
        return Scene(scene.coordinate_space, self.producer, self.producer_version,
                     subjects, regions, relations, scene.palette, provenance, scene.schema_version)

    def _normalize(self, source: Region, width: int, height: int):
        raw = source.geometry.get("components") if self.policy.split_components else None
        boxes = raw if isinstance(raw, (list, tuple)) and raw else [source.geometry.get("bbox")]
        normalized = []
        for box in boxes:
            clipped = self._clip(box, width, height)
            if clipped is None:
                continue
            geometry = {k: v for k, v in source.geometry.items() if k != "components"}
            geometry["bbox"] = clipped
            normalized.append((Region(source.region_id, source.semantic_role,
                                      tuple(sorted(source.evidence_ids)), source.importance,
                                      source.confidence, geometry), (source.region_id,)))
        return sorted(normalized, key=lambda item: (item[0].geometry["bbox"], item[0].region_id))

    def _merge(self, staged):
        groups: list[list[tuple[Region, tuple[str, ...]]]] = []
        for item in sorted(staged, key=self._item_key):
            region = item[0]
            target = None
            for index, group in enumerate(groups):
                representative = group[0][0]
                if representative.semantic_role != region.semantic_role:
                    continue
                if max(self._overlap(region.geometry["bbox"], x[0].geometry["bbox"])
                       for x in group) >= self.policy.merge_overlap_threshold:
                    target = index
                    break
            if target is None:
                groups.append([item])
            else:
                groups[target].append(item)
        return [self._merge_group(group) for group in groups]

    def _merge_group(self, group):
        ordered = sorted(group, key=self._item_key)
        regions = [x[0] for x in ordered]
        source_ids = tuple(sorted({sid for _, ids in ordered for sid in ids}))
        evidence = tuple(sorted({eid for r in regions for eid in r.evidence_ids}))
        bbox = self._union([r.geometry["bbox"] for r in regions])
        geometry = dict(regions[0].geometry)
        geometry["bbox"] = bbox
        merged = Region(regions[0].region_id, regions[0].semantic_role, evidence,
                        max(r.importance for r in regions),
                        max(r.confidence for r in regions), geometry)
        return merged, source_ids

    def _finalize(self, merged):
        ordered = sorted(merged, key=self._item_key)
        regions = []
        remap: dict[str, set[str]] = {}
        for index, (region, source_ids) in enumerate(ordered):
            rid = f"region-{index:04d}"
            regions.append(Region(rid, region.semantic_role, region.evidence_ids,
                                  region.importance, region.confidence, region.geometry))
            for source_id in source_ids:
                remap.setdefault(source_id, set()).add(rid)
        return tuple(regions), remap

    def _subjects(self, subjects: tuple[Subject, ...], remap):
        out = []
        for subject in sorted(subjects, key=lambda s: s.subject_id):
            ids = tuple(sorted({new for old in subject.region_ids for new in remap.get(old, set())}))
            if ids:
                out.append(Subject(subject.subject_id, subject.semantic_class, ids,
                                   subject.importance, subject.confidence))
        return tuple(out)

    def _relations(self, regions):
        out = []
        for i, left in enumerate(regions):
            for right in regions[i + 1:]:
                score = self._overlap(left.geometry["bbox"], right.geometry["bbox"])
                if score > 0:
                    out.append(Relation(left.region_id, right.region_id, "overlaps", score))
        return tuple(out)

    def _clip(self, box, width, height):
        if not isinstance(box, (list, tuple)) or len(box) != 4:
            raise ValueError("Region reconstruction requires geometry.bbox")
        x, y, w, h = (float(v) for v in box)
        if w < 0 or h < 0:
            raise ValueError("bbox width and height must be non-negative")
        if not self.policy.clip_to_canvas:
            return None if w == 0 or h == 0 else [x, y, w, h]
        x0, y0 = max(0.0, x), max(0.0, y)
        x1, y1 = min(float(width), x + w), min(float(height), y + h)
        return None if x1 <= x0 or y1 <= y0 else [x0, y0, x1 - x0, y1 - y0]

    @staticmethod
    def _overlap(a, b):
        ax, ay, aw, ah = a; bx, by, bw, bh = b
        ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
        iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
        inter = ix * iy
        smaller = min(max(0.0, aw * ah), max(0.0, bw * bh))
        return 0.0 if smaller == 0 else inter / smaller

    @staticmethod
    def _union(boxes):
        x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
        x1 = max(b[0] + b[2] for b in boxes); y1 = max(b[1] + b[3] for b in boxes)
        return [x0, y0, x1 - x0, y1 - y0]

    @staticmethod
    def _item_key(item):
        region = item[0]
        return (region.semantic_role, region.geometry["bbox"], region.region_id, region.evidence_ids)
