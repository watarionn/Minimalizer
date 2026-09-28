from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np


def _rounded(value: float) -> float:
    return round(float(value), 6)


@dataclass(frozen=True)
class MajorMassPolicy:
    minimum_shared_boundary_pixels: int = 1
    merge_unbound_regions: bool = False
    allow_cross_part_merge: bool = False

    def __post_init__(self) -> None:
        if self.minimum_shared_boundary_pixels < 1:
            raise ValueError("minimum_shared_boundary_pixels must be at least 1")
        if self.merge_unbound_regions:
            raise ValueError("Phase 7 v1 forbids merging unbound regions")
        if self.allow_cross_part_merge:
            raise ValueError(
                "Phase 7 v1 forbids cross-part merge; explicit relation-aware "
                "cross-part merging is not implemented"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "minimum_shared_boundary_pixels": self.minimum_shared_boundary_pixels,
            "merge_unbound_regions": self.merge_unbound_regions,
            "allow_cross_part_merge": self.allow_cross_part_merge,
        }


@dataclass(frozen=True)
class SemanticMass:
    mass_id: str
    semantic_part_id: str | None
    binding_status: str
    region_ids: tuple[str, ...]
    pixel_count: int
    bbox_xywh: tuple[int, int, int, int]
    centroid_xy: tuple[float, float]
    mean_rgb: tuple[float, float, float]
    pixel_runs: tuple[tuple[int, int, int], ...]
    evidence_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mass_id": self.mass_id,
            "semantic_part_id": self.semantic_part_id,
            "binding_status": self.binding_status,
            "region_ids": list(self.region_ids),
            "pixel_count": self.pixel_count,
            "bbox_xywh": list(self.bbox_xywh),
            "centroid_xy": [_rounded(v) for v in self.centroid_xy],
            "mean_rgb": [_rounded(v) for v in self.mean_rgb],
            "pixel_runs": [list(run) for run in self.pixel_runs],
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class MajorMassResult:
    width: int
    height: int
    masses: tuple[SemanticMass, ...]
    validation: dict[str, Any]
    policy: MajorMassPolicy
    mass_labels: np.ndarray

    def to_dict(self) -> dict[str, Any]:
        hierarchy: dict[str, list[str]] = {}
        for mass in self.masses:
            parent = (
                f"part:{mass.semantic_part_id}"
                if mass.semantic_part_id is not None
                else "unbound"
            )
            hierarchy.setdefault(parent, []).append(mass.mass_id)
        return {
            "schema_version": "1.0",
            "coordinate_space": {
                "pixel_width": self.width,
                "pixel_height": self.height,
                "normalized_origin": "top-left",
                "normalized_range": [0.0, 1.0],
            },
            "mass_policy": self.policy.to_dict(),
            "hierarchy": {
                key: sorted(values)
                for key, values in sorted(hierarchy.items())
            },
            "masses": [mass.to_dict() for mass in self.masses],
            "validation": self.validation,
        }


class _DisjointSet:
    def __init__(self, values: tuple[str, ...]) -> None:
        self.parent = {value: value for value in values}

    def find(self, value: str) -> str:
        parent = self.parent[value]
        while parent != self.parent[parent]:
            parent = self.parent[parent]
        while value != parent:
            next_value = self.parent[value]
            self.parent[value] = parent
            value = next_value
        return parent

    def union(self, left: str, right: str) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        first, second = sorted((left_root, right_root))
        self.parent[second] = first


def _decode_runs(
    runs: Any,
    *,
    width: int,
    height: int,
) -> np.ndarray:
    mask = np.zeros((height, width), dtype=bool)
    for raw in runs:
        if not isinstance(raw, (list, tuple)) or len(raw) != 3:
            raise ValueError("pixel_runs must contain [y, x0, x1] triplets")
        y, x0, x1 = (int(raw[0]), int(raw[1]), int(raw[2]))
        if not (0 <= y < height and 0 <= x0 < x1 <= width):
            raise ValueError("pixel run is outside the declared canvas")
        if np.any(mask[y, x0:x1]):
            raise ValueError("pixel_runs overlap within one region")
        mask[y, x0:x1] = True
    return mask


