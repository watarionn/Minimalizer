from __future__ import annotations

from dataclasses import dataclass
from math import hypot, sqrt
from typing import Any, Mapping

import numpy as np


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, float(value)))


def _rounded(value: float) -> float:
    return round(float(value), 6)


SEMANTIC_ROLE_SCORES: dict[str, float] = {
    "accessory_or_held_object": 0.95,
    "face": 1.0,
    "hair": 0.95,
    "head": 0.9,
    "left_arm": 0.8,
    "lower_body": 0.75,
    "major_clothing": 0.85,
    "neck": 0.7,
    "right_arm": 0.8,
    "torso": 0.85,
}

STRUCTURAL_BODY_PARTS = frozenset(
    {
        "left_arm",
        "right_arm",
        "torso",
        "lower_body",
        "major_clothing",
        "neck",
    }
)


IDENTITY_ROLE_SCORES: dict[str, float] = {
    "accessory_or_held_object": 1.0,
    "face": 0.95,
    "hair": 0.85,
    "head": 0.75,
    "left_arm": 0.5,
    "lower_body": 0.45,
    "major_clothing": 0.7,
    "neck": 0.4,
    "right_arm": 0.5,
    "torso": 0.55,
}


@dataclass(frozen=True)
class OmissionPolicy:
    silhouette_weight: float = 0.22
    semantic_role_weight: float = 0.23
    identity_contribution_weight: float = 0.20
    visual_salience_weight: float = 0.20
    non_redundancy_weight: float = 0.15
    protect_threshold: float = 0.72
    redundancy_threshold: float = 0.70
    prune_score_ceiling: float = 0.55
    prune_max_part_ratio: float = 0.08
    structural_prune_max_part_ratio: float = 0.025
    prune_max_subject_ratio: float = 0.005
    minimum_low_dimension_count: int = 2
    low_silhouette_threshold: float = 0.12
    low_semantic_threshold: float = 0.72
    low_identity_threshold: float = 0.60
    low_salience_threshold: float = 0.18
    minimum_silhouette_retention: float = 0.98

    def __post_init__(self) -> None:
        weights = (
            self.silhouette_weight,
            self.semantic_role_weight,
            self.identity_contribution_weight,
            self.visual_salience_weight,
            self.non_redundancy_weight,
        )
        if any(weight < 0 for weight in weights) or sum(weights) <= 0:
            raise ValueError("importance weights must be non-negative with positive total")
        unit_values = (
            self.protect_threshold,
            self.redundancy_threshold,
            self.prune_score_ceiling,
            self.prune_max_part_ratio,
            self.structural_prune_max_part_ratio,
            self.prune_max_subject_ratio,
            self.low_silhouette_threshold,
            self.low_semantic_threshold,
            self.low_identity_threshold,
            self.low_salience_threshold,
            self.minimum_silhouette_retention,
        )
        if any(not 0.0 <= value <= 1.0 for value in unit_values):
            raise ValueError("Phase 8 thresholds and ratios must be within [0, 1]")
        if self.minimum_low_dimension_count < 2:
            raise ValueError("pruning requires at least two low-dimension grounds")

    def to_dict(self) -> dict[str, Any]:
        return {
            "weights": {
                "identity_contribution": self.identity_contribution_weight,
                "non_redundancy": self.non_redundancy_weight,
                "part_role": self.semantic_role_weight,
                "silhouette_contribution": self.silhouette_weight,
                "visual_salience": self.visual_salience_weight,
            },
            "protect_threshold": self.protect_threshold,
            "prune_requirements": {
                "minimum_low_dimension_count": self.minimum_low_dimension_count,
                "prune_max_part_ratio": self.prune_max_part_ratio,
                "structural_prune_max_part_ratio": self.structural_prune_max_part_ratio,
                "structural_parts": sorted(STRUCTURAL_BODY_PARTS),
                "prune_max_subject_ratio": self.prune_max_subject_ratio,
                "prune_score_ceiling": self.prune_score_ceiling,
                "redundancy_threshold": self.redundancy_threshold,
            },
            "low_dimension_thresholds": {
                "identity_contribution": self.low_identity_threshold,
                "part_role": self.low_semantic_threshold,
                "silhouette_contribution": self.low_silhouette_threshold,
                "visual_salience": self.low_salience_threshold,
            },
            "minimum_silhouette_retention": self.minimum_silhouette_retention,
            "hard_guards": {
                "accessory_or_held_object": "protect",
                "face": "protect",
                "largest_mass_per_present_bound_part": "protect",
                "observed_outer_silhouette_contributor": "protect",
                "unbound": "protect_as_uncertainty",
            },
        }