def _encode_runs(mask: np.ndarray) -> tuple[tuple[int, int, int], ...]:
    runs: list[tuple[int, int, int]] = []
    for y in np.flatnonzero(np.any(mask, axis=1)):
        xs = np.flatnonzero(mask[y])
        if xs.size == 0:
            continue
        start = previous = int(xs[0])
        for raw_x in xs[1:]:
            x = int(raw_x)
            if x != previous + 1:
                runs.append((int(y), start, previous + 1))
                start = x
            previous = x
        runs.append((int(y), start, previous + 1))
    return tuple(runs)


def _region_index(
    payload: Mapping[str, Any],
) -> tuple[int, int, dict[str, dict[str, Any]]]:
    coordinate = payload.get("coordinate_space")
    if not isinstance(coordinate, Mapping):
        raise ValueError("Phase 7 requires Phase 6 coordinate_space")
    width = int(coordinate.get("pixel_width", 0))
    height = int(coordinate.get("pixel_height", 0))
    if width <= 0 or height <= 0:
        raise ValueError("Phase 6 coordinate space must be positive")

    regions = payload.get("regions")
    if not isinstance(regions, list) or not regions:
        raise ValueError("Phase 7 requires non-empty Phase 6 regions")
    by_id: dict[str, dict[str, Any]] = {}
    for raw in regions:
        if not isinstance(raw, dict):
            raise ValueError("Phase 6 region records must be objects")
        region_id = str(raw.get("region_id", ""))
        if not region_id:
            raise ValueError("Phase 6 region_id is required")
        if region_id in by_id:
            raise ValueError(f"duplicate Phase 6 region_id: {region_id}")
        status = str(raw.get("binding_status", ""))
        part_id = raw.get("semantic_part_id")
        if status == "bound" and not isinstance(part_id, str):
            raise ValueError("bound Phase 6 region requires semantic_part_id")
        if status == "unbound" and part_id is not None:
            raise ValueError("unbound Phase 6 region must not claim semantic_part_id")
        if status not in {"bound", "unbound"}:
            raise ValueError(f"unsupported Phase 6 binding_status: {status}")
        by_id[region_id] = raw
    return width, height, by_id


def _validate_adjacency(
    regions: Mapping[str, Mapping[str, Any]],
) -> None:
    for region_id, record in sorted(regions.items()):
        seen: set[str] = set()
        for adjacent in record.get("adjacent_regions", ()):
            adjacent_id = str(adjacent.get("region_id", ""))
            if not adjacent_id or adjacent_id == region_id:
                raise ValueError("Phase 6 adjacency must reference another region")
            if adjacent_id in seen:
                raise ValueError(
                    f"duplicate Phase 6 adjacency: {region_id} -> {adjacent_id}"
                )
            seen.add(adjacent_id)
            if adjacent_id not in regions:
                raise ValueError(
                    f"Phase 6 adjacency references missing region {adjacent_id}"
                )
            boundary = int(adjacent.get("shared_boundary_pixels", 0))
            if boundary < 0:
                raise ValueError("shared boundary pixels must be non-negative")
            reciprocal = [
                item
                for item in regions[adjacent_id].get("adjacent_regions", ())
                if str(item.get("region_id", "")) == region_id
            ]
            if len(reciprocal) != 1:
                raise ValueError(
                    f"Phase 6 adjacency is not reciprocal: {region_id} <-> {adjacent_id}"
                )
            if int(reciprocal[0].get("shared_boundary_pixels", -1)) != boundary:
                raise ValueError(
                    f"Phase 6 adjacency boundary mismatch: {region_id} <-> {adjacent_id}"
                )


def reconstruct_major_masses(
    source_rgb: np.ndarray,
    phase6_payload: Mapping[str, Any],
    *,
    policy: MajorMassPolicy | None = None,
) -> MajorMassResult:
    policy = policy or MajorMassPolicy()
    image = np.asarray(source_rgb, dtype=np.uint8)
    if image.ndim != 3 or image.shape[2] < 3:
        raise ValueError("Phase 7 requires an RGB source image")
    image = image[..., :3]
    width, height, regions = _region_index(phase6_payload)
    _validate_adjacency(regions)
    if image.shape[:2] != (height, width):
        raise ValueError("source dimensions must match Phase 6 coordinate space")

    region_masks: dict[str, np.ndarray] = {}
    occupied = np.zeros((height, width), dtype=bool)
    for region_id, record in sorted(regions.items()):
        mask = _decode_runs(
            record.get("pixel_runs", ()),
            width=width,
            height=height,
        )
        pixel_count = int(np.count_nonzero(mask))
        if pixel_count != int(record.get("pixel_count", -1)):
            raise ValueError(
                f"Phase 6 pixel_count mismatch for {region_id}"
            )
        if np.any(occupied & mask):
            raise ValueError("Phase 6 region pixel ownership overlaps")
        occupied |= mask
        region_masks[region_id] = mask

    declared_subject_pixels = int(
        phase6_payload.get("validation", {}).get(
            "subject_pixel_count",
            int(np.count_nonzero(occupied)),
        )
    )
    if int(np.count_nonzero(occupied)) != declared_subject_pixels:
        raise ValueError(
            "Phase 6 subject pixel count does not match decoded regions"
        )

    region_ids = tuple(sorted(regions))
    dsu = _DisjointSet(region_ids)
    for region_id in region_ids:
        record = regions[region_id]
        if record["binding_status"] != "bound":
            continue
        part_id = str(record["semantic_part_id"])
        for adjacent in record.get("adjacent_regions", ()):
            adjacent_id = str(adjacent.get("region_id", ""))
            if adjacent_id not in regions:
                raise ValueError(
                    f"Phase 6 adjacency references missing region {adjacent_id}"
                )
            boundary = int(adjacent.get("shared_boundary_pixels", 0))
            if boundary < 0:
                raise ValueError("shared boundary pixels must be non-negative")
            neighbor = regions[adjacent_id]
            reciprocal = [
                item
                for item in neighbor.get("adjacent_regions", ())
                if str(item.get("region_id", "")) == region_id
            ]
            if len(reciprocal) != 1:
                raise ValueError(
                    f"Phase 6 adjacency is not reciprocal: {region_id} <-> {adjacent_id}"
                )
            if int(reciprocal[0].get("shared_boundary_pixels", -1)) != boundary:
                raise ValueError(
                    f"Phase 6 adjacency boundary mismatch: {region_id} <-> {adjacent_id}"
                )
            if boundary < policy.minimum_shared_boundary_pixels:
                continue
            if neighbor["binding_status"] != "bound":
                continue
            if neighbor.get("semantic_part_id") != part_id:
                continue
            dsu.union(region_id, adjacent_id)

    groups: dict[str, list[str]] = {}
    for region_id in region_ids:
        record = regions[region_id]
        if record["binding_status"] == "unbound" and not policy.merge_unbound_regions:
            root = f"unbound:{region_id}"
        else:
            root = dsu.find(region_id)
        groups.setdefault(root, []).append(region_id)

    ordered_groups = sorted(
        (
            tuple(sorted(values))
            for values in groups.values()
        ),
        key=lambda values: values[0],
    )

    mass_labels = np.full((height, width), -1, dtype=np.int32)
    masses: list[SemanticMass] = []
    seen_regions: set[str] = set()
    for mass_index, member_ids in enumerate(ordered_groups):
        member_records = [regions[region_id] for region_id in member_ids]
        statuses = {str(record["binding_status"]) for record in member_records}
        parts = {record.get("semantic_part_id") for record in member_records}
        if len(statuses) != 1:
            raise ValueError("major mass cannot mix bound and unbound regions")
        status = next(iter(statuses))
        if status == "bound" and len(parts) != 1:
            raise ValueError("major mass cannot cross semantic part boundaries")
        if status == "unbound" and parts != {None}:
            raise ValueError("unbound major mass cannot claim a semantic part")

        mask = np.logical_or.reduce(
            [region_masks[region_id] for region_id in member_ids]
        )
        if np.any(mass_labels[mask] >= 0):
            raise ValueError("major masses overlap")
        mass_labels[mask] = mass_index

        ys, xs = np.where(mask)
        pixel_count = int(xs.size)
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        pixels = image[mask].astype(np.float64)
        mean_rgb = tuple(float(value) for value in pixels.mean(axis=0))
        mass_id = f"mass-{mass_index:04d}"
        semantic_part_id = (
            str(next(iter(parts))) if status == "bound" else None
        )
        masses.append(
            SemanticMass(
                mass_id=mass_id,
                semantic_part_id=semantic_part_id,
                binding_status=status,
                region_ids=member_ids,
                pixel_count=pixel_count,
                bbox_xywh=(x0, y0, x1 - x0, y1 - y0),
                centroid_xy=(float(xs.mean()), float(ys.mean())),
                mean_rgb=mean_rgb,
                pixel_runs=_encode_runs(mask),
                evidence_refs=tuple(
                    [
                        "phase06:06_region_bindings.json",
                        "phase06:06_region_labels.png",
                        *(
                            f"phase06:{region_id}"
                            for region_id in member_ids
                        ),
                    ]
                ),
            )
        )
        seen_regions.update(member_ids)

    if seen_regions != set(region_ids):
        raise ValueError("Phase 7 did not account for every Phase 6 region")
    if np.any(mass_labels[occupied] < 0):
        raise ValueError("Phase 7 lost Phase 6 subject pixels")
    if np.any(mass_labels[~occupied] >= 0):
        raise ValueError("Phase 7 claimed pixels outside Phase 6 subject")

    bound_regions = [
        region
        for region in regions.values()
        if region["binding_status"] == "bound"
    ]
    bound_masses = [
        mass for mass in masses if mass.binding_status == "bound"
    ]
    unbound_regions = [
        region
        for region in regions.values()
        if region["binding_status"] == "unbound"
    ]
    unbound_masses = [
        mass for mass in masses if mass.binding_status == "unbound"
    ]
    part_mass_counts: dict[str, int] = {}
    for mass in bound_masses:
        part_mass_counts[mass.semantic_part_id or ""] = (
            part_mass_counts.get(mass.semantic_part_id or "", 0) + 1
        )

    mixed_semantic_mass_count = 0
    for mass in bound_masses:
        region_parts = {
            regions[region_id].get("semantic_part_id")
            for region_id in mass.region_ids
        }
        if len(region_parts) != 1:
            mixed_semantic_mass_count += 1

    validation = {
        "source_region_count": len(regions),
        "mass_count": len(masses),
        "bound_region_count": len(bound_regions),
        "bound_mass_count": len(bound_masses),
        "unbound_region_count": len(unbound_regions),
        "unbound_mass_count": len(unbound_masses),
        "region_to_mass_reduction_ratio": _rounded(
            1.0 - len(masses) / float(len(regions))
        ),
        "subject_pixel_count": declared_subject_pixels,
        "mass_pixel_count": sum(mass.pixel_count for mass in masses),
        "subject_pixel_coverage": _rounded(
            sum(mass.pixel_count for mass in masses)
            / float(declared_subject_pixels)
        ),
        "mixed_semantic_mass_count": mixed_semantic_mass_count,
        "cross_part_merge_count": mixed_semantic_mass_count,
        "unbound_absorbed_into_bound_count": 0,
        "part_mass_counts": {
            key: part_mass_counts[key]
            for key in sorted(part_mass_counts)
        },
        "pass": (
            sum(mass.pixel_count for mass in masses)
            == declared_subject_pixels
            and mixed_semantic_mass_count == 0
            and len(bound_masses) <= len(bound_regions)
            and len(unbound_masses) == len(unbound_regions)
        ),
    }
    return MajorMassResult(
        width=width,
        height=height,
        masses=tuple(masses),
        validation=validation,
        policy=policy,
        mass_labels=mass_labels,
    )