@dataclass(frozen=True)
class MassImportanceDecision:
    mass_id: str
    semantic_part_id: str | None
    binding_status: str
    pixel_count: int
    action: str
    score: float
    silhouette_contribution: float
    part_role: float
    identity_contribution: float
    visual_salience: float
    redundancy: float
    part_area_ratio: float
    subject_area_ratio: float
    low_importance_grounds: tuple[str, ...]
    redundancy_evidence: dict[str, Any]
    omission_reason: str | None
    rationale: tuple[str, ...]
    review_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "mass_id": self.mass_id,
            "semantic_part_id": self.semantic_part_id,
            "binding_status": self.binding_status,
            "pixel_count": self.pixel_count,
            "action": self.action,
            "score": _rounded(self.score),
            "score_breakdown": {
                "identity_contribution": _rounded(self.identity_contribution),
                "redundancy": _rounded(self.redundancy),
                "part_role": _rounded(self.part_role),
                "silhouette_contribution": _rounded(
                    self.silhouette_contribution
                ),
                "visual_salience": _rounded(self.visual_salience),
            },
            "relative_area": {
                "within_part": _rounded(self.part_area_ratio),
                "within_subject": _rounded(self.subject_area_ratio),
            },
            "low_importance_grounds": list(self.low_importance_grounds),
            "redundancy_evidence": self.redundancy_evidence,
            "omission_reason": self.omission_reason,
            "rationale": list(self.rationale),
            "review_status": self.review_status,
        }


@dataclass(frozen=True)
class ImportanceOmissionResult:
    width: int
    height: int
    decisions: tuple[MassImportanceDecision, ...]
    validation: dict[str, Any]
    policy: OmissionPolicy
    mass_labels: np.ndarray
    mean_rgb_by_mass: tuple[tuple[float, float, float], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "coordinate_space": {
                "pixel_width": self.width,
                "pixel_height": self.height,
                "normalized_origin": "top-left",
                "normalized_range": [0.0, 1.0],
            },
            "importance_policy": self.policy.to_dict(),
            "action_semantics": {
                "protect": "must survive downstream omission",
                "keep": "retained by the current policy",
                "prune": "omission candidate with explicit redundancy evidence",
            },
            "decisions": [decision.to_dict() for decision in self.decisions],
            "validation": self.validation,
        }


def _decode_runs(
    runs: Any,
    *,
    width: int,
    height: int,
) -> np.ndarray:
    mask = np.zeros((height, width), dtype=bool)
    if not isinstance(runs, list):
        raise ValueError("Phase 7 mass pixel_runs must be a list")
    for raw in runs:
        if not isinstance(raw, (list, tuple)) or len(raw) != 3:
            raise ValueError("Phase 7 mass pixel_runs must contain [y, x0, x1]")
        y, x0, x1 = (int(raw[0]), int(raw[1]), int(raw[2]))
        if not (0 <= y < height and 0 <= x0 < x1 <= width):
            raise ValueError("Phase 7 mass pixel run is outside the canvas")
        if np.any(mask[y, x0:x1]):
            raise ValueError("Phase 7 mass pixel_runs overlap")
        mask[y, x0:x1] = True
    return mask


def _subject_boundary(subject: np.ndarray) -> np.ndarray:
    padded = np.pad(subject, 1, mode="constant", constant_values=False)
    interior = (
        padded[1:-1, 1:-1]
        & padded[:-2, 1:-1]
        & padded[2:, 1:-1]
        & padded[1:-1, :-2]
        & padded[1:-1, 2:]
    )
    return subject & ~interior


def _role_score(table: Mapping[str, float], part_id: str | None) -> float:
    if part_id is None:
        return 0.5
    return _clamp(table.get(part_id, 0.5))


def _colour_similarity(left: np.ndarray, right: np.ndarray) -> float:
    distance = float(np.linalg.norm(left.astype(np.float64) - right.astype(np.float64)))
    return _clamp(1.0 - distance / sqrt(3.0 * 255.0 * 255.0))


def evaluate_importance_omission(
    phase7_payload: Mapping[str, Any],
    mass_labels: np.ndarray,
    silhouette: np.ndarray,
    *,
    policy: OmissionPolicy | None = None,
) -> ImportanceOmissionResult:
    policy = policy or OmissionPolicy()
    coordinate = phase7_payload.get("coordinate_space")
    if not isinstance(coordinate, Mapping):
        raise ValueError("Phase 8 requires Phase 7 coordinate_space")
    width = int(coordinate.get("pixel_width", 0))
    height = int(coordinate.get("pixel_height", 0))
    if width <= 0 or height <= 0:
        raise ValueError("Phase 7 coordinate space must be positive")

    raw_labels = np.asarray(mass_labels)
    if raw_labels.shape != (height, width):
        raise ValueError("Phase 7 mass labels do not match coordinate space")
    labels = raw_labels.astype(np.int64, copy=True)
    labels[labels == 65535] = -1

    observed_silhouette = np.asarray(silhouette) > 0
    if observed_silhouette.shape != (height, width):
        raise ValueError("Phase 7 silhouette does not match coordinate space")
    if not np.array_equal(observed_silhouette, labels >= 0):
        raise ValueError("Phase 7 silhouette and mass labels disagree")

    raw_masses = phase7_payload.get("masses")
    if not isinstance(raw_masses, list) or not raw_masses:
        raise ValueError("Phase 8 requires non-empty Phase 7 masses")
    if np.any(labels >= len(raw_masses)):
        raise ValueError("Phase 7 labels reference a missing mass")

    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(raw_masses):
        if not isinstance(raw, Mapping):
            raise ValueError("Phase 7 mass records must be objects")
        mass_id = str(raw.get("mass_id", ""))
        if not mass_id or mass_id in seen_ids:
            raise ValueError("Phase 7 mass_id must be present and unique")
        seen_ids.add(mass_id)
        status = str(raw.get("binding_status", ""))
        part_id = raw.get("semantic_part_id")
        if status == "bound" and not isinstance(part_id, str):
            raise ValueError("bound Phase 7 mass requires semantic_part_id")
        if status == "unbound" and part_id is not None:
            raise ValueError("unbound Phase 7 mass must not claim semantic_part_id")
        if status not in {"bound", "unbound"}:
            raise ValueError("unsupported Phase 7 binding_status")

        mask = labels == index
        pixel_count = int(np.count_nonzero(mask))
        if pixel_count <= 0 or pixel_count != int(raw.get("pixel_count", -1)):
            raise ValueError(f"Phase 7 pixel_count mismatch for {mass_id}")
        decoded = _decode_runs(
            raw.get("pixel_runs"),
            width=width,
            height=height,
        )
        if not np.array_equal(decoded, mask):
            raise ValueError(f"Phase 7 labels and pixel_runs disagree for {mass_id}")
        mean_rgb_raw = raw.get("mean_rgb")
        if not isinstance(mean_rgb_raw, list) or len(mean_rgb_raw) != 3:
            raise ValueError(f"Phase 7 mean_rgb is invalid for {mass_id}")
        mean_rgb = np.asarray(mean_rgb_raw, dtype=np.float64)
        if not np.all(np.isfinite(mean_rgb)) or np.any(mean_rgb < 0) or np.any(mean_rgb > 255):
            raise ValueError(f"Phase 7 mean_rgb is outside RGB range for {mass_id}")
        ys, xs = np.where(mask)
        records.append(
            {
                "mass_id": mass_id,
                "binding_status": status,
                "semantic_part_id": part_id,
                "pixel_count": pixel_count,
                "mask": mask,
                "centroid": (float(xs.mean()), float(ys.mean())),
                "mean_rgb": mean_rgb,
            }
        )

    subject_pixel_count = int(np.count_nonzero(observed_silhouette))
    declared_subject_pixels = int(
        phase7_payload.get("validation", {}).get(
            "subject_pixel_count",
            subject_pixel_count,
        )
    )
    if subject_pixel_count != declared_subject_pixels:
        raise ValueError("Phase 7 declared subject pixel count disagrees with silhouette")

    boundary = _subject_boundary(observed_silhouette)
    boundary_pixel_count = int(np.count_nonzero(boundary))
    canvas_diagonal = hypot(width, height)

    by_part: dict[str, list[int]] = {}
    for index, record in enumerate(records):
        if record["binding_status"] == "bound":
            by_part.setdefault(str(record["semantic_part_id"]), []).append(index)

    largest_by_part: dict[str, int] = {}
    for part_id, indices in sorted(by_part.items()):
        largest_by_part[part_id] = sorted(
            indices,
            key=lambda idx: (-records[idx]["pixel_count"], records[idx]["mass_id"]),
        )[0]

    decisions: list[MassImportanceDecision] = []
    weights = (
        policy.silhouette_weight,
        policy.semantic_role_weight,
        policy.identity_contribution_weight,
        policy.visual_salience_weight,
        policy.non_redundancy_weight,
    )
    total_weight = sum(weights)

    for index, record in enumerate(records):
        mass_id = str(record["mass_id"])
        part_id = record["semantic_part_id"]
        pixel_count = int(record["pixel_count"])
        mask = record["mask"]
        boundary_share = (
            float(np.count_nonzero(mask & boundary)) / boundary_pixel_count
            if boundary_pixel_count
            else 0.0
        )
        silhouette_score = _clamp(2.0 * sqrt(boundary_share))
        semantic_score = _role_score(SEMANTIC_ROLE_SCORES, part_id)
        identity_score = _role_score(IDENTITY_ROLE_SCORES, part_id)
        subject_area_ratio = pixel_count / float(subject_pixel_count)

        if part_id is None:
            part_indices = [index]
            part_max_pixels = pixel_count
        else:
            part_indices = by_part[str(part_id)]
            part_max_pixels = int(
                records[largest_by_part[str(part_id)]]["pixel_count"]
            )
        part_area_ratio = pixel_count / float(part_max_pixels)

        area_salience = _clamp(3.0 * sqrt(subject_area_ratio))
        larger_same_part = [
            candidate
            for candidate in part_indices
            if candidate != index
            and records[candidate]["pixel_count"] >= pixel_count
        ]
        comparisons: list[tuple[float, float, int]] = []
        for candidate in larger_same_part:
            other = records[candidate]
            colour = _colour_similarity(record["mean_rgb"], other["mean_rgb"])
            cx, cy = record["centroid"]
            ox, oy = other["centroid"]
            distance_ratio = hypot(cx - ox, cy - oy) / canvas_diagonal
            proximity = _clamp(1.0 - distance_ratio / 0.35)
            comparisons.append((colour, proximity, candidate))
        if comparisons:
            best_colour, best_proximity, comparison_index = max(
                comparisons,
                key=lambda item: (
                    item[0] * (0.65 + 0.35 * item[1]),
                    -item[2],
                ),
            )
            best_similarity = best_colour * (0.65 + 0.35 * best_proximity)
            strongest_contrast = max(
                1.0 - colour for colour, _, _ in comparisons
            )
            redundancy = _clamp((1.0 - part_area_ratio) * best_similarity)
        else:
            best_colour = 0.0
            best_proximity = 0.0
            comparison_index = None
            strongest_contrast = 0.0
            redundancy = 0.0
        visual_salience = _clamp(0.8 * area_salience + 0.2 * strongest_contrast)

        dimension_values = (
            silhouette_score,
            semantic_score,
            identity_score,
            visual_salience,
            1.0 - redundancy,
        )
        score = sum(value * weight for value, weight in zip(dimension_values, weights)) / total_weight

        low_grounds: list[str] = []
        if silhouette_score <= policy.low_silhouette_threshold:
            low_grounds.append("low-silhouette-contribution")
        if semantic_score <= policy.low_semantic_threshold:
            low_grounds.append("low-part-role")
        if identity_score <= policy.low_identity_threshold:
            low_grounds.append("low-identity-contribution")
        if visual_salience <= policy.low_salience_threshold:
            low_grounds.append("low-visual-salience")

        rationale: list[str] = []
        omission_reason: str | None = None
        review_status = "resolved"
        if record["binding_status"] == "unbound":
            action = "protect"
            rationale.append("unbound-uncertainty-preserved")
            review_status = "deferred-unbound"
        elif part_id in {"accessory_or_held_object", "face"}:
            action = "protect"
            rationale.append(f"identity-role-protected:{part_id}")
        elif np.any(mask & boundary):
            action = "protect"
            rationale.append("observed-outer-silhouette-contributor")
        elif largest_by_part.get(str(part_id)) == index:
            action = "protect"
            rationale.append(f"largest-mass-for-present-part:{part_id}")
        else:
            prune_part_ratio_limit = (
                policy.structural_prune_max_part_ratio
                if part_id in STRUCTURAL_BODY_PARTS
                else policy.prune_max_part_ratio
            )
            prune_supported = (
                redundancy >= policy.redundancy_threshold
                and score <= policy.prune_score_ceiling
                and part_area_ratio <= prune_part_ratio_limit
                and subject_area_ratio <= policy.prune_max_subject_ratio
                and len(low_grounds) >= policy.minimum_low_dimension_count
            )
            if prune_supported:
                action = "prune"
                omission_reason = "redundant-low-contribution-same-part-fragment"
                rationale.extend(("same-part-redundancy-supported", *low_grounds))
            elif score >= policy.protect_threshold:
                action = "protect"
                rationale.append("importance-score-at-or-above-protect-threshold")
            else:
                action = "keep"
                rationale.append("insufficient-multi-ground-prune-evidence")

        redundancy_established = bool(
            comparison_index is not None
            and redundancy >= policy.redundancy_threshold
        )
        redundancy_evidence = {
            "established": redundancy_established,
            "reference_mass_id": (
                str(records[comparison_index]["mass_id"])
                if comparison_index is not None
                else None
            ),
            "same_semantic_part": bool(comparison_index is not None),
            "reference_is_not_smaller": bool(comparison_index is not None),
            "color_similarity": _rounded(best_colour),
            "spatial_proximity": _rounded(best_proximity),
            "candidate_to_largest_part_area_ratio": _rounded(part_area_ratio),
            "prune_part_ratio_limit": _rounded(
                policy.structural_prune_max_part_ratio
                if part_id in STRUCTURAL_BODY_PARTS
                else policy.prune_max_part_ratio
            ),
        }

        decisions.append(
            MassImportanceDecision(
                mass_id=mass_id,
                semantic_part_id=part_id if isinstance(part_id, str) else None,
                binding_status=str(record["binding_status"]),
                pixel_count=pixel_count,
                action=action,
                score=_rounded(score),
                silhouette_contribution=_rounded(silhouette_score),
                part_role=_rounded(semantic_score),
                identity_contribution=_rounded(identity_score),
                visual_salience=_rounded(visual_salience),
                redundancy=_rounded(redundancy),
                part_area_ratio=_rounded(part_area_ratio),
                subject_area_ratio=_rounded(subject_area_ratio),
                low_importance_grounds=tuple(low_grounds),
                redundancy_evidence=redundancy_evidence,
                omission_reason=omission_reason,
                rationale=tuple(rationale),
                review_status=review_status,
            )
        )

    pruned_indices = {
        index
        for index, decision in enumerate(decisions)
        if decision.action == "prune"
    }
    retained_mask = observed_silhouette.copy()
    for index in pruned_indices:
        retained_mask[labels == index] = False
    retained_boundary_pixels = int(np.count_nonzero(boundary & retained_mask))
    silhouette_retention = (
        retained_boundary_pixels / float(boundary_pixel_count)
        if boundary_pixel_count
        else 1.0
    )

    action_counts = {
        name: sum(decision.action == name for decision in decisions)
        for name in ("keep", "protect", "prune")
    }
    action_pixels = {
        name: sum(
            decision.pixel_count
            for decision in decisions
            if decision.action == name
        )
        for name in ("keep", "protect", "prune")
    }
    largest_violations = [
        records[index]["mass_id"]
        for index in largest_by_part.values()
        if decisions[index].action != "protect"
    ]
    identity_pruned = [
        decision.mass_id
        for decision in decisions
        if decision.semantic_part_id in {"accessory_or_held_object", "face"}
        and decision.action == "prune"
    ]
    unbound_pruned = [
        decision.mass_id
        for decision in decisions
        if decision.binding_status == "unbound"
        and decision.action == "prune"
    ]
    protected_part_presence = {
        part_id: sum(
            decision.semantic_part_id == part_id
            and decision.action != "prune"
            for decision in decisions
        )
        for part_id in ("face", "hair", "torso")
        if part_id in by_part
    }
    removed_parts = sorted(
        part_id for part_id, count in protected_part_presence.items() if count == 0
    )
    invalid_prune_evidence = [
        decision.mass_id
        for decision in decisions
        if decision.action == "prune"
        and (
            decision.redundancy < policy.redundancy_threshold
            or not decision.redundancy_evidence["established"]
            or len(decision.low_importance_grounds)
            < policy.minimum_low_dimension_count
        )
    ]
    passed = (
        not largest_violations
        and not identity_pruned
        and not unbound_pruned
        and not removed_parts
        and not invalid_prune_evidence
        and silhouette_retention >= policy.minimum_silhouette_retention
    )
    validation = {
        "mass_count": len(decisions),
        "action_counts": action_counts,
        "action_pixel_counts": action_pixels,
        "prune_pixel_ratio": _rounded(
            action_pixels["prune"] / float(subject_pixel_count)
        ),
        "subject_pixel_count": subject_pixel_count,
        "subject_boundary_pixel_count": boundary_pixel_count,
        "retained_subject_boundary_pixel_count": retained_boundary_pixels,
        "silhouette_retention_ratio": _rounded(silhouette_retention),
        "minimum_silhouette_retention": policy.minimum_silhouette_retention,
        "present_bound_parts": sorted(by_part),
        "largest_part_mass_protection_violations": largest_violations,
        "identity_protection_violations": identity_pruned,
        "unbound_protection_violations": unbound_pruned,
        "removed_major_parts": removed_parts,
        "invalid_prune_evidence": invalid_prune_evidence,
        "observed_only": True,
        "pass": passed,
    }
    return ImportanceOmissionResult(
        width=width,
        height=height,
        decisions=tuple(decisions),
        validation=validation,
        policy=policy,
        mass_labels=labels.astype(np.int32),
        mean_rgb_by_mass=tuple(
            tuple(float(value) for value in record["mean_rgb"])
            for record in records
        ),
    )
